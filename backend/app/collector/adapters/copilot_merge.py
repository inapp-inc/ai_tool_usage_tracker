"""Shared Copilot metrics + seats merge logic (adapter and verification)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.collector.adapters.base import UsageRecord
from app.collector.adapters.copilot_parsing import parse_copilot_seat, parse_copilot_user_day


def merge_copilot_records(
    metrics_records: list[UsageRecord],
    seat_payloads: list[dict[str, Any]],
    *,
    fallback_at: datetime,
) -> list[UsageRecord]:
    """Same merge order as CopilotUsageAdapter.fetch_usage."""
    records: list[UsageRecord] = []
    seen_ids: set[str] = set()

    for record in metrics_records:
        if record.vendor_event_id in seen_ids:
            continue
        seen_ids.add(record.vendor_event_id)
        records.append(record)

    for seat in seat_payloads:
        seat_record = parse_copilot_seat(seat, fallback_at=fallback_at)
        if seat_record is None:
            continue
        if any(
            record.user_email == seat_record.user_email
            and record.occurred_at.date() == seat_record.occurred_at.date()
            for record in records
        ):
            continue
        if seat_record.vendor_event_id in seen_ids:
            continue
        seen_ids.add(seat_record.vendor_event_id)
        records.append(seat_record)

    return records


def metrics_overlap_exists(
    records: list[UsageRecord],
    *,
    user_email: str | None,
    occurred_date,
) -> bool:
    if not user_email:
        return False
    return any(
        record.user_email == user_email and record.occurred_at.date() == occurred_date
        for record in records
    )
