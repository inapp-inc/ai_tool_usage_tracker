"""Connectivity checks for PostgreSQL and Redis (TASK-INF-001)."""

from dataclasses import dataclass

import redis.asyncio as redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings


@dataclass(frozen=True)
class ConnectivityStatus:
    """Result of dependency connectivity checks."""

    database: str
    redis: str

    @property
    def is_healthy(self) -> bool:
        return self.database == "ok" and self.redis == "ok"


def create_engine(settings: Settings) -> AsyncEngine:
    """Create async SQLAlchemy engine from settings."""
    return create_async_engine(
        str(settings.database_url),
        pool_pre_ping=True,
    )


async def check_postgres(engine: AsyncEngine) -> str:
    """Verify PostgreSQL connectivity."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def check_redis(redis_url: str) -> str:
    """Verify Redis connectivity."""
    client = redis.from_url(redis_url, decode_responses=True)
    try:
        response = await client.ping()
        if response is True:
            return "ok"
        return "error"
    except Exception:
        return "error"
    finally:
        await client.aclose()


async def verify_connectivity(settings: Settings) -> ConnectivityStatus:
    """Check PostgreSQL and Redis using configured service hostnames."""
    engine = create_engine(settings)
    try:
        database_status = await check_postgres(engine)
    finally:
        await engine.dispose()

    redis_status = await check_redis(str(settings.redis_url))
    return ConnectivityStatus(database=database_status, redis=redis_status)
