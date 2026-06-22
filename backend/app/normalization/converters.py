"""Convert normalized events to collector UsageRecord."""

from __future__ import annotations

from datetime import UTC, datetime

from app.collector.adapters.base import UsageRecord
from app.normalization.schemas import (
    NormalizedLicenseEvent,
    NormalizedProductivityEvent,
    NormalizedTokenEvent,
)


def token_to_usage_record(event: NormalizedTokenEvent) -> UsageRecord:
    occurred_at = event.occurred_at or datetime.now(UTC)
    return UsageRecord(
        vendor_event_id=event.vendor_event_id,
        model=event.model,
        occurred_at=occurred_at,
        input_tokens=event.parsed_input_tokens,
        output_tokens=event.parsed_output_tokens,
        cache_write_tokens=event.parsed_cache_write_tokens,
        cache_read_tokens=event.parsed_cache_read_tokens,
        estimated_cost=event.estimated_cost_usd,
        user_email=event.user_email,
        user_name=event.user_email,
        requests=event.requests,
        included_in_plan=bool(event.kind_included_in_plan),
    )


def productivity_to_usage_record(event: NormalizedProductivityEvent) -> UsageRecord:
    """Seat/productivity tools: encode activity counts as requests, not tokens."""
    occurred_at = datetime.combine(
        event.report_date or datetime.now(UTC).date(),
        datetime.min.time(),
        tzinfo=UTC,
    )
    return UsageRecord(
        vendor_event_id=event.vendor_event_id,
        model=f"{event.feature or 'productivity'}",
        occurred_at=occurred_at,
        input_tokens=0,
        output_tokens=0,
        estimated_cost=event.estimated_cost,
        user_email=event.user_email,
        user_name=event.user_email,
        requests=event.suggestions_count + event.chat_turns,
    )


def license_to_usage_record(event: NormalizedLicenseEvent) -> UsageRecord:
    occurred_at = event.activity_timestamp or datetime.now(UTC)
    return UsageRecord(
        vendor_event_id=event.vendor_event_id,
        model=event.license_type or f"{event.source.lower()}-seat",
        occurred_at=occurred_at,
        input_tokens=0,
        output_tokens=0,
        estimated_cost=event.estimated_monthly_cost,
        user_email=event.user_email,
        user_name=event.user_name or event.user_email,
        requests=1 if event.seat_active else 0,
    )
