from maxapi import F, Router
from maxapi.types import Command, MessageCallback, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import CATEGORIES, categories_keyboard
from services.db_queries import get_or_create_user, get_user_stats, update_user_categories

router = Router()


@router.message_created(Command("start"))
async def cmd_start(event: MessageCreated, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)

    if user.categories is None:
        # новый юзер, показываем выбор категорий
        await event.message.answer(
            text="Для начала давай разберёмся, куда тебе хочется ходить. \
            Можешь выбрать всё, что интересно. потом я буду использовать это для рекомендаций.",
            attachments=[categories_keyboard([])]
        )
    else:
        # уже зарегистрирован, показываем профиль
        stats = await get_user_stats(session, event.from_user.user_id)
        await event.message.answer(
            text=(
                f"стрик: {stats['current_streak']}\n"
                f"максимум: {stats['max_streak']}\n"
                f"уровень: {stats['level']}\n"
                f"заморозки: {stats['freezes_available']}"
            )
        )


@router.message_callback(F.callback.payload.startswith("cat_"))
async def toggle_category(event: MessageCallback, session: AsyncSession):
    payload = event.callback.payload
    user_id = event.from_user.user_id
    user = await get_or_create_user(session, user_id)

    selected = [c.strip() for c in user.categories.split(",") if c.strip()] if user.categories else []

    if payload == "cat_done":
        await update_user_categories(session, user_id, selected)
        await event.answer(new_text="хорошо, запомнил")
        return

    cat = payload[4:]  # убираем "cat_"
    if cat not in CATEGORIES:
        return

    if cat in selected:
        selected.remove(cat)
    else:
        selected.append(cat)

    user.categories = ",".join(selected)
    await session.commit()

    await event.answer(
        new_text="выбери что тебе интересно:",
        attachments=[categories_keyboard(selected)]
    )
