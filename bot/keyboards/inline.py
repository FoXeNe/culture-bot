from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

CATEGORIES = ["Выставки и музеи", "Концерты и музыка", "Театр", "Мастер-классы", "Кино", "Экскурсии", "Квесты и квизы", "Другое"]

def categories_keyboard(selected: list[str]):
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        label = f"✔ {cat}" if cat in selected else cat
        builder.row(CallbackButton(text=label, payload=f"cat_{cat}"))
    builder.row(CallbackButton(text="готово ->", payload="cat_done"))
    return builder.as_markup()
