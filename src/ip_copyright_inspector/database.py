"""SQLAlchemy 2.0 asynchronous persistence setup."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
import os

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./ip_copyright_inspector.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


class Base(DeclarativeBase):
    """Declarative mapping root."""


class ComparisonRecord(Base):
    """A result record that deliberately excludes the original text."""

    __tablename__ = "comparison_records"
    __table_args__ = (
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="score_between_0_and_1"),
        CheckConstraint("ngram_size >= 1 AND ngram_size <= 8", name="valid_ngram_size"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(
        String(64), default="character_ngram_jaccard", nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    ngram_size: Mapped[int] = mapped_column(Integer, nullable=False)
    left_ngram_count: Mapped[int] = mapped_column(Integer, nullable=False)
    right_ngram_count: Mapped[int] = mapped_column(Integer, nullable=False)
    intersection_count: Mapped[int] = mapped_column(Integer, nullable=False)
    union_count: Mapped[int] = mapped_column(Integer, nullable=False)
    left_normalized_length: Mapped[int] = mapped_column(Integer, nullable=False)
    right_normalized_length: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield one session per request or background operation."""

    async with async_session_factory() as session:
        yield session


async def create_schema() -> None:
    """Create the exercise schema without introducing a migration tool."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Release pooled connections during application shutdown."""

    await engine.dispose()
