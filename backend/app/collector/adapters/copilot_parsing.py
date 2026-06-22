"""Parse GitHub Copilot billing seats and usage metrics into UsageRecords."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.collector.adapters.base import ProviderMember, UsageRecord
from app.collector.adapters.copilot_metrics_fields import (
    COPILOT_USED_FLAGS,
    feature_flags_from_row,
    has_usage_signal,
    tokens_from_user_day,
    user_login_from_row,
)


def _parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def parse_copilot_seat(seat: dict[str, Any], *, fallback_at: datetime) -> UsageRecord | None:
    assignee = seat.get("assignee") if isinstance(seat.get("assignee"), dict) else {}
    login = assignee.get("login")
    if not isinstance(login, str) or not login.strip():
        return None

    login = login.strip()
    occurred_at = (
        _parse_iso_datetime(seat.get("last_activity_at"))
        or _parse_iso_datetime(seat.get("updated_at"))
        or _parse_iso_datetime(seat.get("created_at"))
        or fallback_at
    )
    plan_type = seat.get("plan_type")
    editor = seat.get("last_activity_editor")
    model = str(editor or plan_type or "copilot-seat")

    day_key = occurred_at.astimezone(UTC).strftime("%Y-%m-%d")
    vendor_event_id = f"copilot-seat-{login}-{day_key}"

    return UsageRecord(
        vendor_event_id=vendor_event_id,
        model=model,
        occurred_at=occurred_at,
        input_tokens=1 if seat.get("last_activity_at") else 0,
        output_tokens=0,
        estimated_cost=Decimal("0"),
        user_email=login,
        user_name=login,
    )


def parse_copilot_user_day(row: dict[str, Any]) -> UsageRecord | None:
    login = user_login_from_row(row)
    if login is None:
        return None

    day = row.get("day") or row.get("report_day")
    if isinstance(day, str) and day.strip():
        try:
            occurred_at = datetime.fromisoformat(day.strip()).replace(tzinfo=UTC)
        except ValueError:
            occurred_at = datetime.now(UTC)
    else:
        occurred_at = datetime.now(UTC)

    input_tokens, output_tokens, _rule = tokens_from_user_day(row)
    if not has_usage_signal(row):
        return None

    day_key = occurred_at.strftime("%Y-%m-%d")
    user_id = row.get("user_id", login)
    vendor_event_id = f"copilot-user-{user_id}-{day_key}"

    features = feature_flags_from_row(row)
    model = "+".join(features) if features else "copilot"

    return UsageRecord(
        vendor_event_id=vendor_event_id,
        model=model,
        occurred_at=occurred_at,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=Decimal("0"),
        user_email=login,
        user_name=login,
    )


def parse_copilot_seat_members(seats: list[dict[str, Any]]) -> list[ProviderMember]:
    members: list[ProviderMember] = []
    seen: set[str] = set()
    for seat in seats:
        assignee = seat.get("assignee") if isinstance(seat.get("assignee"), dict) else {}
        login = assignee.get("login")
        if not isinstance(login, str) or not login.strip():
            continue
        login = login.strip()
        key = login.lower()
        if key in seen:
            continue
        seen.add(key)
        members.append(ProviderMember(email=login, name=login))
    members.sort(key=lambda row: row.email.lower())
    return members


def seat_to_synthetic_user_day(seat: dict[str, Any], *, fallback_day: str) -> dict[str, Any]:
    """Build a user-metrics-shaped row from seat API data when metrics NDJSON is unavailable."""
    assignee = seat.get("assignee") if isinstance(seat.get("assignee"), dict) else {}
    login = assignee.get("login")
    activity_at = seat.get("last_activity_at")
    day = fallback_day
    if isinstance(activity_at, str) and "T" in activity_at:
        day = activity_at.split("T", 1)[0]
    return {
        "user_login": login,
        "day": day,
        "used_chat": bool(activity_at),
        "loc_added_sum": 1 if activity_at else 0,
        "code_generation_activity_count": 1 if activity_at else 0,
        "_synthetic_from_seat": True,
        "_seat_plan_type": seat.get("plan_type"),
        "_seat_last_activity_editor": seat.get("last_activity_editor"),
    }
