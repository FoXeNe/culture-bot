from core.database import async_session
from vkbottle import BaseMiddleware


class DatabaseMiddleware(BaseMiddleware):
    """Передает DB-сессию в handler и закрывает ее после обработки."""

    async def pre(self):
        self.session = async_session()
        self.send({"session": self.session})

    async def post(self):
        await self.session.close()