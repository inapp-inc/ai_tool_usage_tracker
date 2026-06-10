"""Async and sync database session factories."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from app.config import Settings, get_settings


def create_async_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Create async SQLAlchemy engine."""
    return create_async_engine(
        str(settings.database_url),
        pool_pre_ping=True,
    )


def create_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    """Create async session factory for FastAPI dependencies."""
    engine = create_async_engine_from_settings(settings)
    return async_sessionmaker(engine, expire_on_commit=False)


def create_sync_session_factory(settings: Settings) -> sessionmaker[Session]:
    """Create sync session factory for Celery worker tasks."""
    sync_url = str(settings.database_url).replace("+asyncpg", "")
    engine = create_engine(sync_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    settings = get_settings()
    session_factory = create_session_factory(settings)
    async with session_factory() as session:
        yield session
