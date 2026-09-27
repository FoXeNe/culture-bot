from apscheduler.schedulers.asyncio import AsyncIOScheduler
from maxapi import Bot

from bot.handlers.challenge import _reminder_text, send_challenge_card
from bot.keyboards.inline import friday_keyboard, post_event_keyboard, reminder_keyboard
from core.database import async_session
from services.db_queries import (
    create_challenge,
    get_challenge_for_user,
    get_challenges_for_post_event,
    get_challenges_for_reminder,
    get_users_for_friday_reminder,
    get_users_for_weekly_challenge,
    mark_post_event_sent,
    mark_reminder_sent,
)

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# еженедельная рассылка челленджа
async def _weekly_challenge_job(bot: Bot) -> None:
    async with async_session() as session:
        users = await get_users_for_weekly_challenge(session)
        for user in users:
            event = await get_challenge_for_user(session, user.user_id, exclude_ids=[])
            if event is None:
                continue
            challenge = await create_challenge(session, user.user_id, event.id)
            await send_challenge_card(bot, user.user_id, event, challenge.id)

# напоминание за сутки до события
async def _reminder_job(bot: Bot) -> None:
    async with async_session() as session:
        challenges = await get_challenges_for_reminder(session)
        for ch in challenges:
            ev = ch.event
            await bot.send_message(
                user_id=ch.user_id,
                text=_reminder_text(ev),
                attachments=[reminder_keyboard(ch.id)],
            )
            await mark_reminder_sent(session, ch.id)

# спрашиваем сходил ли юзер
async def _post_event_job(bot: Bot) -> None:
    async with async_session() as session:
        challenges = await get_challenges_for_post_event(session)
        for ch in challenges:
            ev = ch.event
            await bot.send_message(
                user_id=ch.user_id,
                text=f"ну как, получилось посетить {ev.title}?",
                attachments=[post_event_keyboard(ch.id)],
            )
            await mark_post_event_sent(session, ch.id)

# если нет принятых мероприятий на неделю
async def _friday_reminder_job(bot: Bot) -> None:
    async with async_session() as session:
        users = await get_users_for_friday_reminder(session)
        for user in users:
            await bot.send_message(
                user_id=user.user_id,
                text=(
                    "осталось всего два дня чтобы продлить стрик!\n"
                    "\n"
                    "хочешь, подскажу интересные мероприятия на выходные?"
                ),
                attachments=[friday_keyboard()],
            )

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler.add_job(
        _weekly_challenge_job,
        trigger="cron",
        day_of_week="mon",
        hour=10,
        minute=0,
        args=[bot],
    )
    scheduler.add_job(
        _reminder_job,
        trigger="interval",
        hours=1,
        args=[bot],
    )
    scheduler.add_job(
        _post_event_job,
        trigger="interval",
        hours=1,
        args=[bot],
    )
    scheduler.add_job(
        _friday_reminder_job,
        trigger="cron",
        day_of_week="fri",
        hour=10,
        minute=0,
        args=[bot],
    )
    return scheduler
