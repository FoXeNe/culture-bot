import os
from maxapi import F, Router
from maxapi.types import Command, MessageCallback, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import friday_keyboard, post_event_keyboard, reminder_keyboard
from services.db_queries import get_latest_user_challenge

router = Router()

def _admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}

def _is_admin(user_id: int) -> bool:
    return user_id in _admin_ids()

from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Тест напоминание", payload="admin_test_reminder"))
    builder.row(CallbackButton(text="Тест пост-ивент", payload="admin_test_post_event"))
    builder.row(CallbackButton(text="Тест пятница", payload="admin_test_friday"))
    return builder.as_markup()

@router.message_created(Command("admin"))
async def cmd_admin(event: MessageCreated, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await event.message.answer(text="Админ панель", attachments=[admin_keyboard()])

@router.message_callback(F.callback.payload == "admin_test_reminder")
async def cb_admin_test_reminder(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    from bot.handlers.challenge import _reminder_text
    ch = await get_latest_user_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.answer(new_text="Нет челленджа, сначала /challenge и прими мероприятие")
        return
    await event.answer(new_text=_reminder_text(ch.event), attachments=[reminder_keyboard(ch.id)])

@router.message_callback(F.callback.payload == "admin_test_post_event")
async def cb_admin_test_post_event(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    ch = await get_latest_user_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.answer(new_text="Нет челленджа, сначала /challenge и прими мероприятие")
        return
    await event.answer(
        new_text=f"Ну как, получилось посетить {ch.event.title}?",
        attachments=[post_event_keyboard(ch.id)],
    )

@router.message_callback(F.callback.payload == "admin_test_friday")
async def cb_admin_test_friday(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await event.answer(
        new_text="Осталось всего два дня чтобы продлить стрик!\n\nХочешь, подскажу интересные мероприятия на выходные?",
        attachments=[friday_keyboard()],
    )
