from maxapi import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.challenge import _reminder_text, send_challenge_card
from bot.keyboards.inline import friday_keyboard, monday_push_keyboard, post_event_keyboard, reminder_keyboard
from models.models import UserChallenge
from services.db_queries import create_challenge, get_challenge_for_user, get_event_attendee_count

# и планировщик, и админка зовут эти функции

# карточка подборки. возвращает False если событий не нашлось
async def send_podborka(
    bot: Bot, session: AsyncSession, user_id: int, exclude_ids: list[int] | None = None
) -> bool:
    ev = await get_challenge_for_user(session, user_id, exclude_ids=exclude_ids or [])
    if ev is None:
        return False
    challenge = await create_challenge(session, user_id, ev.id)
    count = await get_event_attendee_count(session, ev.id)
    await send_challenge_card(bot, user_id, ev, challenge.id, count)
    return True

async def send_monday_push(bot: Bot, user_id: int) -> None:
    await bot.send_message(
        user_id=user_id,
        text=(
            "Появилась новая подборка мероприятий на неделю!\n"
            "Не забудь проверить, вдруг что-то придется по душе.\n\n"
            "Напоминаю, что подборка обновляется каждый понедельник."
        ),
        attachments=[monday_push_keyboard()],
    )

# напоминание за сутки до события
async def send_reminder(bot: Bot, challenge: UserChallenge) -> None:
    await bot.send_message(
        user_id=challenge.user_id,
        text=_reminder_text(challenge.event),
        attachments=[reminder_keyboard(challenge.id)],
    )

# вопрос сходил ли юзер после события
async def send_post_event(bot: Bot, challenge: UserChallenge) -> None:
    await bot.send_message(
        user_id=challenge.user_id,
        text=f"Ну как, получилось посетить {challenge.event.title}?",
        attachments=[post_event_keyboard(challenge.id)],
    )

# уведомление в пятницу тем, кто на неделе ничего не выбрал
async def send_friday(bot: Bot, user_id: int) -> None:
    await bot.send_message(
        user_id=user_id,
        text="Осталось всего два дня чтобы продлить стрик!\n\nХочешь, подскажу интересные мероприятия на выходные?",
        attachments=[friday_keyboard()],
    )
