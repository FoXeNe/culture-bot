# модели БД
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


# статусы жизненного цикла челленджа
# offered => accepted => confirmed
# из offered возможен skipped, из accepted может missed
class ChallengeStatus:
    OFFERED = "offered"
    ACCEPTED = "accepted"
    CONFIRMED = "confirmed"
    MISSED = "missed"
    SKIPPED = "skipped"


# профиль пользователя
class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    freezes_available: Mapped[int] = mapped_column(Integer, default=1)
    categories: Mapped[str | None] = mapped_column(String(255))
    pushkin_card: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    challenges: Mapped[list["UserChallenge"]] = relationship(back_populates="user")


# афиша событий для подборок
class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(255))
    venue: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(255))
    about: Mapped[str | None] = mapped_column(String)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price_from: Mapped[int | None] = mapped_column(Integer)
    is_pushkin_card: Mapped[bool] = mapped_column(Boolean, default=False)
    ticket_url: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    challenges: Mapped[list["UserChallenge"]] = relationship(back_populates="event")


# челлендж на неделю
# юзер + событие и весь его жизненный цикл
class UserChallenge(Base):
    __tablename__ = "user_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="CASCADE")
    )
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE")
    )
    week_start: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rating: Mapped[int | None] = mapped_column(Integer)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    post_event_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="challenges")
    event: Mapped["Event"] = relationship(back_populates="challenges")
