"""Запросы к базе данных для бизнес-логики приложения."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import User, UserChallenge, ChallengeStatus, Event


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

def _get_level_and_badge(streak: int) -> tuple[str, str]:
    """Определить уровень и бейдж по текущему стрику."""

    if streak <= 2:
        return "Новичок", "🌱"

    if streak <= 5:
        return "Исследователь", "🔎"

    if streak <= 11:
        return "Ценитель", "🎭"

    if streak <= 23:
        return "Знаток", "🏆"

    return "Легенда", "👑"


async def get_user_stats(
    session: AsyncSession,
    vk_id: int,
) -> dict:
    """Получить статистику пользователя для профиля."""

    result = await session.execute(
        select(User).where(User.user_id == vk_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        return {}

    confirmed_result = await session.execute(
        select(func.count(UserChallenge.id)).where(
            UserChallenge.user_id == vk_id,
            UserChallenge.status == ChallengeStatus.CONFIRMED,
        )
    )

    total_confirmed = confirmed_result.scalar() or 0

    level, badge = _get_level_and_badge(user.current_streak)

    return {
        "current_streak": user.current_streak,
        "max_streak": user.max_streak,
        "level": level,
        "badge": badge,
        "freezes_available": user.freezes_available,
        "total_confirmed": total_confirmed,
    }