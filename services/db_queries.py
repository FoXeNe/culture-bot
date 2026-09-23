"""Запросы к базе данных для бизнес-логики приложения."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import User


async def get_or_create_user(
    session: AsyncSession,
    vk_id: int,
) -> User:
    """Получить пользователя по VK ID или создать нового."""

    result = await session.execute(
        select(User).where(User.user_id == vk_id)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        return user

    user = User(user_id=vk_id)
    session.add(user)

    await session.commit()
    await session.refresh(user)

    return user


async def update_user_categories(
    session: AsyncSession,
    vk_id: int,
    categories: list[str],
) -> None:
    """Обновить выбранные пользователем категории."""

    result = await session.execute(
        select(User).where(User.user_id == vk_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return

    user.categories = ",".join(categories)

    await session.commit()


async def get_user_stats(
    session: AsyncSession,
    vk_id: int,
) -> dict:
    """Получить статистику пользователя для профиля."""

    pass

