"""Shared async database engine and session factory."""

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

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_sync_session_factory: sessionmaker[Session] | None = None


def get_async_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return cached async engine."""
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(
            str(settings.database_url),
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return cached async session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_async_engine(settings),
            expire_on_commit=False,
        )
    return _session_factory


def get_sync_session_factory(settings: Settings | None = None) -> sessionmaker[Session]:
    """Return cached sync session factory for Celery workers."""
    global _sync_session_factory
    if _sync_session_factory is None:
        settings = settings or get_settings()
        sync_url = str(settings.database_url).replace("+asyncpg", "")
        engine = create_engine(sync_url, pool_pre_ping=True)
        _sync_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _sync_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


def reset_session_caches() -> None:
    """Reset cached engines (for tests)."""
    global _engine, _session_factory, _sync_session_factory
    _engine = None
    _session_factory = None
    _sync_session_factory = None
