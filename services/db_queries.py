from datetime import date, datetime, timedelta, timezone
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.models import ChallengeStatus, Event, User, UserChallenge

WEEK_CARD_LIMIT = 10

def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())

# юзер

async def get_or_create_user(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(user_id=user_id)
        session.add(user)
        await session.commit()
    return user

async def update_user_categories(
    session: AsyncSession, user_id: int, categories: list[str]
) -> None:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()
    user.categories = ",".join(categories)
    await session.commit()

async def update_user_pushkin_card(
    session: AsyncSession, user_id: int, has_card: bool
) -> None:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()
    user.pushkin_card = has_card
    await session.commit()

async def get_user_stats(session: AsyncSession, user_id: int) -> dict:
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()

    count_result = await session.execute(
        select(func.count(UserChallenge.id)).where(
            and_(
                UserChallenge.user_id == user_id,
                UserChallenge.status == ChallengeStatus.CONFIRMED,
            )
        )
    )
    total_confirmed = count_result.scalar_one()

    return {
        "current_streak": user.current_streak,
        "max_streak": user.max_streak,
        "level": total_confirmed // 5,
        "freezes_available": user.freezes_available,
        "total_confirmed": total_confirmed,
    }

# ивенты

async def get_upcoming_challenges(session: AsyncSession, user_id: int) -> list[UserChallenge]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(UserChallenge)
        .options(selectinload(UserChallenge.event))
        .join(Event)
        .where(
            and_(
                UserChallenge.user_id == user_id,
                UserChallenge.status == ChallengeStatus.ACCEPTED,
                Event.event_date > now,
            )
        )
        .order_by(Event.event_date)
    )
    return list(result.scalars().all())

async def get_current_week_challenge(session: AsyncSession, user_id: int) -> UserChallenge | None:
    this_week = _week_start(date.today())
    result = await session.execute(
        select(UserChallenge)
        .options(selectinload(UserChallenge.event))
        .where(
            and_(
                UserChallenge.user_id == user_id,
                UserChallenge.week_start == this_week,
                UserChallenge.status == ChallengeStatus.OFFERED,
            )
        )
        .limit(1)
    )
    return result.scalars().first()

async def use_freeze(session: AsyncSession, user_id: int) -> bool:
    # возвращает false если заморозок нет
    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one()
    if user.freezes_available <= 0:
        return False
    user.freezes_available -= 1
    await session.commit()
    return True

async def get_event_by_challenge_id(session: AsyncSession, challenge_id: int) -> Event:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    event_result = await session.execute(select(Event).where(Event.id == challenge.event_id))
    return event_result.scalar_one()

async def get_week_event_ids(session: AsyncSession, user_id: int) -> list[int]:
    this_week = _week_start(date.today())
    result = await session.execute(
        select(UserChallenge.event_id).where(
            and_(
                UserChallenge.user_id == user_id,
                UserChallenge.week_start == this_week,
            )
        )
    )
    return list(result.scalars().all())

async def get_challenge_for_user(
    session: AsyncSession, user_id: int, exclude_ids: list[int]
) -> Event | None:
    # лимит в 10 карточек
    if len(exclude_ids) >= WEEK_CARD_LIMIT:
        return None

    result = await session.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    query = select(Event).where(
        and_(Event.is_active == True, Event.event_date > datetime.now(timezone.utc))
    )

    if user and user.categories:
        cats = [c.strip() for c in user.categories.split(",") if c.strip()]
        if cats:
            query = query.where(Event.category.in_(cats))

    if exclude_ids:
        query = query.where(Event.id.not_in(exclude_ids))

    # от дешевого к дорогому
    query = query.order_by(Event.price_from.asc(), Event.id.asc()).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none()

async def get_event_attendee_count(session: AsyncSession, event_id: int) -> int:
    # сколько людей приняли этот же ивент
    result = await session.execute(
        select(func.count(func.distinct(UserChallenge.user_id))).where(
            and_(
                UserChallenge.event_id == event_id,
                UserChallenge.status == ChallengeStatus.ACCEPTED,
            )
        )
    )
    return result.scalar_one()

# челленджи

async def create_challenge(
    session: AsyncSession, user_id: int, event_id: int
) -> UserChallenge:
    challenge = UserChallenge(
        user_id=user_id,
        event_id=event_id,
        week_start=_week_start(date.today()),
        status=ChallengeStatus.OFFERED,
    )
    session.add(challenge)
    await session.commit()
    return challenge

async def reset_week_offers(session: AsyncSession, user_id: int) -> None:
    # убираем показанные и пролистанные ивенты этой недели, чтобы юзер смог
    # заново просмотреть всю подборку. принятые не трогаем — они уже в планах
    this_week = _week_start(date.today())
    await session.execute(
        delete(UserChallenge).where(
            and_(
                UserChallenge.user_id == user_id,
                UserChallenge.week_start == this_week,
                UserChallenge.status.in_([ChallengeStatus.OFFERED, ChallengeStatus.SKIPPED]),
            )
        )
    )
    await session.commit()

