"""Unit tests for connectivity checks (TASK-INF-001)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.connectivity import (
    ConnectivityStatus,
    check_postgres,
    check_redis,
    verify_connectivity,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://aitracker:secret@postgres:5432/aitracker",
        REDIS_URL="redis://redis:6379/0",
        CELERY_BROKER_URL="redis://redis:6379/1",
        CELERY_RESULT_BACKEND="redis://redis:6379/2",
    )


@pytest.mark.asyncio
async def test_check_postgres_returns_ok_on_success() -> None:
    connection = AsyncMock()
    connection.execute = AsyncMock()
    engine = MagicMock()
    engine.connect.return_value.__aenter__.return_value = connection

    result = await check_postgres(engine)

    assert result == "ok"
    connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_postgres_returns_error_on_failure() -> None:
    engine = MagicMock()
    engine.connect.side_effect = OSError("connection refused")

    result = await check_postgres(engine)

    assert result == "error"


@pytest.mark.asyncio
async def test_check_redis_returns_ok_on_ping() -> None:
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)

    with patch("app.connectivity.redis.from_url", return_value=client):
        result = await check_redis("redis://redis:6379/0")

    assert result == "ok"
    client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_connectivity_aggregates_status(settings: Settings) -> None:
    with (
        patch(
            "app.connectivity.check_postgres",
            AsyncMock(return_value="ok"),
        ),
        patch(
            "app.connectivity.check_redis",
            AsyncMock(return_value="ok"),
        ),
        patch("app.connectivity.create_engine") as create_engine,
    ):
        engine = MagicMock()
        engine.dispose = AsyncMock()
        create_engine.return_value = engine

        status = await verify_connectivity(settings)

    assert status == ConnectivityStatus(database="ok", redis="ok")
    assert status.is_healthy is True


@pytest.mark.asyncio
async def test_verify_connectivity_not_healthy_when_redis_fails(
    settings: Settings,
) -> None:
    with (
        patch(
            "app.connectivity.check_postgres",
            AsyncMock(return_value="ok"),
        ),
        patch(
            "app.connectivity.check_redis",
            AsyncMock(return_value="error"),
        ),
        patch("app.connectivity.create_engine") as create_engine,
    ):
        engine = MagicMock()
        engine.dispose = AsyncMock()
        create_engine.return_value = engine

        status = await verify_connectivity(settings)

    assert status.is_healthy is False
