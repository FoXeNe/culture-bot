from maxapi import F, Router
from maxapi.types import MessageCallback, MessageCreated
from maxapi.enums.attachment import AttachmentType
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import geo_keyboard, geo_menu_keyboard, menu_keyboard
from services.db_queries import update_user_geo

router = Router()

# сохраняем гео юзера
@router.message_created(
    lambda e: any(
        getattr(a, "type", None) == AttachmentType.LOCATION
        for a in (e.message.body.attachments or [])
    )
)
async def handle_location(event: MessageCreated, session: AsyncSession):
    attachments = event.message.body.attachments or []
    loc = next(
        (a for a in attachments if getattr(a, "type", None) == AttachmentType.LOCATION),
        None,
    )
    if loc is None or loc.latitude is None or loc.longitude is None:
        return
    await update_user_geo(session, event.from_user.user_id, loc.latitude, loc.longitude)
    await event.message.answer(
        text="геолокация сохранена! теперь буду показывать мероприятия поближе к тебе",
        attachments=[menu_keyboard()],
    )

@router.message_callback(F.callback.payload == "geo_skip")
async def cb_geo_skip(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text="хорошо, покажу мероприятия без учёта локации", attachments=[menu_keyboard()])

@router.message_callback(F.callback.payload == "menu_geo")
async def cb_menu_geo(event: MessageCallback, session: AsyncSession):
    await event.answer(
        new_text="можешь поделиться геолокацией, буду показывать мероприятия поближе к тебе",
        attachments=[geo_menu_keyboard()],
    )

@router.message_callback(F.callback.payload == "geo_remove")
async def cb_geo_remove(event: MessageCallback, session: AsyncSession):
    await update_user_geo(session, event.from_user.user_id, None, None)
    await event.answer(new_text="геолокация удалена", attachments=[menu_keyboard()])
