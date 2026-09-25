from maxapi import F, Router
from maxapi.types import Command, MessageCallback, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import CATEGORIES, categories_keyboard, pushkin_keyboard, welcome_keyboard
from bot.texts.registration import CATEGORIES_START_TEXT, CATEGORIES_TEXT, PUSHKIN_TEXT, WELCOME_TEXT
from services.db_queries import get_or_create_user, get_user_stats, update_user_categories

router = Router()

def _selected_from_user(user) -> list[str]:
    return [c.strip() for c in user.categories.split(",") if c.strip()] if user.categories else []

@router.message_created(Command("start"))
async def cmd_start(event: MessageCreated, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)

    if user.categories is None:
        # новый юзер, показывает велком
        await event.message.answer(text=WELCOME_TEXT, attachments=[welcome_keyboard()])
    elif user.pushkin_card is None:
        # категории выбраны, онбординг не завершён
        await event.message.answer(text=PUSHKIN_TEXT, attachments=[pushkin_keyboard()])
    else:
        # уже зарегистрирован, показываем профиль
        stats = await get_user_stats(session, event.from_user.user_id)
        await event.message.answer(
            text=f"стрик: {stats['current_streak']} 🔥\n"
                f"максимум: {stats['max_streak']}\n"
                f"уровень: {stats['level']}\n"
                f"заморозки: {stats['freezes_available']}"
        )

@router.message_callback(F.callback.payload == "reg_start")
async def cb_reg_start(event: MessageCallback, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    selected = _selected_from_user(user)
    await event.answer(
        new_text=CATEGORIES_START_TEXT,
        attachments=[categories_keyboard(selected)]
    )

@router.message_callback(F.callback.payload.startswith("cat_"))
async def toggle_category(event: MessageCallback, session: AsyncSession):
    payload = event.callback.payload
    user_id = event.from_user.user_id
    user = await get_or_create_user(session, user_id)
    selected = _selected_from_user(user)

    if payload == "cat_done":
        await update_user_categories(session, user_id, selected)
        await event.answer(new_text=PUSHKIN_TEXT, attachments=[pushkin_keyboard()])
        return

    # убираем cat_
    cat = payload[4:]
    if cat not in CATEGORIES:
        return

    if cat in selected:
        selected.remove(cat)
    else:
        selected.append(cat)

    user.categories = ",".join(selected)
    await session.commit()

    await event.answer(
        new_text=CATEGORIES_TEXT,
        attachments=[categories_keyboard(selected)]
    )
