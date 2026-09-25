from apscheduler.schedulers.asyncio import AsyncIOScheduler
from maxapi import Bot

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# TODO: добавить джобы
def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    return scheduler
