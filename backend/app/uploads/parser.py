"""Parse vendor CSV/JSON uploads — raw rows kept separate from mapped usage."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, TypedDict
from uuid import UUID


@dataclass
class ToolLookup:
    id: UUID
    name: str
    vendor: str


@dataclass
class ParsedUploadRow:
    row_number: int
    raw_payload: dict[str, Any]
    mapped_payload: dict[str, Any]
    user_email: str | None = None
    matched_user_id: UUID | None = None
    occurred_at: datetime | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    match_status: str = "matched"
    error_reason: str | None = None


@dataclass
class ParseResult:
    rows: list[ParsedUploadRow] = field(default_factory=list)
    error_message: str | None = None


class ColumnMapping(TypedDict, total=False):
    email: str | None
    cost: str | None
    model: str | None
    input_tokens: str | None
    output_tokens: str | None
    tokens: str | None
    timestamp: str | None
    tool: str | None


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "email": ("email", "user_email", "user", "member_email", "username"),
    "model": ("model", "model_name", "model_id"),
    "input_tokens": ("input_tokens", "prompt_tokens", "input"),
    "output_tokens": ("output_tokens", "completion_tokens", "output"),
    "tokens": ("tokens", "total_tokens", "token_count"),
    "cost": ("cost", "cost_usd", "amount", "spend", "price"),
    "timestamp": ("timestamp", "occurred_at", "date", "created_at", "time"),
    "tool": ("tool", "tool_name", "vendor", "provider", "service"),
}

MAPPING_FIELD_LABELS: dict[str, str] = {
    "email": "Email",
    "cost": "Cost",
    "model": "Model",
    "input_tokens": "Input tokens",
    "output_tokens": "Output tokens",
    "tokens": "Total tokens",
    "timestamp": "Timestamp",
    "tool": "Tool / vendor",
}


def _normalize_key(key: str) -> str:
    return re.sub(r"[\s_-]+", "_", key.strip().lower())


def _pick_value(raw: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    normalized = {_normalize_key(k): v for k, v in raw.items()}
    for alias in aliases:
        value = normalized.get(_normalize_key(alias))
        if value is not None and str(value).strip() != "":
            return value
    return None


def _pick_mapped_value(
    raw: dict[str, Any],
    column_mapping: ColumnMapping | None,
    field: str,
    aliases: tuple[str, ...],
) -> Any:
    if column_mapping:
        header = column_mapping.get(field)
        if header:
            if header in raw:
                value = raw[header]
            else:
                normalized = {_normalize_key(k): v for k, v in raw.items()}
                value = normalized.get(_normalize_key(header))
            if value is not None and str(value).strip() != "":
                return value
    return _pick_value(raw, aliases)


def extract_csv_headers(content: str) -> tuple[list[str], str | None]:
    try:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return [], "CSV file is empty or missing a header row."
        headers = [name for name in reader.fieldnames if name is not None]
        if not headers:
            return [], "CSV file is empty or missing a header row."
        return headers, None
    except csv.Error as exc:
        return [], f"CSV parse error: {exc}"


def extract_csv_sample_row(content: str) -> dict[str, Any] | None:
    try:
        reader = csv.DictReader(io.StringIO(content))
        for raw in reader:
            return {key: value for key, value in raw.items() if key is not None}
    except csv.Error:
        return None
    return None


def suggest_column_mapping(headers: list[str]) -> ColumnMapping:
    normalized_headers = {_normalize_key(header): header for header in headers}
    suggested: ColumnMapping = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            match = normalized_headers.get(_normalize_key(alias))
            if match:
                suggested[field] = match
                break
    return suggested


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(float(str(value).strip().replace(",", "")))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _match_tool(
    raw: dict[str, Any],
    tools: list[ToolLookup],
    column_mapping: ColumnMapping | None = None,
) -> ToolLookup | None:
    tool_hint = _pick_mapped_value(
        raw,
        column_mapping,
        "tool",
        FIELD_ALIASES["tool"],
    )
    if tool_hint is None:
        return tools[0] if len(tools) == 1 else None

    hint = str(tool_hint).strip().lower()
    for tool in tools:
        if tool.name.lower() == hint or tool.vendor.lower() == hint:
            return tool
    for tool in tools:
        if hint in tool.name.lower() or hint in tool.vendor.lower():
            return tool
    return None


def map_row_to_usage(
    *,
    row_number: int,
    raw_payload: dict[str, Any],
    tools: list[ToolLookup],
    users_by_email: dict[str, UUID],
    column_mapping: ColumnMapping | None = None,
) -> ParsedUploadRow:
    email_raw = _pick_mapped_value(
        raw_payload,
        column_mapping,
        "email",
        FIELD_ALIASES["email"],
    )
    email = str(email_raw).strip().lower() if email_raw else None

    model = _pick_mapped_value(
        raw_payload,
        column_mapping,
        "model",
        FIELD_ALIASES["model"],
    )
    model_str = str(model).strip() if model else None

    input_tokens = _parse_int(
        _pick_mapped_value(
            raw_payload,
            column_mapping,
            "input_tokens",
            FIELD_ALIASES["input_tokens"],
        )
    )
    output_tokens = _parse_int(
        _pick_mapped_value(
            raw_payload,
            column_mapping,
            "output_tokens",
            FIELD_ALIASES["output_tokens"],
        )
    )
    total_tokens = _parse_int(
        _pick_mapped_value(
            raw_payload,
            column_mapping,
            "tokens",
            FIELD_ALIASES["tokens"],
        )
    )

    if input_tokens is None and output_tokens is None and total_tokens is not None:
        input_tokens = total_tokens
        output_tokens = 0
    input_tokens = input_tokens or 0
    output_tokens = output_tokens or 0

    cost = _parse_decimal(
        _pick_mapped_value(
            raw_payload,
            column_mapping,
            "cost",
            FIELD_ALIASES["cost"],
        )
    )
    occurred_at = _parse_datetime(
        _pick_mapped_value(
            raw_payload,
            column_mapping,
            "timestamp",
            FIELD_ALIASES["timestamp"],
        )
    )

    tool = _match_tool(raw_payload, tools, column_mapping)
    matched_user_id = users_by_email.get(email) if email else None

    mapped_payload: dict[str, Any] = {
        "tool_id": str(tool.id) if tool else None,
        "tool_name": tool.name if tool else None,
        "vendor": tool.vendor if tool else None,
        "email": email,
        "model": model_str,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost": float(cost) if cost is not None else 0.0,
        "occurred_at": occurred_at.isoformat() if occurred_at else None,
    }

    errors: list[str] = []
    if email and matched_user_id is None:
        errors.append(f"Unknown user email: {email}")
    if input_tokens + output_tokens <= 0:
        errors.append("Token count must be greater than zero")
    if tool is None and tools:
        errors.append("Could not match row to a configured AI tool")

    match_status = "matched" if not errors else "unmatched"
    error_reason = "; ".join(errors) if errors else None

    return ParsedUploadRow(
        row_number=row_number,
        raw_payload=raw_payload,
        mapped_payload=mapped_payload,
        user_email=email,
        matched_user_id=matched_user_id,
        occurred_at=occurred_at,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        match_status=match_status,
        error_reason=error_reason,
    )


def parse_csv_content(
    content: str,
    *,
    tools: list[ToolLookup],
    users_by_email: dict[str, UUID],
    column_mapping: ColumnMapping | None = None,
) -> ParseResult:
    try:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return ParseResult(error_message="CSV file is empty or missing a header row.")

        rows: list[ParsedUploadRow] = []
        for index, raw in enumerate(reader, start=1):
            raw_payload = {key: value for key, value in raw.items() if key is not None}
            rows.append(
                map_row_to_usage(
                    row_number=index,
                    raw_payload=raw_payload,
                    tools=tools,
                    users_by_email=users_by_email,
                    column_mapping=column_mapping,
                )
            )
        if not rows:
            return ParseResult(error_message="CSV file contains no data rows.")
        return ParseResult(rows=rows)
    except csv.Error as exc:
        return ParseResult(error_message=f"CSV parse error: {exc}")


def parse_json_content(
    content: str,
    *,
    tools: list[ToolLookup],
    users_by_email: dict[str, UUID],
) -> ParseResult:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return ParseResult(error_message=f"JSON parse error: {exc.msg}")

    if isinstance(payload, dict) and "rows" in payload:
        items = payload["rows"]
    elif isinstance(payload, list):
        items = payload
    else:
        return ParseResult(error_message="JSON must be an array of usage rows.")

    rows: list[ParsedUploadRow] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            rows.append(
                ParsedUploadRow(
                    row_number=index,
                    raw_payload={"value": item},
                    mapped_payload={},
                    match_status="unmatched",
                    error_reason="Row must be a JSON object",
                )
            )
            continue
        rows.append(
            map_row_to_usage(
                row_number=index,
                raw_payload=item,
                tools=tools,
                users_by_email=users_by_email,
            )
        )

    if not rows:
        return ParseResult(error_message="JSON file contains no rows.")
    return ParseResult(rows=rows)


def parse_upload_content(
    content: str,
    *,
    filename: str,
    tools: list[ToolLookup],
    users_by_email: dict[str, UUID],
    column_mapping: ColumnMapping | None = None,
) -> ParseResult:
    if filename.lower().endswith(".json"):
        return parse_json_content(content, tools=tools, users_by_email=users_by_email)
    return parse_csv_content(
        content,
        tools=tools,
        users_by_email=users_by_email,
        column_mapping=column_mapping,
    )
