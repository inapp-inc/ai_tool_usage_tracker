"""Integration tests for health endpoint (TASK-INF-002)."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.connectivity import ConnectivityStatus
from app.main import app


@pytest.fixture
def healthy_connectivity() -> ConnectivityStatus:
    return ConnectivityStatus(database="ok", redis="ok")


@pytest.mark.asyncio
async def test_health_v1_ok(healthy_connectivity: ConnectivityStatus) -> None:
    with (
        patch(
            "app.main.verify_connectivity",
            AsyncMock(return_value=healthy_connectivity),
        ),
        patch(
            "app.api.v1.router.verify_connectivity",
            AsyncMock(return_value=healthy_connectivity),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["redis"] == "ok"


@pytest.mark.asyncio
async def test_health_v1_connectivity_degraded() -> None:
    degraded = ConnectivityStatus(database="ok", redis="error")
    with (
        patch(
            "app.main.verify_connectivity",
            AsyncMock(return_value=degraded),
        ),
        patch(
            "app.api.v1.router.verify_connectivity",
            AsyncMock(return_value=degraded),
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["redis"] == "error"
