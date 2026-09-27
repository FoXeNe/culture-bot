from maxapi import Bot, F, Router
from maxapi.types import MessageCallback
from maxapi.types.attachments.attachment import Attachment, OtherAttachmentPayload
from maxapi.enums.attachment import AttachmentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    after_rating_keyboard,
    challenge_detail_keyboard,
    challenge_keyboard,
    menu_keyboard,
    no_more_events_keyboard,
    post_event_keyboard,
    post_event_miss_keyboard,
    rating_keyboard,
    reminder_keyboard,
    reminder_miss_keyboard,
)
from models.models import Event
from services.db_queries import (
    accept_challenge,
    confirm_visit,
    create_challenge,
    get_challenge_for_user,
    get_event_by_challenge_id,
    get_stats_by_challenge,
    get_week_event_ids,
    miss_visit,
    save_rating,
    skip_challenge,
)

router = Router()

# хелперы карточки

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

def _price_str(event: Event) -> str | None:
    price = None
    if event.price_from is not None:
        price = "бесплатно" if event.price_from == 0 else f"от {event.price_from} ₽"
    if event.is_pushkin_card:
        price = f"{price} · 🎫 пушкинская карта" if price else "🎫 пушкинская карта"
    return price

def _card_text(event: Event) -> str:
    dt = event.event_date
    date_str = f"{dt.day} {MONTHS[dt.month - 1]}, {dt.strftime('%H:%M')}"
    location = ", ".join(p for p in [date_str, event.venue] if p)
    parts = [event.title, "", location]
    price = _price_str(event)
    if price:
        parts.append(price)
    return "\n".join(parts)

def _detail_text(event: Event) -> str:
    dt = event.event_date
    date_str = f"{dt.day} {MONTHS[dt.month - 1]}, {dt.strftime('%H:%M')}"
    location = ", ".join(p for p in [date_str, event.venue] if p)
    parts = [event.title, "", location]
    price = _price_str(event)
    if price:
        parts.append(price)
    if event.about:
        parts.extend(["", event.about])
    if event.ticket_url:
        parts.extend(["", f"купить билет: {event.ticket_url}"])
    return "\n".join(parts)

def _reminder_text(event: Event) -> str:
    dt = event.event_date
    date_str = f"{dt.day} {MONTHS[dt.month - 1]}, {dt.strftime('%H:%M')}"
    parts = [
        "напоминаю! завтра у тебя мероприятие:",
        "",
        event.title,
        event.venue or "",
        date_str,
        "",
        "не забудь проверить билет и заранее спланировать маршрут. приятного отдыха!",
    ]
    return "\n".join(p for p in parts if p is not None)

def _card_attachments(event: Event, challenge_id: int, prev_id: int | None = None) -> list:
    attachments = []
    if event.image_url:
        attachments.append(
            Attachment(
                type=AttachmentType.IMAGE,
                payload=OtherAttachmentPayload(url=event.image_url),
            )
        )
    attachments.append(challenge_keyboard(challenge_id, prev_id))
    return attachments

async def send_challenge_card(bot: Bot, user_id: int, event: Event, challenge_id: int) -> None:
    await bot.send_message(
        user_id=user_id,
        text=_card_text(event),
        attachments=_card_attachments(event, challenge_id),
    )

async def _show_visited_prompt(event: MessageCallback, session: AsyncSession, challenge_id: int) -> None:
    stats = await get_stats_by_challenge(session, challenge_id)
    streak = stats["current_streak"]
    level = stats["level"]
    remaining = (level + 1) * 5 - stats["total_confirmed"]
    text = (
        f"отлично. тогда засчитываю посещение.\n"
        f"🔥 твой стрик: {streak}\n"
        f"осталось ещё {remaining} посещений до нового уровня.\n"
        "\n"
        "как оценишь мероприятие?"
    )
    await event.answer(new_text=text, attachments=[rating_keyboard(challenge_id)])

# колбэки

@router.message_callback(F.callback.payload.startswith("accept_"))
async def cb_accept_challenge(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("accept_"))
    await accept_challenge(session, challenge_id)
    await event.answer(new_text="отлично, напомню за день до события! 🎉")

