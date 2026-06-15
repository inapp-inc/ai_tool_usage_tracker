"""Integration tests for login rate limiting."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.connectivity import ConnectivityStatus
from app.main import app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_login_throttled(auth_env: None) -> None:
    healthy = ConnectivityStatus(database="ok", redis="ok")
    with (
        patch("app.main.verify_connectivity", AsyncMock(return_value=healthy)),
        patch("app.api.v1.router.verify_connectivity", AsyncMock(return_value=healthy)),
        patch(
            "app.auth.router.LoginRateLimiter.is_blocked",
            AsyncMock(return_value=True),
        ),
        patch("app.auth.router.LoginRateLimiter.close", AsyncMock()),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "admin@acme.example", "password": "SecurePass123!"},
            )
    assert response.status_code == 429
