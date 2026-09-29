from maxapi.types import CallbackButton, LinkButton
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
    builder.row(CallbackButton(text="Готово ->", payload="cat_done"))
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

def challenge_keyboard(challenge_id: int, prev_id: int | None = None, ticket_url: str | None = None):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="❤️", payload=f"accept_{challenge_id}"),
        CallbackButton(text="Подробнее", payload=f"detail_{challenge_id}"),
        CallbackButton(text="Не мое", payload=f"skip_{challenge_id}"),
        CallbackButton(text="В меню", payload="menu"),
    )
    if ticket_url:
        builder.row(LinkButton(text="Купить билет", url=ticket_url))
    if prev_id is not None:
        builder.row(CallbackButton(text="← Назад", payload=f"prev_{prev_id}"))
    return builder.as_markup()

def challenge_detail_keyboard(challenge_id: int, ticket_url: str | None = None):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="❤️", payload=f"accept_{challenge_id}"),
        CallbackButton(text="Не мое", payload=f"skip_{challenge_id}"),
        CallbackButton(text="Назад", payload=f"detail_back_{challenge_id}"),
    )
    if ticket_url:
        builder.row(LinkButton(text="Купить билет", url=ticket_url))
    return builder.as_markup()

def reminder_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Спасибо", payload=f"remind_ok_{challenge_id}"),
        CallbackButton(text="Я не смогу пойти", payload=f"remind_miss_{challenge_id}"),
    )
    return builder.as_markup()

def reminder_miss_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Перейти к подборке", payload="menu_to_catalog"),
        CallbackButton(text="В меню", payload="menu"),
        CallbackButton(text="Назад", payload=f"remind_back_{challenge_id}"),
    )
    return builder.as_markup()

def post_event_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Да", payload=f"visited_{challenge_id}"),
        CallbackButton(text="Не получилось прийти", payload=f"missed_{challenge_id}"),
    )
    return builder.as_markup()

def post_event_miss_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Перейти к подборке", payload="menu_to_catalog"),
        CallbackButton(text="В меню", payload="menu"),
        CallbackButton(text="Назад", payload=f"post_back_{challenge_id}"),
    )
    return builder.as_markup()

def rating_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="*", payload=f"rate_1_{challenge_id}"),
        CallbackButton(text="**", payload=f"rate_2_{challenge_id}"),
        CallbackButton(text="***", payload=f"rate_3_{challenge_id}"),
        CallbackButton(text="****", payload=f"rate_4_{challenge_id}"),
        CallbackButton(text="*****", payload=f"rate_5_{challenge_id}"),
        CallbackButton(text="Назад", payload=f"post_back_{challenge_id}"),
    )
    return builder.as_markup()

def after_rating_keyboard(challenge_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Да", payload="menu_to_catalog"),
        CallbackButton(text="Нет", payload="menu"),
        CallbackButton(text="Назад", payload=f"rate_back_{challenge_id}"),
    )
    return builder.as_markup()

def friday_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Да", payload="menu_to_catalog"),
        CallbackButton(text="Нет", payload="menu"),
    )
    return builder.as_markup()

def no_more_events_keyboard(prev_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Назад", payload=f"prev_{prev_id}"),
        CallbackButton(text="В меню", payload="menu"),
    )
    return builder.as_markup()

def menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="Недельная подборка", payload="menu_weekly"))
    builder.row(CallbackButton(text="Мои мероприятия", payload="menu_events"))
    builder.row(CallbackButton(text="Изменить категории", payload="menu_categories"))
    builder.row(CallbackButton(text="Мой стрик", payload="menu_streak"))
    return builder.as_markup()

def streak_keyboard(has_freeze: bool):
    builder = InlineKeyboardBuilder()
    builder.row(CallbackButton(text="В меню", payload="menu"))
    if has_freeze:
        builder.row(CallbackButton(text="Активировать заморозку", payload="freeze_activate"))
    return builder.as_markup()

def my_events_keyboard(challenges: list | None = None):
    builder = InlineKeyboardBuilder()
    if challenges:
        for ch in challenges:
            builder.row(CallbackButton(text=f"Отменить: {ch.event.title[:30]}", payload=f"cancel_{ch.id}"))
            if ch.event.ticket_url:
                builder.row(LinkButton(text=f"Билет: {ch.event.title[:30]}", url=ch.event.ticket_url))
    builder.row(CallbackButton(text="В меню", payload="menu"))
    return builder.as_markup()

def confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Перейти к подборке", payload="reg_done"),
        CallbackButton(text="Назад", payload="reg_back"),
    )
    return builder.as_markup()
