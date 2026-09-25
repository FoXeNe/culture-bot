from maxapi import F, Router
from maxapi.types import MessageCallback
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.start import _selected_from_user
from bot.keyboards.inline import categories_keyboard, confirm_keyboard, continue_keyboard, pushkin_keyboard
from bot.texts.registration import CATEGORIES_TEXT, PUSHKIN_IDK_TEXT, PUSHKIN_TEXT, PUSHKIN_YES_TEXT, REG_DONE_TEXT
from services.db_queries import get_or_create_user, update_user_pushkin_card

router = Router()

def confirm_text(user) -> str:
    cats = _selected_from_user(user)
    cats_list = "\n".join(f"{i+1}. {c}" for i, c in enumerate(cats)) if cats else "—"
    return f"""\
хорошо, я запомнил:
{cats_list}

интересы можно изменить в меню в любой момент.

кстати, ты можешь заработать стрик, если будешь посещать хотя бы 1 мероприятие в неделю! 😎

тебе будет доступна 1 заморозка в месяц, если посетить мероприятие совсем не получается. \
но если просто так пропустить неделю стрик обнулится 😢"""

@router.message_callback(F.callback.payload == "pushkin_yes")
async def cb_pushkin_yes(event: MessageCallback, session: AsyncSession):
    await update_user_pushkin_card(session, event.from_user.user_id, True)
    await event.answer(new_text=PUSHKIN_YES_TEXT, attachments=[continue_keyboard()])

@router.message_callback(F.callback.payload == "pushkin_no")
async def cb_pushkin_no(event: MessageCallback, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    user.pushkin_card = False
    await session.commit()
    await event.answer(new_text=confirm_text(user), attachments=[confirm_keyboard()])

@router.message_callback(F.callback.payload == "pushkin_idk")
async def cb_pushkin_idk(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text=PUSHKIN_IDK_TEXT, attachments=[continue_keyboard()])

@router.message_callback(F.callback.payload == "pushkin_back")
async def cb_pushkin_back(event: MessageCallback, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    selected = _selected_from_user(user)
    await event.answer(new_text=CATEGORIES_TEXT, attachments=[categories_keyboard(selected)])

@router.message_callback(F.callback.payload == "reg_confirm")
async def cb_reg_confirm(event: MessageCallback, session: AsyncSession):
    user = await get_or_create_user(session, event.from_user.user_id)
    await event.answer(new_text=confirm_text(user), attachments=[confirm_keyboard()])

@router.message_callback(F.callback.payload == "reg_done")
async def cb_reg_done(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text=REG_DONE_TEXT)

@router.message_callback(F.callback.payload == "reg_back")
async def cb_reg_back(event: MessageCallback, session: AsyncSession):
    await event.answer(new_text=PUSHKIN_TEXT, attachments=[pushkin_keyboard()])
