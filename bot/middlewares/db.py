from typing import Any, Awaitable, Callable

from maxapi.filters.middleware import BaseMiddleware
from maxapi.types import UpdateUnion

from core.database import async_session

# кладет db сессию в data['session'] на каждый запрос
class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[UpdateUnion, dict[str, Any]], Awaitable[Any]],
        event_object: UpdateUnion,
        data: dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            return await handler(event_object, data)
