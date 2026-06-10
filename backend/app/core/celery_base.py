"""Celery task base with observability context (TASK-INF-003)."""

import logging

from celery import Task

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """Base task propagating correlation_id and organization_id in logs."""

    abstract = True

    def _context_headers(self) -> dict[str, str | None]:
        headers = getattr(self.request, "headers", None) or {}
        return {
            "correlation_id": headers.get("correlation_id"),
            "organization_id": headers.get("organization_id"),
        }

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: object,
    ) -> None:
        ctx = self._context_headers()
        logger.error(
            "Task failed task_id=%s correlation_id=%s organization_id=%s error=%s",
            task_id,
            ctx["correlation_id"],
            ctx["organization_id"],
            exc,
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)
