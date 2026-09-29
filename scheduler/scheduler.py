from apscheduler.schedulers.asyncio import AsyncIOScheduler
from maxapi import Bot

from bot.notifications import send_friday, send_podborka, send_post_event, send_reminder
from core.database import async_session
from services.db_queries import (
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
            await send_podborka(bot, session, user.user_id)

# напоминание за сутки до события
async def _reminder_job(bot: Bot) -> None:
    async with async_session() as session:
        challenges = await get_challenges_for_reminder(session)
        for ch in challenges:
            await send_reminder(bot, ch)
            await mark_reminder_sent(session, ch.id)

# спрашиваем сходил ли юзер
async def _post_event_job(bot: Bot) -> None:
    async with async_session() as session:
        challenges = await get_challenges_for_post_event(session)
        for ch in challenges:
            await send_post_event(bot, ch)
            await mark_post_event_sent(session, ch.id)

# если нет принятых мероприятий на неделю
async def _friday_reminder_job(bot: Bot) -> None:
    async with async_session() as session:
        users = await get_users_for_friday_reminder(session)
        for user in users:
            await send_friday(bot, user.user_id)

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
