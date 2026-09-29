from maxapi import Bot, F, Router
from maxapi.types import BotStarted, Command, MessageCallback, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.assets import WELCOME_IMAGE, get_image
from bot.keyboards.inline import CATEGORIES, categories_keyboard, menu_keyboard, pushkin_keyboard, welcome_keyboard
from bot.texts.registration import CATEGORIES_START_TEXT, CATEGORIES_TEXT, PUSHKIN_TEXT, WELCOME_TEXT
from services.db_queries import get_or_create_user, get_user_stats, update_user_categories

router = Router()

def _selected_from_user(user) -> list[str]:
    return [c.strip() for c in user.categories.split(",") if c.strip()] if user.categories else []

# показывает нужный экран в зависимости от того где юзер остановился в онбординге
async def _send_funnel(bot: Bot, user_id: int, user) -> None:
    if user.categories is None:
        # новый юзер, показываем велком с картинкой
        img = await get_image(bot, WELCOME_IMAGE)
        attachments = [img, welcome_keyboard()] if img else [welcome_keyboard()]
        await bot.send_message(user_id=user_id, text=WELCOME_TEXT, attachments=attachments)
    elif user.pushkin_card is None:
        # категории выбраны, онбординг не завершен
        await bot.send_message(user_id=user_id, text=PUSHKIN_TEXT, attachments=[pushkin_keyboard()])
    else:
        # уже зарегистрирован, показываем меню
        await bot.send_message(user_id=user_id, text="меню", attachments=[menu_keyboard()])

@router.message_created(Command("challenge"))
async def cmd_challenge(event: MessageCreated, session: AsyncSession):
    from bot.handlers.challenge import send_challenge_card
    from services.db_queries import create_challenge, get_challenge_for_user, get_event_attendee_count, get_or_create_user
    user_id = event.from_user.user_id
    user = await get_or_create_user(session, user_id)
    if user.pushkin_card is None:
        await event.message.answer(text="сначала пройди регистрацию /start")
        return
    ev = await get_challenge_for_user(session, user_id, exclude_ids=[])
    if ev is None:
        await event.message.answer(text="событий нет")
        return
    challenge = await create_challenge(session, user_id, ev.id)
    count = await get_event_attendee_count(session, ev.id)
    await send_challenge_card(event.message.bot, user_id, ev, challenge.id, count)

@router.bot_started()
async def on_bot_started(event: BotStarted, session: AsyncSession):
    user = await get_or_create_user(session, event.user.user_id)
    await _send_funnel(event.bot, event.user.user_id, user)

@router.message_created(Command("start"))
async def cmd_start(event: MessageCreated, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    await _send_funnel(event.message.bot, event.from_user.user_id, user)

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
        if user.pushkin_card is not None:
            # уже зарегистрирован, возвращаем в меню
            await event.answer(new_text="категории обновлены!", attachments=[menu_keyboard()])
        else:
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

# любой текст прогоняем через воронку, должен быть последним хендлером
# что бы не перехватывать /start и /challenge
@router.message_created()
async def catch_all(event: MessageCreated, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    await _send_funnel(event.message.bot, event.from_user.user_id, user)
