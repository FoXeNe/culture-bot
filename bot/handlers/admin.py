import os
from maxapi import F, Router
from maxapi.types import CallbackButton, Command, MessageCallback, MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import menu_keyboard
from bot.notifications import send_friday, send_podborka, send_post_event, send_reminder
from services.db_queries import (
    get_latest_accepted_challenge,
    get_or_create_user,
    reset_streak,
    reset_user_progress,
)

router = Router()

def _admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "")
    return {int(x.strip()) for x in raw.split(",") if x.strip()}

def _is_admin(user_id: int) -> bool:
    return user_id in _admin_ids()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="1. Показать подборку", payload="admin_show_podborka"))
    builder.row(CallbackButton(text="2. Тест напоминание", payload="admin_test_reminder"))
    builder.row(CallbackButton(text="3. Тест пост-ивент", payload="admin_test_post_event"))
    builder.row(CallbackButton(text="4. Тест пятница", payload="admin_test_friday"))
    builder.row(CallbackButton(text="5. Открыть меню", payload="admin_open_menu"))
    builder.row(CallbackButton(text="6. Сбросить стрик", payload="admin_reset_streak"))
    builder.row(CallbackButton(text="7. Сбросить прогресс", payload="admin_reset_progress"))
    return builder.as_markup()

@router.message_created(Command("admin"))
async def cmd_admin(event: MessageCreated, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await event.message.answer(text="Админ панель", attachments=[admin_keyboard()])

@router.message_callback(F.callback.payload == "admin_show_podborka")
async def cb_admin_show_podborka(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    user_id = event.from_user.user_id
    user = await get_or_create_user(session, user_id)
    if user.pushkin_card is None:
        await event.bot.send_message(user_id=user_id, text="Сначала пройди регистрацию")
        return
    ok = await send_podborka(event.bot, session, user_id)
    if not ok:
        await event.bot.send_message(user_id=user_id, text="Событий нет")

@router.message_callback(F.callback.payload == "admin_test_reminder")
async def cb_admin_test_reminder(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    ch = await get_latest_accepted_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.bot.send_message(user_id=event.from_user.user_id, text="Нет челленджа, сначала покажи подборку и прими мероприятие")
        return
    await send_reminder(event.bot, ch)

@router.message_callback(F.callback.payload == "admin_test_post_event")
async def cb_admin_test_post_event(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    ch = await get_latest_accepted_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.bot.send_message(user_id=event.from_user.user_id, text="Нет челленджа, сначала покажи подборку и прими мероприятие")
        return
    await send_post_event(event.bot, ch)

@router.message_callback(F.callback.payload == "admin_test_friday")
async def cb_admin_test_friday(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await send_friday(event.bot, event.from_user.user_id)

@router.message_callback(F.callback.payload == "admin_open_menu")
async def cb_admin_open_menu(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await event.bot.send_message(user_id=event.from_user.user_id, text="Меню", attachments=[menu_keyboard()])

@router.message_callback(F.callback.payload == "admin_reset_streak")
async def cb_admin_reset_streak(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await reset_streak(session, event.from_user.user_id)
    await event.bot.send_message(user_id=event.from_user.user_id, text="Стрик обнулён")

@router.message_callback(F.callback.payload == "admin_reset_progress")
async def cb_admin_reset_progress(event: MessageCallback, session: AsyncSession):
    if not _is_admin(event.from_user.user_id):
        return
    await reset_user_progress(session, event.from_user.user_id)
    await event.bot.send_message(user_id=event.from_user.user_id, text="Прогресс сброшен, напиши что-нибудь боту чтобы пройти онбординг заново")
