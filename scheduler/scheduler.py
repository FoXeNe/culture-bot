from apscheduler.schedulers.asyncio import AsyncIOScheduler
from maxapi import Bot

from bot.handlers.challenge import send_challenge_card
from core.database import async_session
from services.db_queries import create_challenge, get_challenge_for_user, get_users_for_weekly_challenge

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

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler.add_job(
        _weekly_challenge_job,
        trigger="cron",
        day_of_week="mon",
        hour=10,
        minute=0,
        args=[bot],
    )
    return scheduler
