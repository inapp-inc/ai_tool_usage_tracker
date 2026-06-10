"""Integration tests for Celery queue routing (TASK-INF-003)."""

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def celery_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv(
        "DATABASE_URL",
        os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://aitracker:secret@localhost:5432/aitracker",
        ),
    )
    monkeypatch.setenv("REDIS_URL", os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    monkeypatch.setenv(
        "CELERY_BROKER_URL",
        os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    )
    monkeypatch.setenv(
        "CELERY_RESULT_BACKEND",
        os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    )
    get_settings.cache_clear()


def test_ingestion_queue_routing(celery_env: None) -> None:
    from app.celery_app import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_store_eager_result = True

    result = celery_app.send_task(
        "app.core.tasks.ping_queue",
        args=["ingestion"],
        queue="ingestion",
    )
    assert result.get(timeout=5) == "pong:ingestion"
