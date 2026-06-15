"""Integration tests for auth login."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.connectivity import ConnectivityStatus
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def mock_connectivity():
    healthy = ConnectivityStatus(database="ok", redis="ok")
    with (
        patch("app.main.verify_connectivity", AsyncMock(return_value=healthy)),
        patch("app.api.v1.router.verify_connectivity", AsyncMock(return_value=healthy)),
        patch("app.core.rate_limit.LoginRateLimiter.is_blocked", AsyncMock(return_value=False)),
        patch("app.core.rate_limit.LoginRateLimiter.record_failure", AsyncMock()),
        patch("app.core.rate_limit.LoginRateLimiter.close", AsyncMock()),
    ):
        yield


@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_connectivity, auth_env: None) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@acme.example", "password": "WrongPass1!"},
        )
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
