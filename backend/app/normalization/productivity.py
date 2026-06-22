"""Productivity-based vendor API → NormalizedProductivityEvent."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app.normalization.cost_engine import apply_productivity_seat_cost
from app.normalization.schemas import NormalizedProductivityEvent


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _acceptance_rate(suggestions: int, acceptances: int) -> Decimal | None:
    if suggestions <= 0:
        return None
    return Decimal(acceptances) / Decimal(suggestions) * Decimal("100")


def _parse_date(value: object) -> date | None:
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def map_copilot_productivity(
    row: dict[str, Any],
    *,
    report_date: date | None = None,
    page: int | None = None,
) -> NormalizedProductivityEvent | None:
    from app.collector.adapters.copilot_metrics_fields import user_login_from_row

    user_login = row.get("user_login") or row.get("userLogin") or user_login_from_row(row)
    if not isinstance(user_login, str) or not user_login.strip():
        return None

    day = report_date or _parse_date(row.get("day") or row.get("report_date"))
    feature = str(row.get("feature") or ("chat" if row.get("used_chat") else "all"))
    editor = str(row.get("editor") or row.get("last_activity_editor") or "all")
    language = str(row.get("language") or "all")

    suggestions = _int(row.get("suggestions_count") or row.get("code_generation_activity_count"))
    acceptances = _int(row.get("acceptances_count") or row.get("code_acceptance_activity_count"))
    chat_turns = _int(row.get("chat_turns") or row.get("user_initiated_interaction_count"))
    active_days = _int(row.get("active_days")) or (1 if suggestions or acceptances or chat_turns else 0)

    if not any([suggestions, acceptances, chat_turns, active_days, row.get("used_chat"), row.get("used_cli"), row.get("used_agent")]):
        return None

    login = user_login.strip()
    day_key = day.isoformat() if day else "unknown"
    event = NormalizedProductivityEvent(
        source="GitHub Copilot",
        page=page,
        report_date=day,
        user_email=login,
        feature=feature,
        editor=editor,
        language=language,
        active_days=active_days,
        suggestions_count=suggestions,
        acceptances_count=acceptances,
        acceptance_rate=_acceptance_rate(suggestions, acceptances),
        chat_turns=chat_turns,
        lines_suggested=_int(row.get("lines_suggested") or row.get("loc_suggested_to_add_sum")),
        lines_accepted=_int(row.get("lines_accepted") or row.get("loc_added_sum")),
        vendor_event_id=f"copilot-{login}-{day_key}",
        raw_payload=row,
    )
    return event


def map_amazon_q_productivity(row: dict[str, Any], *, report_date: date | None = None) -> NormalizedProductivityEvent | None:
    user = row.get("user_email") or row.get("userEmail") or row.get("user_login")
    if not isinstance(user, str) or not user.strip():
        return None
    suggestions = _int(row.get("suggestions_count") or row.get("codeSuggestions"))
    acceptances = _int(row.get("acceptances_count") or row.get("acceptances"))
    chat_turns = _int(row.get("chat_turns") or row.get("chatSessions"))
    day = report_date or _parse_date(row.get("report_date") or row.get("day"))
    event = NormalizedProductivityEvent(
        source="Amazon Q Developer",
        report_date=day,
        user_email=user.strip(),
        feature=str(row.get("feature") or "code_assist"),
        editor=str(row.get("editor") or row.get("ide") or "all"),
        language=str(row.get("language") or "all"),
        active_days=_int(row.get("active_days")) or 1,
        suggestions_count=suggestions,
        acceptances_count=acceptances,
        acceptance_rate=_acceptance_rate(suggestions, acceptances),
        chat_turns=chat_turns,
        lines_suggested=_int(row.get("lines_suggested")),
        lines_accepted=_int(row.get("lines_accepted")),
        vendor_event_id=f"amazon-q-{user.strip()}-{day or 'unknown'}",
        raw_payload=row,
    )
    return event if suggestions or acceptances or chat_turns else None


def map_gemini_code_assist_productivity(
    row: dict[str, Any],
    *,
    report_date: date | None = None,
) -> NormalizedProductivityEvent | None:
    user = row.get("user_email") or row.get("userEmail")
    if not isinstance(user, str) or not user.strip():
        return None
    suggestions = _int(row.get("suggestions_count") or row.get("completions"))
    acceptances = _int(row.get("acceptances_count") or row.get("acceptances"))
    day = report_date or _parse_date(row.get("report_date"))
    event = NormalizedProductivityEvent(
        source="Gemini Code Assist",
        report_date=day,
        user_email=user.strip(),
        feature=str(row.get("feature") or "code_assist"),
        editor=str(row.get("editor") or "all"),
        language=str(row.get("language") or "all"),
        active_days=_int(row.get("active_days")) or 1,
        suggestions_count=suggestions,
        acceptances_count=acceptances,
        acceptance_rate=_acceptance_rate(suggestions, acceptances),
        chat_turns=_int(row.get("chat_turns")),
        lines_suggested=_int(row.get("lines_suggested")),
        lines_accepted=_int(row.get("lines_accepted")),
        vendor_event_id=f"gemini-code-assist-{user.strip()}-{day or 'unknown'}",
        raw_payload=row,
    )
    return event if suggestions or acceptances else None


def with_seat_cost(
    event: NormalizedProductivityEvent,
    *,
    monthly_package_cost: Decimal,
    assigned_seats: int,
) -> NormalizedProductivityEvent:
    return apply_productivity_seat_cost(
        event,
        monthly_package_cost=monthly_package_cost,
        assigned_seats=assigned_seats,
    )
