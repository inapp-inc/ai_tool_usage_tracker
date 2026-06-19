"""Parse GitHub Copilot billing seats and usage metrics into UsageRecords."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.collector.adapters.base import ProviderMember, UsageRecord
from app.integration.numbers import parse_compact_int


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


def _int_field(row: dict[str, Any], key: str) -> int:
    return parse_compact_int(row.get(key), default=0)


def _tokens_from_user_day(row: dict[str, Any]) -> tuple[int, int]:
    input_tokens = 0
    output_tokens = 0

    cli = row.get("totals_by_cli")
    if isinstance(cli, dict):
        token_usage = cli.get("token_usage")
        if isinstance(token_usage, dict):
            input_tokens += _int_field(token_usage, "prompt_tokens_sum")
            output_tokens += _int_field(token_usage, "output_tokens_sum")

    if input_tokens + output_tokens == 0:
        input_tokens = (
            _int_field(row, "loc_added_sum")
            + _int_field(row, "loc_deleted_sum")
            + _int_field(row, "code_generation_activity_count")
            + _int_field(row, "code_acceptance_activity_count")
            + _int_field(row, "user_initiated_interaction_count")
        )

    return max(input_tokens, 0), max(output_tokens, 0)


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
    login = row.get("user_login")
    if not isinstance(login, str) or not login.strip():
        return None
    login = login.strip()

    day = row.get("day")
    if isinstance(day, str) and day.strip():
        try:
            occurred_at = datetime.fromisoformat(day.strip()).replace(tzinfo=UTC)
        except ValueError:
            occurred_at = datetime.now(UTC)
    else:
        occurred_at = datetime.now(UTC)

    input_tokens, output_tokens = _tokens_from_user_day(row)
    if input_tokens + output_tokens <= 0 and not any(
        row.get(flag) for flag in ("used_chat", "used_cli", "used_agent")
    ):
        return None

    day_key = occurred_at.strftime("%Y-%m-%d")
    user_id = row.get("user_id", login)
    vendor_event_id = f"copilot-user-{user_id}-{day_key}"

    features: list[str] = []
    if row.get("used_chat"):
        features.append("chat")
    if row.get("used_cli"):
        features.append("cli")
    if row.get("used_agent"):
        features.append("agent")
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
