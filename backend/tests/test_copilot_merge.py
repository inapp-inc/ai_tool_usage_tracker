"""Tests for Copilot metrics + seats merge."""

from datetime import UTC, datetime
from decimal import Decimal

from app.collector.adapters.base import UsageRecord
from app.collector.adapters.copilot_merge import merge_copilot_records


def test_merge_prefers_metrics_over_seat_for_same_user_day() -> None:
    metrics = [
        UsageRecord(
            vendor_event_id="copilot-user-1-2026-06-01",
            model="chat",
            occurred_at=datetime(2026, 6, 1, tzinfo=UTC),
            input_tokens=100,
            output_tokens=50,
            estimated_cost=Decimal("0"),
            user_email="alice",
        )
    ]
    seats = [
        {
            "assignee": {"login": "alice"},
            "last_activity_at": "2026-06-01T12:00:00Z",
        }
    ]
    merged = merge_copilot_records(
        metrics,
        seats,
        fallback_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    assert len(merged) == 1
    assert merged[0].vendor_event_id == "copilot-user-1-2026-06-01"
