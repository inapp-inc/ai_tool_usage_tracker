"""Sample Celery tasks for queue routing verification (TASK-INF-003)."""

from app.celery_app import celery_app
from app.core.celery_base import BaseTask


@celery_app.task(
    base=BaseTask,
    name="app.core.tasks.ping_queue",
    bind=True,
)
def ping_queue(self: BaseTask, queue_name: str) -> str:
    """Return pong for the given queue — used in integration tests."""
    return f"pong:{queue_name}"


@celery_app.task(
    base=BaseTask,
    name="app.core.tasks.ping_maintenance",
    bind=True,
    queue="maintenance",
)
def ping_maintenance(self: BaseTask) -> str:
    """Placeholder Beat task on maintenance queue."""
    return "pong:maintenance"
