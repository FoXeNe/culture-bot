from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

CATEGORIES = ["Выставки и музеи", "Концерты и музыка", "Театр", "Мастер-классы", "Кино", "Экскурсии", "Квесты и квизы", "Другое"]

def welcome_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Начать", payload="reg_start"))
    return builder.as_markup()

def categories_keyboard(selected: list[str]):
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        label = f"✔ {cat}" if cat in selected else cat
        builder.row(CallbackButton(text=label, payload=f"cat_{cat}"))
    builder.row(CallbackButton(text="готово ->", payload="cat_done"))
    return builder.as_markup()

def pushkin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Да", payload="pushkin_yes"),
        CallbackButton(text="Нет", payload="pushkin_no"),
        CallbackButton(text="Не знаю", payload="pushkin_idk"),
        CallbackButton(text="Назад", payload="pushkin_back"),
    )
    return builder.as_markup()

def continue_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Продолжить →", payload="reg_confirm"))
    return builder.as_markup()

def challenge_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="❤️", payload=f"accept_{challenge_id}"),
        CallbackButton(text="Подробнее", payload=f"detail_{challenge_id}"),
        CallbackButton(text="👎", payload=f"skip_{challenge_id}"),
        CallbackButton(text="В меню", payload="menu"),
    )
    return builder.as_markup()

def challenge_detail_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="❤️", payload=f"accept_{challenge_id}"),
        CallbackButton(text="Пропустить", payload=f"skip_{challenge_id}"),
        CallbackButton(text="Назад", payload=f"detail_back_{challenge_id}"),
    )
    return builder.as_markup()

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Перейти к подборке", payload="reg_done"),
        CallbackButton(text="Назад", payload="reg_back"),
    )
    return builder.as_markup()
