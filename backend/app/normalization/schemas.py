"""Normalized vendor event schemas (token, productivity, license)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class NormalizedTokenEvent:
    source: str
    page: int | None = None
    raw_timestamp_ms: int | None = None
    occurred_at: datetime | None = None
    user_email: str | None = None
    model: str | None = None
    kind: str | None = None
    kind_included_in_plan: bool | None = None
    api_input_tokens: int | None = None
    api_output_tokens: int | None = None
    api_cache_write_tokens: int | None = None
    api_cache_read_tokens: int | None = None
    parsed_input_tokens: int = 0
    parsed_output_tokens: int = 0
    parsed_cache_write_tokens: int = 0
    parsed_cache_read_tokens: int = 0
    parsed_total_tokens: int = 0
    api_charged_cents: int | None = None
    charged_cents_usd: Decimal | None = None
    cost_rule_applied: str | None = None
    estimated_cost_usd: Decimal = Decimal("0")
    cost_matches_rule: bool | None = None
    requests: int = 1
    vendor_event_id: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedProductivityEvent:
    source: str
    page: int | None = None
    report_date: date | None = None
    user_email: str | None = None
    feature: str | None = None
    editor: str | None = None
    language: str | None = None
    active_days: int = 0
    suggestions_count: int = 0
    acceptances_count: int = 0
    acceptance_rate: Decimal | None = None
    chat_turns: int = 0
    lines_suggested: int = 0
    lines_accepted: int = 0
    estimated_cost: Decimal = Decimal("0")
    cost_rule: str | None = None
    vendor_event_id: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedLicenseEvent:
    source: str
    activity_timestamp: datetime | None = None
    user_email: str | None = None
    user_name: str | None = None
    team_name: str | None = None
    project_name: str | None = None
    file_name: str | None = None
    activity_type: str | None = None
    license_type: str | None = None
    seat_assigned: bool = False
    seat_active: bool = False
    last_active_date: date | None = None
    estimated_monthly_cost: Decimal = Decimal("0")
    cost_rule: str | None = None
    vendor_event_id: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)
