"""Shared pytest fixtures for auth integration tests."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from app.config import get_settings
from app.connectivity import ConnectivityStatus
from app.db.session import reset_session_caches


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    reset_session_caches()
    yield
    get_settings.cache_clear()
    reset_session_caches()


@pytest.fixture(autouse=True)
def mock_startup_connectivity(request: pytest.FixtureRequest):
    """Avoid real DB/Redis during app lifespan in integration tests."""
    if "integration" not in request.keywords:
        yield
        return
    healthy = ConnectivityStatus(database="ok", redis="ok")
    with patch("app.main.verify_connectivity", AsyncMock(return_value=healthy)):
        yield


@pytest.fixture
def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url


@pytest.fixture
def auth_env(database_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    monkeypatch.setenv(
        "CELERY_BROKER_URL",
        os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    )
    monkeypatch.setenv(
        "CELERY_RESULT_BACKEND",
        os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    )
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "test_jwt_secret_key_for_integration")
    monkeypatch.setenv(
        "CREDENTIAL_ENCRYPTION_KEY", "test_credential_encryption_key_dev"
    )
    monkeypatch.setenv("DEV_SUPER_ADMIN_EMAIL", "admin@acme.example")
    monkeypatch.setenv("DEV_SUPER_ADMIN_PASSWORD", "SecurePass123!")
    get_settings.cache_clear()
    reset_session_caches()
