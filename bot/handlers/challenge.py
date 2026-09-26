from maxapi import Bot, F, Router
from maxapi.types import MessageCallback
from maxapi.types.attachments.attachment import Attachment, OtherAttachmentPayload
from maxapi.enums.attachment import AttachmentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import challenge_detail_keyboard, challenge_keyboard
from models.models import Event
from services.db_queries import (
    accept_challenge,
    create_challenge,
    get_challenge_for_user,
    get_event_by_challenge_id,
    get_week_event_ids,
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

def _card_attachments(event: Event, challenge_id: int) -> list:
    attachments = []
    if event.image_url:
        attachments.append(
            Attachment(
                type=AttachmentType.IMAGE,
                payload=OtherAttachmentPayload(url=event.image_url),
            )
        )
    attachments.append(challenge_keyboard(challenge_id))
    return attachments

async def send_challenge_card(bot: Bot, user_id: int, event: Event, challenge_id: int) -> None:
    await bot.send_message(
        user_id=user_id,
        text=_card_text(event),
        attachments=_card_attachments(event, challenge_id),
    )

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
        await event.answer(new_text="на этой неделе событий по твоим категориям больше нет")
        return

    new_challenge = await create_challenge(session, user_id, new_event.id)
    await event.answer(
        new_text=_card_text(new_event),
        attachments=_card_attachments(new_event, new_challenge.id),
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

@router.message_callback(F.callback.payload == "menu")
async def cb_menu(event: MessageCallback, session: AsyncSession):
    await event.ack()
