"""Unit tests for Celery BaseTask logging (TASK-INF-003)."""

import logging

import pytest

from app.core.celery_base import BaseTask


def test_correlation_id_logged_on_failure(caplog: pytest.LogCaptureFixture) -> None:
    task = BaseTask()
    task.request = type(
        "Request",
        (),
        {"headers": {"correlation_id": "corr-fail-123", "organization_id": "org-2"}},
    )()

    with caplog.at_level(logging.ERROR):
        task.on_failure(
            RuntimeError("boom"),
            "task-id-1",
            (),
            {},
            None,
        )

    assert any("corr-fail-123" in record.message for record in caplog.records)
