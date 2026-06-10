"""Unit tests for application settings (TASK-INF-002)."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_load_with_required_fields() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
        REDIS_URL="redis://localhost:6379/0",
        CELERY_BROKER_URL="redis://localhost:6379/1",
        CELERY_RESULT_BACKEND="redis://localhost:6379/2",
    )
    assert settings.environment == "development"
    assert settings.jwt_access_token_expire_minutes == 30


def test_missing_database_url_raises() -> None:
    with pytest.raises(ValidationError):
        Settings(
            REDIS_URL="redis://localhost:6379/0",
            CELERY_BROKER_URL="redis://localhost:6379/1",
            CELERY_RESULT_BACKEND="redis://localhost:6379/2",
        )


def test_jwt_secret_required_in_production() -> None:
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db",
            REDIS_URL="redis://localhost:6379/0",
            CELERY_BROKER_URL="redis://localhost:6379/1",
            CELERY_RESULT_BACKEND="redis://localhost:6379/2",
            ENVIRONMENT="production",
            JWT_SECRET_KEY="change_me_jwt_secret_dev_only",
        )
