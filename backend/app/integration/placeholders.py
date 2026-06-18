"""Resolve template placeholders in integration URLs and query values."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def format_iso_z(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%dT%H:%M:%SZ")


def format_date(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d")


def organization_id_from_config(config: dict[str, Any] | None) -> str:
    raw = (config or {}).get("organization_id")
    if raw is None:
        return ""
    return str(raw).strip()


def build_context(
    *,
    api_endpoint: str | None,
    since: datetime,
    until: datetime,
    pricing_config: dict[str, Any] | None = None,
) -> dict[str, str]:
    endpoint = (api_endpoint or "").strip()
    org_id = organization_id_from_config(pricing_config)
    return {
        "api_endpoint": endpoint,
        "organization_id": org_id,
        "since_iso": format_iso_z(since),
        "until_iso": format_iso_z(until),
        "since_date": format_date(since),
        "until_date": format_date(until),
    }


def apply_placeholders(template: str, context: dict[str, str]) -> str:
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", value)
    return result


def apply_placeholders_to_mapping(
    mapping: dict[str, Any] | None,
    context: dict[str, str],
) -> dict[str, str]:
    if not mapping:
        return {}
    resolved: dict[str, str] = {}
    for key, raw in mapping.items():
        if raw is None:
            continue
        resolved[str(key)] = apply_placeholders(str(raw), context)
    return resolved
