"""License-based vendor API → NormalizedLicenseEvent."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from app.normalization.cost_engine import apply_license_seat_cost
from app.normalization.schemas import NormalizedLicenseEvent


def _parse_date(value: object) -> date | None:
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def map_figma_activity(row: dict[str, Any], *, license_type: str | None = None) -> NormalizedLicenseEvent | None:
    user = row.get("user") or row.get("user_email") or row.get("email")
    if not isinstance(user, str) or not user.strip():
        return None
    last_active = _parse_date(row.get("last_active") or row.get("last_active_date"))
    team = row.get("team") or row.get("team_name")
    project = row.get("project") or row.get("project_name")
    file_name = row.get("file") or row.get("file_name")
    action = row.get("action") or row.get("activity_type")
    day_key = last_active.isoformat() if last_active else datetime.now(UTC).date().isoformat()

    return NormalizedLicenseEvent(
        source="Figma",
        user_email=user.strip(),
        team_name=str(team) if team else None,
        project_name=str(project) if project else None,
        file_name=str(file_name) if file_name else None,
        activity_type=str(action) if action else None,
        license_type=license_type,
        seat_assigned=True,
        seat_active=last_active is not None,
        last_active_date=last_active,
        vendor_event_id=f"figma-{user.strip()}-{file_name or 'seat'}-{day_key}",
        raw_payload=row,
    )


def map_figma_member_seat(
    *,
    user_email: str,
    user_name: str | None,
    license_type: str | None = None,
    occurred_at: datetime,
) -> NormalizedLicenseEvent:
    day = occurred_at.astimezone(UTC).date()
    return NormalizedLicenseEvent(
        source="Figma",
        activity_timestamp=occurred_at,
        user_email=user_email,
        user_name=user_name,
        license_type=license_type,
        seat_assigned=True,
        seat_active=True,
        last_active_date=day,
        activity_type="seat_assigned",
        vendor_event_id=f"figma-seat-{user_email}-{day.isoformat()}",
        raw_payload={"user": user_email, "name": user_name},
    )


def map_notion_license(row: dict[str, Any], *, license_type: str | None = None) -> NormalizedLicenseEvent | None:
    user = row.get("user_email") or row.get("user")
    if not isinstance(user, str) or not user.strip():
        return None
    last_active = _parse_date(row.get("last_active") or row.get("last_active_date"))
    return NormalizedLicenseEvent(
        source="Notion AI",
        user_email=user.strip(),
        activity_type=str(row.get("activity_type") or row.get("action") or "workspace_activity"),
        license_type=license_type,
        seat_assigned=True,
        seat_active=bool(last_active),
        last_active_date=last_active,
        vendor_event_id=f"notion-{user.strip()}-{last_active or 'unknown'}",
        raw_payload=row,
    )


def map_grammarly_license(row: dict[str, Any], *, license_type: str | None = None) -> NormalizedLicenseEvent | None:
    user = row.get("user_email") or row.get("user")
    if not isinstance(user, str) or not user.strip():
        return None
    last_active = _parse_date(row.get("last_active") or row.get("last_active_date"))
    return NormalizedLicenseEvent(
        source="Grammarly",
        user_email=user.strip(),
        activity_type=str(row.get("activity_type") or "writing_session"),
        license_type=license_type,
        seat_assigned=True,
        seat_active=bool(last_active),
        last_active_date=last_active,
        vendor_event_id=f"grammarly-{user.strip()}-{last_active or 'unknown'}",
        raw_payload=row,
    )


def map_canva_license(row: dict[str, Any], *, license_type: str | None = None) -> NormalizedLicenseEvent | None:
    user = row.get("user_email") or row.get("user")
    if not isinstance(user, str) or not user.strip():
        return None
    last_active = _parse_date(row.get("last_active") or row.get("last_active_date"))
    return NormalizedLicenseEvent(
        source="Canva",
        user_email=user.strip(),
        activity_type=str(row.get("activity_type") or "design_activity"),
        license_type=license_type,
        seat_assigned=True,
        seat_active=bool(last_active),
        last_active_date=last_active,
        vendor_event_id=f"canva-{user.strip()}-{last_active or 'unknown'}",
        raw_payload=row,
    )


def with_license_cost(
    event: NormalizedLicenseEvent,
    *,
    monthly_package_cost: Decimal,
    assigned_licenses: int,
) -> NormalizedLicenseEvent:
    return apply_license_seat_cost(
        event,
        monthly_package_cost=monthly_package_cost,
        assigned_licenses=assigned_licenses,
    )
