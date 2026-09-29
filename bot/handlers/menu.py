from maxapi import F, Router
from maxapi.types import MessageCallback
from sqlalchemy.ext.asyncio import AsyncSession

from bot.assets import STREAK_IMAGE, get_image
from bot.handlers.challenge import _card_attachments, _card_text
from bot.keyboards.inline import (
    categories_keyboard,
    menu_keyboard,
    my_events_keyboard,
    streak_keyboard,
)
from bot.texts.registration import CATEGORIES_TEXT
from services.db_queries import (
    create_challenge,
    get_challenge_for_user,
    get_current_week_challenge,
    get_event_attendee_count,
    get_or_create_user,
    get_upcoming_challenges,
    get_user_stats,
    get_week_event_ids,
    reset_week_offers,
    use_freeze,
)

router = Router()

MONTHS = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

# показывает текущую карточку челленджа или сообщение что подборки нет
async def _show_catalog(event: MessageCallback, session: AsyncSession, user_id: int) -> None:
    challenge = await get_current_week_challenge(session, user_id)
    if challenge is None:
        await event.answer(new_text="Подборка придёт в понедельник!")
        return
    ev = challenge.event
    count = await get_event_attendee_count(session, ev.id)
    await event.answer(
        new_text=_card_text(ev, count),
        attachments=_card_attachments(ev, challenge.id),
    )

# сбрасывает пролистанные ивенты и показывает подборку с начала
async def _show_weekly(event: MessageCallback, session: AsyncSession, user_id: int) -> None:
    await reset_week_offers(session, user_id)
    exclude_ids = await get_week_event_ids(session, user_id)
    ev = await get_challenge_for_user(session, user_id, exclude_ids=exclude_ids)
    if ev is None:
        await event.answer(
            new_text="На этой неделе событий по твоим категориям больше нет",
            attachments=[menu_keyboard()],
        )
        return
    challenge = await create_challenge(session, user_id, ev.id)
    count = await get_event_attendee_count(session, ev.id)
    await event.answer(
        new_text=_card_text(ev, count),
        attachments=_card_attachments(ev, challenge.id),
    )

@router.message_callback(F.callback.payload == "menu")
async def cb_menu(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text="Меню", attachments=[menu_keyboard()])

@router.message_callback(F.callback.payload == "menu_weekly")
async def cb_menu_weekly(event: MessageCallback, session: AsyncSession):
    await _show_weekly(event, session, event.from_user.user_id)

@router.message_callback(F.callback.payload == "menu_to_catalog")
async def cb_menu_to_catalog(event: MessageCallback, session: AsyncSession):
    await _show_catalog(event, session, event.from_user.user_id)

@router.message_callback(F.callback.payload == "menu_streak")
async def cb_menu_streak(event: MessageCallback, session: AsyncSession):
    user_id = event.from_user.user_id
    stats = await get_user_stats(session, user_id)
    upcoming = await get_upcoming_challenges(session, user_id)

    streak = stats["current_streak"]
    text = (
        f"🔥 Твой культурный стрик — {streak} мероприятий!\n"
        f"Твой уровень: {stats['level']}\n"
        "\n"
        "Посещай мероприятия каждую неделю и продлей стрик, чтобы зарабатывать уровни\n"
        "\n"
        f"Предстоящих мероприятий на этой неделе — {len(upcoming)}\n"
        f"Доступных заморозок — {stats['freezes_available']}"
    )
    kb = streak_keyboard(has_freeze=stats["freezes_available"] > 0)
    img = await get_image(event.bot, STREAK_IMAGE)
    await event.answer(
        new_text=text,
        attachments=[img, kb] if img else [kb],
    )

@router.message_callback(F.callback.payload == "menu_events")
async def cb_menu_events(event: MessageCallback, session: AsyncSession):
    user_id = event.from_user.user_id
    upcoming = await get_upcoming_challenges(session, user_id)

    if not upcoming:
        text = "У тебя пока нет принятых мероприятий"
    else:
        lines = []
        for i, ch in enumerate(upcoming, 1):
            ev = ch.event
            dt = ev.event_date
            date_str = f"{dt.day} {MONTHS[dt.month - 1]}, {dt.strftime('%H:%M')}"
            lines.append(f"{i}. {ev.title} — {date_str}")
        text = "\n".join(lines)

    await event.answer(new_text=text, attachments=[my_events_keyboard(upcoming if upcoming else None)])

@router.message_callback(F.callback.payload == "menu_categories")
async def cb_menu_categories(event: MessageCallback, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    selected = [c.strip() for c in user.categories.split(",") if c.strip()] if user.categories else []
    await event.answer(new_text=CATEGORIES_TEXT, attachments=[categories_keyboard(selected)])

@router.message_callback(F.callback.payload == "freeze_activate")
async def cb_freeze_activate(event: MessageCallback, session: AsyncSession):
    ok = await use_freeze(session, event.from_user.user_id)
    if ok:
        await event.answer(
            new_text=(
                "🧊 Ты использовал заморозку! теперь твой стрик сохранится, "
                "даже если на этой неделе ты не посетишь ни одного мероприятия.\n"
                "\n"
                "Напоминаю, что доступна всего 1 заморозка в месяц."
            ),
            attachments=[menu_keyboard()],
        )
    else:
        await event.answer(new_text="У тебя нет доступных заморозок", attachments=[menu_keyboard()])
