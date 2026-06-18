"""Map vendor JSON records to canonical usage fields."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_TEMPLATE = re.compile(r"\{([a-zA-Z0-9_.]+)\}")


def extract_dot_path(record: Any, path: str) -> Any:
    if not path or path in {"$", "."}:
        return record
    normalized = path.removeprefix("$.").removeprefix("$")
    current = record
    for part in normalized.split("."):
        if part == "":
            continue
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def resolve_field_value(record: Any, spec: str) -> Any:
    spec = spec.strip()
    if not spec:
        return None

    if spec.startswith("$."):
        return extract_dot_path(record, spec)

    if _TEMPLATE.search(spec):
        def replacer(match: re.Match[str]) -> str:
            value = extract_dot_path(record, match.group(1))
            return "" if value is None else str(value)

        return _TEMPLATE.sub(replacer, spec)

    if spec.isdigit() or (spec.startswith("-") and spec[1:].isdigit()):
        return int(spec)

    try:
        return Decimal(spec)
    except InvalidOperation:
        pass

    value = extract_dot_path(record, spec)
    if value is not None:
        return value
    return spec


def parse_occurred_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if value is None:
        return datetime.now(UTC)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.now(UTC)


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except ValueError:
        return default


def parse_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return default


def extract_records(payload: Any, records_path: str | None, response_type: str) -> list[Any]:
    if response_type == "json_array" and isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        if records_path:
            found = extract_dot_path(payload, records_path)
            if isinstance(found, list):
                return found
            if found is not None:
                return [found]
        if response_type == "json_array":
            for key in ("data", "items", "results", "records"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        return [payload]

    if isinstance(payload, list):
        return payload
    return []


def map_record(record: Any, fields: dict[str, str]) -> dict[str, Any]:
    vendor_event_id = resolve_field_value(record, fields.get("vendor_event_id", ""))
    occurred_raw = resolve_field_value(record, fields.get("occurred_at", ""))
    input_tokens = resolve_field_value(record, fields.get("input_tokens", "0"))
    output_tokens = resolve_field_value(record, fields.get("output_tokens", "0"))
    estimated_cost = resolve_field_value(record, fields.get("estimated_cost", "0"))
    model = resolve_field_value(record, fields.get("model", "default"))
    user_email_raw = resolve_field_value(record, fields.get("user_email", ""))
    user_name_raw = resolve_field_value(record, fields.get("user_name", ""))

    event_id = str(vendor_event_id).strip() if vendor_event_id is not None else ""
    if not event_id:
        event_id = f"event-{parse_occurred_at(occurred_raw).isoformat()}"

    user_email = str(user_email_raw).strip() if user_email_raw not in (None, "") else None
    user_name = str(user_name_raw).strip() if user_name_raw not in (None, "") else None

    return {
        "vendor_event_id": event_id,
        "occurred_at": parse_occurred_at(occurred_raw),
        "input_tokens": parse_int(input_tokens),
        "output_tokens": parse_int(output_tokens),
        "estimated_cost": parse_decimal(estimated_cost),
        "model": str(model) if model is not None else "default",
        "user_email": user_email,
        "user_name": user_name,
    }
