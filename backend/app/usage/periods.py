"""Shared UTC period windows for usage aggregates."""

from datetime import UTC, datetime


def current_month_window() -> tuple[datetime, datetime]:
    """Calendar month start (UTC) through now (UTC). Matches Teams list metrics."""
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return month_start, now
