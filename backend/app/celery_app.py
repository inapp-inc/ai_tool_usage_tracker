"""Celery application for worker and beat containers (TASK-INF-003)."""

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings
from app.core.celery_base import BaseTask

settings = get_settings()

QUEUE_NAMES = ["ingestion", "reports", "alerts", "email", "maintenance"]

celery_app = Celery(
    "ai_tool_tracker",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
)

celery_app.conf.update(
    task_default_queue="maintenance",
    worker_hijack_root_logger=False,
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.core.tasks.ping_queue": {"queue": "ingestion"},
        "app.core.tasks.ping_maintenance": {"queue": "maintenance"},
    },
    beat_schedule={
        "maintenance-heartbeat": {
            "task": "app.core.tasks.ping_maintenance",
            "schedule": crontab(minute=0),
            "options": {"queue": "maintenance"},
        },
    },
)

celery_app.Task = BaseTask


@celery_app.task(name="app.health.ping")
def ping() -> str:
    """Legacy sample task used to verify worker startup."""
    return "pong"


import app.core.tasks  # noqa: E402, F401
