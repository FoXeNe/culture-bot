import os

from dotenv import load_dotenv
from vkbottle import Bot

from bot.middlewares.db import DatabaseMiddleware


load_dotenv()

bot = Bot(os.environ["BOT_TOKEN"])

bot.labeler.message_view.register_middleware(DatabaseMiddleware)
bot.labeler.raw_event_view.register_middleware(DatabaseMiddleware)


if __name__ == "__main__":
    bot.run_forever()