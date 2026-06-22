"""Map GitHub Copilot API payloads to productivity domain rows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from app.collector.adapters.copilot_metrics_fields import int_field
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


def _parse_report_date(row: dict[str, Any]) -> date | None:
    day = row.get("day") or row.get("report_day")
    if isinstance(day, str) and day.strip():
        try:
            return date.fromisoformat(day.strip()[:10])
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class CopilotUserUsageRow:
    report_date: date
    user_login: str
    user_email: str | None
    user_name: str | None
    feature: str
    editor: str
    language: str
    active_days: int
    chat_turns: int
    suggestions_count: int
    acceptances_count: int
    acceptance_rate: Decimal | None
    lines_suggested: int
    lines_accepted: int
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class CopilotSeatRow:
    user_login: str
    user_email: str | None
    seat_status: str
    assigned_at: datetime | None
    last_activity_at: datetime | None


@dataclass(frozen=True)
class CopilotOrgSnapshot:
    organization_id: str
    organization_name: str | None
    subscription_type: str | None
    total_seats: int
    assigned_seats: int
    active_users: int
    report_date: date | None


def parse_user_metrics_row(row: dict[str, Any]) -> CopilotUserUsageRow | None:
    from app.normalization.productivity import map_copilot_productivity

    normalized = map_copilot_productivity(row, report_date=_parse_report_date(row))
    if normalized is None:
        return None
    return CopilotUserUsageRow(
        report_date=normalized.report_date or _parse_report_date(row) or date.today(),
        user_login=normalized.user_email or "",
        user_email=normalized.user_email,
        user_name=normalized.user_email,
        feature=normalized.feature or "all",
        editor=normalized.editor or "all",
        language=normalized.language or "all",
        active_days=normalized.active_days,
        chat_turns=normalized.chat_turns,
        suggestions_count=normalized.suggestions_count,
        acceptances_count=normalized.acceptances_count,
        acceptance_rate=normalized.acceptance_rate,
        lines_suggested=normalized.lines_suggested,
        lines_accepted=normalized.lines_accepted,
        raw_payload=normalized.raw_payload,
    )


def parse_seat_row(seat: dict[str, Any]) -> CopilotSeatRow | None:
    assignee = seat.get("assignee") if isinstance(seat.get("assignee"), dict) else {}
    login = assignee.get("login")
    if not isinstance(login, str) or not login.strip():
        return None
    login = login.strip()
    pending = seat.get("pending_cancellation_date")
    status = "pending_cancel" if pending else "assigned"
    return CopilotSeatRow(
        user_login=login,
        user_email=login,
        seat_status=status,
        assigned_at=_parse_iso_datetime(seat.get("created_at")),
        last_activity_at=_parse_iso_datetime(seat.get("last_activity_at")),
    )


def parse_org_metrics_row(row: dict[str, Any], *, github_org_id: str) -> CopilotOrgSnapshot:
    report_date = _parse_report_date(row)
    active_users = parse_compact_int(row.get("total_active_users"), default=0)
    if active_users == 0:
        active_users = parse_compact_int(row.get("active_users"), default=0)
    return CopilotOrgSnapshot(
        organization_id=github_org_id,
        organization_name=row.get("organization_name") if isinstance(row.get("organization_name"), str) else None,
        subscription_type=None,
        total_seats=parse_compact_int(row.get("total_seats"), default=0),
        assigned_seats=parse_compact_int(row.get("assigned_seats"), default=0),
        active_users=active_users,
        report_date=report_date,
    )


def top_languages_from_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[tuple[str, int]]:
    totals: dict[str, int] = {}
    for row in rows:
        payload = row.get("totals_by_language_feature")
        if not isinstance(payload, list):
            continue
        for item in payload:
            if not isinstance(item, dict):
                continue
            language = item.get("language") or item.get("name")
            if not isinstance(language, str):
                continue
            count = int_field(item, "code_generation_activity_count")
            totals[language] = totals.get(language, 0) + count
    return sorted(totals.items(), key=lambda pair: pair[1], reverse=True)[:limit]


def top_editors_from_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[tuple[str, int]]:
    totals: dict[str, int] = {}
    for row in rows:
        payload = row.get("totals_by_ide")
        if not isinstance(payload, list):
            continue
        for item in payload:
            if not isinstance(item, dict):
                continue
            editor = item.get("editor") or item.get("ide")
            if not isinstance(editor, str):
                continue
            count = int_field(item, "user_initiated_interaction_count") + int_field(
                item, "code_generation_activity_count"
            )
            totals[editor] = totals.get(editor, 0) + count
    return sorted(totals.items(), key=lambda pair: pair[1], reverse=True)[:limit]