@router.message_callback(F.callback.payload.startswith("skip_"))
async def cb_skip_challenge(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("skip_"))
    user_id = event.from_user.user_id
    await skip_challenge(session, challenge_id)

    exclude_ids = await get_week_event_ids(session, user_id)
    new_event = await get_challenge_for_user(session, user_id, exclude_ids=exclude_ids)

    if new_event is None:
        await event.answer(
            new_text="на этой неделе событий по твоим категориям больше нет",
            attachments=[no_more_events_keyboard(challenge_id)],
        )
        return

    new_challenge = await create_challenge(session, user_id, new_event.id)
    await event.answer(
        new_text=_card_text(new_event),
        attachments=_card_attachments(new_event, new_challenge.id, prev_id=challenge_id),
    )

@router.message_callback(F.callback.payload.startswith("prev_"))
async def cb_prev_challenge(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("prev_"))
    ev = await get_event_by_challenge_id(session, challenge_id)
    await event.answer(
        new_text=_card_text(ev),
        attachments=_card_attachments(ev, challenge_id),
    )

@router.message_callback(F.callback.payload.startswith("detail_back_"))
async def cb_detail_back(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("detail_back_"))
    ev = await get_event_by_challenge_id(session, challenge_id)
    await event.answer(
        new_text=_card_text(ev),
        attachments=_card_attachments(ev, challenge_id),
    )

@router.message_callback(F.callback.payload.startswith("detail_"))
async def cb_detail_challenge(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("detail_"))
    ev = await get_event_by_challenge_id(session, challenge_id)
    await event.answer(
        new_text=_detail_text(ev),
        attachments=[challenge_detail_keyboard(challenge_id)],
    )

# напоминание

@router.message_callback(F.callback.payload.startswith("remind_ok_"))
async def cb_remind_ok(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text="меню", attachments=[menu_keyboard()])

@router.message_callback(F.callback.payload.startswith("remind_back_"))
async def cb_remind_back(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("remind_back_"))
    ev = await get_event_by_challenge_id(session, challenge_id)
    await event.answer(
        new_text=_reminder_text(ev),
        attachments=[reminder_keyboard(challenge_id)],
    )

@router.message_callback(F.callback.payload.startswith("remind_miss_"))
async def cb_remind_miss(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("remind_miss_"))
    await skip_challenge(session, challenge_id)
    text = (
        "хорошо, уберу мероприятие из ближайших планов.\n"
        "\n"
        "напоминаю, что если ты не посетишь ни одного мероприятия за неделю, твой стрик обнулится!\n"
        "\n"
        "хочешь посмотреть другие мероприятия на неделю?"
    )
    await event.answer(new_text=text, attachments=[reminder_miss_keyboard(challenge_id)])

# пост-ивент

@router.message_callback(F.callback.payload.startswith("post_back_"))
async def cb_post_back(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("post_back_"))
    await event.answer(
        new_text="ну как, получилось посетить мероприятие?",
        attachments=[post_event_keyboard(challenge_id)],
    )

@router.message_callback(F.callback.payload.startswith("visited_"))
async def cb_visited(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("visited_"))
    await confirm_visit(session, challenge_id)
    await _show_visited_prompt(event, session, challenge_id)

@router.message_callback(F.callback.payload.startswith("missed_"))
async def cb_missed(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("missed_"))
    await miss_visit(session, challenge_id)
    text = (
        "очень жаль. в таком случае мероприятие не зачтется в твоем стрике.\n"
        "\n"
        "хочешь посмотреть другие варианты мероприятий?"
    )
    await event.answer(new_text=text, attachments=[post_event_miss_keyboard(challenge_id)])

# рейтинг

@router.message_callback(F.callback.payload.startswith("rate_back_"))
async def cb_rate_back(event: MessageCallback, session: AsyncSession):
    challenge_id = int(event.callback.payload.removeprefix("rate_back_"))
    await _show_visited_prompt(event, session, challenge_id)

@router.message_callback(F.callback.payload.startswith("rate_"))
async def cb_rate(event: MessageCallback, session: AsyncSession):
    parts = event.callback.payload.removeprefix("rate_").split("_")
    stars = int(parts[0])
    challenge_id = int(parts[1])
    await save_rating(session, challenge_id, stars)
    text = (
        "спасибо! буду учитывать твою оценку в следующей подборке!\n"
        "\n"
        "хочешь посмотреть мероприятия на следующую неделю?"
    )
    await event.answer(new_text=text, attachments=[after_rating_keyboard(challenge_id)])
