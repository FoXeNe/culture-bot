from maxapi import F, Router
from maxapi.types import Command, MessageCallback, MessageCreated
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import CATEGORIES, categories_keyboard, menu_keyboard, pushkin_keyboard, welcome_keyboard
from bot.texts.registration import CATEGORIES_START_TEXT, CATEGORIES_TEXT, PUSHKIN_TEXT, WELCOME_TEXT
from services.db_queries import get_or_create_user, get_user_stats, update_user_categories

router = Router()

def _selected_from_user(user) -> list[str]:
    return [c.strip() for c in user.categories.split(",") if c.strip()] if user.categories else []

@router.message_created(Command("challenge"))
async def cmd_challenge(event: MessageCreated, session: AsyncSession):
    from bot.handlers.challenge import send_challenge_card
    from services.db_queries import create_challenge, get_challenge_for_user, get_or_create_user
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
    await send_challenge_card(event.message.bot, user_id, ev, challenge.id)

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
        # уже зарегистрирован, показываем меню
        await event.message.answer(text="меню", attachments=[menu_keyboard()])

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

# TODO удалить перед релизом
@router.message_created(Command("test_reminder"))
async def cmd_test_reminder(event: MessageCreated, session: AsyncSession):
    from bot.handlers.challenge import _reminder_text
    from bot.keyboards.inline import reminder_keyboard
    from services.db_queries import get_latest_user_challenge
    ch = await get_latest_user_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.message.answer(text="нет challenge")
        return
    await event.message.answer(text=_reminder_text(ch.event), attachments=[reminder_keyboard(ch.id)])

@router.message_created(Command("test_post_event"))
async def cmd_test_post_event(event: MessageCreated, session: AsyncSession):
    from bot.keyboards.inline import post_event_keyboard
    from services.db_queries import get_latest_user_challenge
    ch = await get_latest_user_challenge(session, event.from_user.user_id)
    if ch is None:
        await event.message.answer(text="нет challenge")
        return
    await event.message.answer(
        text=f"ну как, получилось посетить {ch.event.title}?",
        attachments=[post_event_keyboard(ch.id)],
    )

@router.message_created(Command("test_friday"))
async def cmd_test_friday(event: MessageCreated, session: AsyncSession):
    from bot.keyboards.inline import friday_keyboard
    await event.message.answer(
        text="осталось всего два дня чтобы продлить стрик!\n\nхочешь, подскажу интересные мероприятия на выходные?",
        attachments=[friday_keyboard()],
    )
