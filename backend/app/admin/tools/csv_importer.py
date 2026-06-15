"""Parse tool usage CSV exports into token/cost/date metrics."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any


class CsvImportParseError(Exception):
    """CSV could not be parsed into usage metrics."""


TOKEN_HEADERS = {
    "tokens",
    "token",
    "token_count",
    "token_used",
    "tokens_used",
    "total_tokens",
    "requests",
    "usage",
}
# Cursor / vendor export columns that count as usage units (summed when no token column).
CURSOR_USAGE_HEADERS = {
    "subscription_included_reqs",
    "usage_based_reqs",
    "api_key_reqs",
    "composer_requests",
    "chat_requests",
    "agent_requests",
}
# Prefer these cost columns over generic "price" (often text like "Included" in Cursor exports).
COST_HEADERS_PREFERRED = {
    "cost",
    "total_cost",
    "amount",
    "spend",
    "total_cost_usd",
    "estimated_cost",
}
COST_HEADERS_FALLBACK = {
    "price",
    "total_price",
}
COST_HEADERS = COST_HEADERS_PREFERRED | COST_HEADERS_FALLBACK
DATE_HEADERS = {"date", "day", "period", "timestamp", "usage_date"}
DATE_FROM_HEADERS = {"date_from", "start_date", "period_start", "from", "start"}
DATE_TO_HEADERS = {"date_to", "end_date", "period_end", "to", "end"}


@dataclass(frozen=True)
class CsvColumnMapping:
    token_column: str | None = None
    cost_column: str | None = None
    date_column: str | None = None
    date_from_column: str | None = None
    date_to_column: str | None = None


@dataclass(frozen=True)
class CsvImportResult:
    token_count: int
    cost_total: float
    date_from: str | None
    date_to: str | None
    daily_usage: list[dict[str, Any]]
    row_count: int


@dataclass(frozen=True)
class CsvInspectResult:
    headers: list[str]
    row_count: int
    suggested_mapping: CsvColumnMapping
    format_hint: str


def _normalize_header(value: str) -> str:
    return re.sub(r"[\s\-]+", "_", value.strip().lower())


_NON_NUMERIC_COST_TOKENS = frozenset(
    {
        "included",
        "free",
        "n/a",
        "na",
        "none",
        "null",
        "-",
        "--",
        "included in plan",
        "subscription",
    }
)


def _parse_cost(value: str | None) -> float:
    """Parse cost/price cells; Cursor exports often use text like 'Included'."""
    if value is None:
        return 0.0
    raw = value.strip()
    if not raw:
        return 0.0

    lowered = raw.lower().strip("$").strip()
    if lowered in _NON_NUMERIC_COST_TOKENS or "included" in lowered:
        return 0.0

    cleaned = raw.replace(",", "").replace("$", "").strip()
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if match:
        return round(float(match.group()), 2)
    return 0.0


def _parse_number(value: str | None, *, strict: bool = False) -> float:
    if value is None:
        return 0.0
    cleaned = value.strip().replace(",", "").replace("$", "")
    if not cleaned:
        return 0.0

    lowered = cleaned.lower()
    if lowered in _NON_NUMERIC_COST_TOKENS:
        return 0.0

    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if match:
        return float(match.group())

    if strict:
        raise CsvImportParseError(f"Invalid numeric value: {value!r}")
    return 0.0


def _parse_int(value: str | None) -> int:
    return int(round(_parse_number(value, strict=False)))


def _is_usage_header(header: str) -> bool:
    if header in CURSOR_USAGE_HEADERS:
        return True
    return header.endswith("_reqs") or header.endswith("_requests")


def _usage_keys(normalized_headers: list[str]) -> list[str]:
    return [header for header in normalized_headers if _is_usage_header(header)]


def _find_cost_column(headers: list[str]) -> int | None:
    preferred = _find_column(headers, COST_HEADERS_PREFERRED)
    if preferred is not None:
        return preferred
    return _find_column(headers, COST_HEADERS_FALLBACK)


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise CsvImportParseError(f"Unrecognized date format: {value!r}") from exc


def _read_csv_table(content: bytes) -> tuple[list[str], dict[str, str], list[dict[str, str]]]:
    if not content.strip():
        raise CsvImportParseError("CSV file is empty.")

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CsvImportParseError("CSV must be UTF-8 encoded.") from exc

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise CsvImportParseError("CSV is missing a header row.")

    original_headers = [field.strip() for field in reader.fieldnames if field and field.strip()]
    if not original_headers:
        raise CsvImportParseError("CSV is missing a header row.")

    normalized_field_map = {
        field: _normalize_header(field) for field in reader.fieldnames if field
    }
    rows: list[dict[str, str]] = []
    for raw_row in reader:
        if not any((value or "").strip() for value in raw_row.values()):
            continue
        rows.append(
            {
                normalized_field_map[key]: (value or "").strip()
                for key, value in raw_row.items()
                if key in normalized_field_map
            }
        )

    if not rows:
        raise CsvImportParseError("CSV contains no data rows.")

    return original_headers, normalized_field_map, rows


def _find_column(headers: list[str], aliases: set[str]) -> int | None:
    for index, header in enumerate(headers):
        if header in aliases:
            return index
    return None


def _original_for_normalized(
    original_headers: list[str],
    normalized_field_map: dict[str, str],
    normalized_key: str,
) -> str | None:
    for original, normalized in normalized_field_map.items():
        if normalized == normalized_key:
            return original.strip()
    return None


def suggest_column_mapping(
    original_headers: list[str],
    normalized_field_map: dict[str, str],
) -> CsvColumnMapping:
    normalized_headers = list(normalized_field_map.values())
    token_idx = _find_column(normalized_headers, TOKEN_HEADERS)
    cost_idx = _find_cost_column(normalized_headers)
    date_idx = _find_column(normalized_headers, DATE_HEADERS)
    date_from_idx = _find_column(normalized_headers, DATE_FROM_HEADERS)
    date_to_idx = _find_column(normalized_headers, DATE_TO_HEADERS)

    return CsvColumnMapping(
        token_column=(
            _original_for_normalized(
                original_headers, normalized_field_map, normalized_headers[token_idx]
            )
            if token_idx is not None
            else None
        ),
        cost_column=(
            _original_for_normalized(
                original_headers, normalized_field_map, normalized_headers[cost_idx]
            )
            if cost_idx is not None
            else None
        ),
        date_column=(
            _original_for_normalized(
                original_headers, normalized_field_map, normalized_headers[date_idx]
            )
            if date_idx is not None
            else None
        ),
        date_from_column=(
            _original_for_normalized(
                original_headers, normalized_field_map, normalized_headers[date_from_idx]
            )
            if date_from_idx is not None
            else None
        ),
        date_to_column=(
            _original_for_normalized(
                original_headers, normalized_field_map, normalized_headers[date_to_idx]
            )
            if date_to_idx is not None
            else None
        ),
    )


def inspect_tool_usage_csv(content: bytes) -> CsvInspectResult:
    """Return CSV headers and auto-detected column mapping suggestions."""
    original_headers, normalized_field_map, rows = _read_csv_table(content)
    suggested = suggest_column_mapping(original_headers, normalized_field_map)

    if suggested.date_column:
        format_hint = "daily"
    elif suggested.date_from_column or suggested.date_to_column:
        format_hint = "summary"
    else:
        format_hint = "daily"

    return CsvInspectResult(
        headers=original_headers,
        row_count=len(rows),
        suggested_mapping=suggested,
        format_hint=format_hint,
    )


def _resolve_normalized_key(
    column: str | None,
    normalized_field_map: dict[str, str],
    *,
    label: str,
    required: bool = False,
) -> str | None:
    if not column or not column.strip():
        if required:
            raise CsvImportParseError(f"Select a CSV column for {label}.")
        return None

    target = column.strip()
    target_norm = _normalize_header(target)
    for original, normalized in normalized_field_map.items():
        if original.strip() == target or normalized == target_norm:
            return normalized

    raise CsvImportParseError(f"Column {target!r} was not found in the CSV header row.")


def _row_usage_units(
    row: dict[str, str],
    *,
    token_key: str | None,
    usage_keys: list[str],
) -> int:
    if token_key:
        return _parse_int(row.get(token_key))
    return sum(_parse_int(row.get(key)) for key in usage_keys)


def _aggregate_daily(
    rows: list[dict[str, str]],
    *,
    date_key: str,
    token_key: str | None,
    cost_key: str | None,
    usage_keys: list[str] | None = None,
) -> CsvImportResult:
    daily_map: dict[str, dict[str, float | int]] = {}
    keys = usage_keys or []

    for row in rows:
        day = _parse_date(row.get(date_key))
        if day is None:
            continue

        tokens = _row_usage_units(row, token_key=token_key, usage_keys=keys)
        cost = _parse_cost(row.get(cost_key)) if cost_key is not None else 0.0

        key = day.isoformat()
        if key not in daily_map:
            daily_map[key] = {"tokens": 0, "cost": 0.0}
        daily_map[key]["tokens"] = int(daily_map[key]["tokens"]) + tokens
        daily_map[key]["cost"] = round(float(daily_map[key]["cost"]) + cost, 2)

    if not daily_map:
        raise CsvImportParseError(
            "No usage rows found. Check your date and token column selections."
        )

    daily_usage = [
        {"date": day, "tokens": int(values["tokens"]), "cost": float(values["cost"])}
        for day, values in sorted(daily_map.items())
    ]
    token_count = sum(item["tokens"] for item in daily_usage)
    cost_total = round(sum(item["cost"] for item in daily_usage), 2)

    return CsvImportResult(
        token_count=token_count,
        cost_total=cost_total,
        date_from=daily_usage[0]["date"],
        date_to=daily_usage[-1]["date"],
        daily_usage=daily_usage,
        row_count=len(rows),
    )


def parse_tool_usage_csv(
    content: bytes,
    mapping: CsvColumnMapping | None = None,
) -> CsvImportResult:
    """Extract tokens, cost, and date range from a vendor usage CSV."""
    original_headers, normalized_field_map, rows = _read_csv_table(content)
    normalized_headers = list(normalized_field_map.values())

    if mapping is not None and mapping.token_column:
        token_key = _resolve_normalized_key(
            mapping.token_column, normalized_field_map, label="tokens", required=True
        )
        cost_key = _resolve_normalized_key(
            mapping.cost_column, normalized_field_map, label="cost", required=False
        )
        date_key = _resolve_normalized_key(
            mapping.date_column, normalized_field_map, label="date", required=False
        )
        date_from_key = _resolve_normalized_key(
            mapping.date_from_column,
            normalized_field_map,
            label="date from",
            required=False,
        )
        date_to_key = _resolve_normalized_key(
            mapping.date_to_column,
            normalized_field_map,
            label="date to",
            required=False,
        )

        if date_key:
            return _aggregate_daily(
                rows,
                date_key=date_key,
                token_key=token_key,
                cost_key=cost_key,
            )

        if date_from_key or date_to_key:
            first = rows[0]
            token_count = _parse_int(first.get(token_key))
            cost_total = _parse_cost(first.get(cost_key)) if cost_key else 0.0
            date_from = (
                _parse_date(first.get(date_from_key)).isoformat()
                if date_from_key and _parse_date(first.get(date_from_key))
                else None
            )
            date_to = (
                _parse_date(first.get(date_to_key)).isoformat()
                if date_to_key and _parse_date(first.get(date_to_key))
                else None
            )
            if not date_from and not date_to:
                raise CsvImportParseError(
                    "Select date-from and/or date-to columns for summary CSV format."
                )
            date_from = date_from or date_to
            date_to = date_to or date_from
            daily_usage = [
                {"date": date_from, "tokens": token_count, "cost": cost_total}
            ]
            return CsvImportResult(
                token_count=token_count,
                cost_total=cost_total,
                date_from=date_from,
                date_to=date_to,
                daily_usage=daily_usage,
                row_count=len(rows),
            )

        raise CsvImportParseError(
            "Select a date column (daily rows) or date-from/date-to columns (summary)."
        )

    token_idx = _find_column(normalized_headers, TOKEN_HEADERS)
    cost_idx = _find_cost_column(normalized_headers)
    date_idx = _find_column(normalized_headers, DATE_HEADERS)
    date_from_idx = _find_column(normalized_headers, DATE_FROM_HEADERS)
    date_to_idx = _find_column(normalized_headers, DATE_TO_HEADERS)
    usage_keys = _usage_keys(normalized_headers)

    if token_idx is None and not usage_keys:
        raise CsvImportParseError(
            "Could not detect a token column. Select which header contains token usage."
        )

    if date_idx is not None:
        return _aggregate_daily(
            rows,
            date_key=normalized_headers[date_idx],
            token_key=normalized_headers[token_idx] if token_idx is not None else None,
            cost_key=normalized_headers[cost_idx] if cost_idx is not None else None,
            usage_keys=usage_keys if token_idx is None else None,
        )

    first = rows[0]
    if token_idx is not None:
        token_count = _parse_int(first[normalized_headers[token_idx]])
    else:
        token_count = sum(_parse_int(first.get(key)) for key in usage_keys)
    cost_total = (
        _parse_cost(first[normalized_headers[cost_idx]])
        if cost_idx is not None
        else 0.0
    )

    date_from: str | None = None
    date_to: str | None = None
    if date_from_idx is not None:
        parsed = _parse_date(first.get(normalized_headers[date_from_idx]))
        date_from = parsed.isoformat() if parsed else None
    if date_to_idx is not None:
        parsed = _parse_date(first.get(normalized_headers[date_to_idx]))
        date_to = parsed.isoformat() if parsed else None

    if not date_from and not date_to:
        today = datetime.now(tz=UTC).date().isoformat()
        date_from = today
        date_to = today
    else:
        date_from = date_from or date_to
        date_to = date_to or date_from

    daily_usage = [{"date": date_from, "tokens": token_count, "cost": cost_total}]

    return CsvImportResult(
        token_count=token_count,
        cost_total=cost_total,
        date_from=date_from,
        date_to=date_to,
        daily_usage=daily_usage,
        row_count=len(rows),
    )
