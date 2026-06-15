"""Integration tests for tools and credentials APIs."""

import os
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.connectivity import ConnectivityStatus
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"

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


@pytest.fixture
def migrated_db(auth_env: None, database_url: str) -> None:
    subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, "DATABASE_URL": database_url},
        check=True,
    )
    subprocess.run(
        ["python", "-m", "app.scripts.seed_dev_admin"],
        cwd=BACKEND_ROOT,
        env={
            **os.environ,
            "DATABASE_URL": database_url,
            "PYTHONPATH": str(BACKEND_ROOT),
        },
        check=True,
    )


async def _login_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@acme.example", "password": "SecurePass123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_tools_and_credentials_flow(
    mock_connectivity, migrated_db: None, auth_env: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        token = await _login_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        create_tool = await client.post(
            "/api/v1/tools",
            headers=headers,
            json={
                "name": "Test OpenAI",
                "vendor": "OpenAI",
                "pricing_model": "flat_token",
                "token_price": "0.005",
            },
        )
        assert create_tool.status_code == 201
        tool_id = create_tool.json()["id"]

        list_tools = await client.get("/api/v1/tools", headers=headers)
        assert list_tools.status_code == 200
        assert len(list_tools.json()["data"]) >= 1

        create_cred = await client.post(
            "/api/v1/credentials",
            headers=headers,
            json={
                "tool_id": tool_id,
                "environment": "production",
                "secret_value": "sk-live-testkey1234",
            },
        )
        assert create_cred.status_code == 201
        body = create_cred.json()
        assert body["masked_secret"] == "****1234"
        assert "secret_value" not in body
        credential_id = body["id"]

        rotate = await client.post(
            f"/api/v1/credentials/{credential_id}/rotate",
            headers=headers,
            json={"secret_value": "sk-live-rotated5678"},
        )
        assert rotate.status_code == 200
        assert rotate.json()["masked_secret"] == "****5678"

        delete = await client.delete(
            f"/api/v1/credentials/{credential_id}",
            headers=headers,
        )
        assert delete.status_code == 204

        list_creds = await client.get("/api/v1/credentials", headers=headers)
        assert list_creds.status_code == 200
        assert list_creds.json()["data"] == []
