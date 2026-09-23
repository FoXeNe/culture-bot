"""Запросы к базе данных для бизнес-логики приложения."""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta, timezone

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


async def get_challenge_for_user(
    session: AsyncSession,
    vk_id: int,
    exclude_ids: list[int],
) -> Event | None:
    """Найти активное событие подходящей категории."""

    result = await session.execute(
        select(User).where(User.user_id == vk_id)
    )
    user = result.scalar_one_or_none()

    if user is None or not user.categories:
        return None

    categories = [
        category.strip()
        for category in user.categories.split(",")
        if category.strip()
    ]

    if not categories:
        return None

    query = select(Event).where(
        Event.is_active.is_(True),
        Event.category.in_(categories),
    )

    if exclude_ids:
        query = query.where(~Event.id.in_(exclude_ids))

    result = await session.execute(query)

    return result.scalars().first()

async def create_challenge(
    session: AsyncSession,
    vk_id: int,
    event_id: int,
) -> UserChallenge:
    """Создать недельный челлендж для пользователя."""

    week_start = date.today() - timedelta(days=date.today().weekday())

    challenge = UserChallenge(
        user_id=vk_id,
        event_id=event_id,
        week_start=week_start,
        status=ChallengeStatus.OFFERED,
    )

    session.add(challenge)
    await session.commit()
    await session.refresh(challenge)

    return challenge


async def accept_challenge(
    session: AsyncSession,
    challenge_id: int,
) -> UserChallenge | None:
    """Принять предложенный челлендж."""

    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    challenge.status = ChallengeStatus.ACCEPTED
    challenge.accepted_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(challenge)

    return challenge


async def skip_challenge(
    session: AsyncSession,
    challenge_id: int,
) -> UserChallenge | None:
    """Пропустить предложенный челлендж."""

    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    challenge.status = ChallengeStatus.SKIPPED

    await session.commit()
    await session.refresh(challenge)

    return challenge


async def miss_visit(
    session: AsyncSession,
    challenge_id: int,
) -> User | None:
    """Отметить пропуск и при необходимости использовать freeze."""

    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    user_result = await session.execute(
        select(User).where(User.user_id == challenge.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        return None

    challenge.status = ChallengeStatus.MISSED

    if user.freezes_available > 0:
        user.freezes_available -= 1
    else:
        user.current_streak = 0

    await session.commit()
    await session.refresh(user)

    return user


async def save_rating(
    session: AsyncSession,
    challenge_id: int,
    rating: int,
) -> UserChallenge | None:
    """Сохранить оценку посещенного события."""

    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    challenge.rating = rating

    await session.commit()
    await session.refresh(challenge)

    return challenge


async def get_users_for_weekly_challenge(
    session: AsyncSession,
) -> list[User]:
    """Получить пользователей без челленджа на текущую неделю."""

    week_start = date.today() - timedelta(days=date.today().weekday())

    result = await session.execute(
        select(User).where(
            ~User.challenges.any(
                UserChallenge.week_start == week_start
            )
        )
    )

    return list(result.scalars().all())


async def get_challenges_for_reminder(
    session: AsyncSession,
) -> list[UserChallenge]:
    """Получить принятые челленджи, которым пора отправить напоминание."""

    now = datetime.now(timezone.utc)
    reminder_from = now + timedelta(hours=23)
    reminder_to = now + timedelta(hours=25)

    result = await session.execute(
        select(UserChallenge)
        .join(UserChallenge.event)
        .where(
            UserChallenge.status == ChallengeStatus.ACCEPTED,
            UserChallenge.reminder_sent.is_(False),
            Event.event_date >= reminder_from,
            Event.event_date <= reminder_to,
        )
    )

    return list(result.scalars().all())


async def get_challenges_for_post_event(
    session: AsyncSession,
) -> list[UserChallenge]:
    """Получить челленджи для сообщения после события."""

    now = datetime.now(timezone.utc)
    event_deadline = now - timedelta(hours=5)

    result = await session.execute(
        select(UserChallenge)
        .join(UserChallenge.event)
        .where(
            UserChallenge.status == ChallengeStatus.ACCEPTED,
            UserChallenge.post_event_sent.is_(False),
            Event.event_date <= event_deadline,
        )
    )

    return list(result.scalars().all())


async def get_users_for_streak_check(
    session: AsyncSession,
) -> list[User]:
    """Получить пользователей без подтвержденного челленджа на прошлой неделе."""

    current_week_start = date.today() - timedelta(days=date.today().weekday())
    previous_week_start = current_week_start - timedelta(days=7)

    result = await session.execute(
        select(User).where(
            ~User.challenges.any(
                and_(
                    UserChallenge.week_start == previous_week_start,
                    UserChallenge.status == ChallengeStatus.CONFIRMED,
                )
            )
        )
    )

    return list(result.scalars().all())


async def confirm_visit(
    session: AsyncSession,
    challenge_id: int,
) -> User | None:
    """Подтвердить посещение и обновить стрик пользователя."""

    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one_or_none()

    if challenge is None:
        return None

    user_result = await session.execute(
        select(User).where(User.user_id == challenge.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        return None

    challenge.status = ChallengeStatus.CONFIRMED
    challenge.confirmed_at = datetime.now(timezone.utc)

    user.current_streak += 1

    if user.current_streak > user.max_streak:
        user.max_streak = user.current_streak

    await session.commit()
    await session.refresh(user)

    return user