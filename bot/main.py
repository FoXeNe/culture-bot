import asyncio
import logging
import os

from dotenv import load_dotenv
from maxapi import Bot, Dispatcher

from bot.handlers.routers import routers
from bot.middlewares.db import DatabaseMiddleware
from scheduler.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
load_dotenv()

bot = Bot(os.environ["BOT_TOKEN"])
dp = Dispatcher()

# на каждый апдейт кладем в data готовую db сессию
dp.outer_middlewares.append(DatabaseMiddleware())

# подключаем все роутеры из handlers/
dp.include_routers(*routers)

# on_started дергается один раз перед поллингом
# тут поднимаем планировщик
@dp.on_started()
async def on_started() -> None:
    scheduler = setup_scheduler(bot)
    scheduler.start()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