async def accept_challenge(session: AsyncSession, challenge_id: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.status = ChallengeStatus.ACCEPTED
    challenge.accepted_at = datetime.now(timezone.utc)
    await session.commit()

async def skip_challenge(session: AsyncSession, challenge_id: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.status = ChallengeStatus.SKIPPED
    await session.commit()

async def cancel_challenge(session: AsyncSession, challenge_id: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.status = ChallengeStatus.SKIPPED
    await session.commit()

async def confirm_visit(session: AsyncSession, challenge_id: int) -> User:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    user_result = await session.execute(
        select(User).where(User.user_id == challenge.user_id)
    )
    user = user_result.scalar_one()
    # идемпотентно: не инкрементим стрик если уже подтверждено
    if challenge.status == ChallengeStatus.CONFIRMED:
        return user
    challenge.status = ChallengeStatus.CONFIRMED
    challenge.confirmed_at = datetime.now(timezone.utc)
    user.current_streak += 1
    if user.current_streak > user.max_streak:
        user.max_streak = user.current_streak
    await session.commit()
    return user

async def miss_visit(session: AsyncSession, challenge_id: int) -> User:
    # просто помечает как пропущенный, сброс стрика — еженедельный job
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    user_result = await session.execute(
        select(User).where(User.user_id == challenge.user_id)
    )
    user = user_result.scalar_one()
    if challenge.status == ChallengeStatus.MISSED:
        return user
    challenge.status = ChallengeStatus.MISSED
    await session.commit()
    return user

async def get_stats_by_challenge(session: AsyncSession, challenge_id: int) -> dict:
    result = await session.execute(
        select(UserChallenge.user_id).where(UserChallenge.id == challenge_id)
    )
    user_id = result.scalar_one()
    return await get_user_stats(session, user_id)

async def save_rating(session: AsyncSession, challenge_id: int, rating: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.rating = rating
    await session.commit()

# планировщик

async def get_users_for_weekly_challenge(session: AsyncSession) -> list[User]:
    this_week = _week_start(date.today())
    # юзеры у которых ещё нет челленджа на эту неделю
    already_has = select(UserChallenge.user_id).where(
        UserChallenge.week_start == this_week
    )
    result = await session.execute(
        select(User).where(User.user_id.not_in(already_has))
    )
    return list(result.scalars().all())

async def get_challenges_for_reminder(session: AsyncSession) -> list[UserChallenge]:
    now = datetime.now(timezone.utc)
    in_24h = now + timedelta(hours=24)
    result = await session.execute(
        select(UserChallenge)
        .options(selectinload(UserChallenge.event))
        .join(Event)
        .where(
            and_(
                UserChallenge.status == ChallengeStatus.ACCEPTED,
                UserChallenge.reminder_sent == False,
                Event.event_date > now,
                Event.event_date <= in_24h,
            )
        )
    )
    return list(result.scalars().all())

async def get_challenges_for_post_event(session: AsyncSession) -> list[UserChallenge]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(UserChallenge)
        .options(selectinload(UserChallenge.event))
        .join(Event)
        .where(
            and_(
                UserChallenge.status == ChallengeStatus.ACCEPTED,
                UserChallenge.post_event_sent == False,
                Event.event_date < now,
            )
        )
    )
    return list(result.scalars().all())

async def mark_reminder_sent(session: AsyncSession, challenge_id: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.reminder_sent = True
    await session.commit()

async def mark_post_event_sent(session: AsyncSession, challenge_id: int) -> None:
    result = await session.execute(
        select(UserChallenge).where(UserChallenge.id == challenge_id)
    )
    challenge = result.scalar_one()
    challenge.post_event_sent = True
    await session.commit()

async def get_latest_user_challenge(session: AsyncSession, user_id: int) -> UserChallenge | None:
    result = await session.execute(
        select(UserChallenge)
        .options(selectinload(UserChallenge.event))
        .where(UserChallenge.user_id == user_id)
        .order_by(UserChallenge.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

async def get_users_for_friday_reminder(session: AsyncSession) -> list[User]:
    this_week = _week_start(date.today())
    # зарегистрированные юзеры без принятых ивентов на эту неделю
    accepted_this_week = select(UserChallenge.user_id).where(
        and_(
            UserChallenge.week_start == this_week,
            UserChallenge.status == ChallengeStatus.ACCEPTED,
        )
    )
    result = await session.execute(
        select(User).where(
            and_(
                User.pushkin_card.isnot(None),
                User.user_id.not_in(accepted_this_week),
            )
        )
    )
    return list(result.scalars().all())

async def get_users_for_streak_check(session: AsyncSession) -> list[User]:
    last_week = _week_start(date.today()) - timedelta(weeks=1)
    # у кого был челлендж на прошлой неделе, но ни одного подтвержденного
    had_challenge = select(UserChallenge.user_id).where(
        UserChallenge.week_start == last_week
    )
    confirmed_last_week = select(UserChallenge.user_id).where(
        and_(
            UserChallenge.week_start == last_week,
            UserChallenge.status == ChallengeStatus.CONFIRMED,
        )
    )
    result = await session.execute(
        select(User).where(
            and_(
                User.user_id.in_(had_challenge),
                User.user_id.not_in(confirmed_last_week),
            )
        )
    )
    return list(result.scalars().all())
