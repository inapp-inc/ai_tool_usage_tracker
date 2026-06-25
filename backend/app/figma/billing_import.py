"""Parse Figma usage/billing CSV exports."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.copilot.billing_period import report_period_bounds, resolve_billing_period

FIGMA_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "user_id": ("user_id", "userid", "user id"),
    "user_email": ("user_email", "useremail", "user email", "email"),
    "user_name": ("user_name", "username", "user name", "name"),
    "seat_type": ("seat_type", "seattype", "seat type"),
    "seat_credits_used": (
        "seat_credits_used",
        "seat credits used",
        "seat_credits",
        "seat credits",
    ),
    "paid_credits_used": (
        "paid_credits_used",
        "paid credits used",
        "paid_credits",
        "paid credits",
    ),
    "last_activity": ("last_activity", "last activity", "last_active", "last active"),
    "usage_period_start": (
        "usage_period_start",
        "usage period start",
        "period_start",
        "billing_period_start",
    ),
    "usage_period_end": (
        "usage_period_end",
        "usage period end",
        "period_end",
        "billing_period_end",
    ),
}

FIGMA_MAPPING_FIELD_LABELS: dict[str, str] = {
    "user_id": "User ID",
    "user_email": "User email",
    "user_name": "User name",
    "seat_type": "Seat type",
    "seat_credits_used": "Seat credits used",
    "paid_credits_used": "Paid credits used",
    "last_activity": "Last activity",
    "usage_period_start": "Usage period start",
    "usage_period_end": "Usage period end",
}


@dataclass
class FigmaBillingRow:
    row_number: int
    figma_user_id: str | None
    user_email: str | None
    user_name: str | None
    seat_type: str
    seat_credits_used: Decimal
    paid_credits_used: Decimal
    last_activity: datetime | None
    usage_period_start: date | None
    usage_period_end: date | None
    raw_payload: dict[str, Any]
    error_reason: str | None = None


@dataclass
class FigmaBillingAggregate:
    usage_period_start: date | None
    usage_period_end: date | None
    total_seat_cost: Decimal
    total_paid_cost: Decimal
    total_cost: Decimal
    full_seat_count: int
    view_seat_count: int
    user_count: int
    row_count: int


@dataclass
class FigmaParseResult:
    rows: list[FigmaBillingRow] = field(default_factory=list)
    aggregates: list[FigmaBillingAggregate] = field(default_factory=list)
    error_message: str | None = None


def _normalize_key(key: str) -> str:
    return re.sub(r"[\s_-]+", "_", key.strip().lower())


def _pick_mapped_value(
    raw: dict[str, Any],
    column_mapping: dict[str, str | None],
    field: str,
) -> Any:
    header = column_mapping.get(field)
    if header:
        if header in raw:
            value = raw[header]
        else:
            normalized = {_normalize_key(k): v for k, v in raw.items()}
            value = normalized.get(_normalize_key(header))
        if value is not None and str(value).strip() != "":
            return value
    aliases = FIGMA_FIELD_ALIASES.get(field, ())
    normalized = {_normalize_key(k): v for k, v in raw.items()}
    for alias in aliases:
        value = normalized.get(_normalize_key(alias))
        if value is not None and str(value).strip() != "":
            return value
    return None


def _decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text:
        return Decimal("0")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("0")


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ):
        try:
            parsed = datetime.strptime(normalized[:19], fmt[: len(normalized[:19])])
            return parsed
        except ValueError:
            continue
    parsed_date = _parse_date(text)
    if parsed_date is not None:
        return datetime.combine(parsed_date, datetime.min.time())
    return None


def _normalize_seat_type(value: str | None) -> str:
    text = (value or "full").strip().lower()
    if text in {"view", "viewer", "collab", "collaborator"}:
        return "view"
    return "full"


def suggest_figma_column_mapping(headers: list[str]) -> dict[str, str | None]:
    normalized_headers = {_normalize_key(header): header for header in headers}
    mapping: dict[str, str | None] = {}
    for field, aliases in FIGMA_FIELD_ALIASES.items():
        matched = None
        for alias in aliases:
            header = normalized_headers.get(_normalize_key(alias))
            if header:
                matched = header
                break
        mapping[field] = matched
    return mapping


def parse_figma_billing_csv(
    content: str,
    *,
    column_mapping: dict[str, str | None],
) -> FigmaParseResult:
    try:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return FigmaParseResult(error_message="CSV file is empty or missing a header row.")
    except csv.Error as exc:
        return FigmaParseResult(error_message=f"Invalid CSV: {exc}")

    if not any(column for column in column_mapping.values() if column):
        return FigmaParseResult(error_message="Map at least one CSV column before continuing.")

    rows: list[FigmaBillingRow] = []
    for index, raw in enumerate(reader, start=1):
        if not raw:
            continue
        user_email = str(_pick_mapped_value(raw, column_mapping, "user_email") or "").strip() or None
        user_id = str(_pick_mapped_value(raw, column_mapping, "user_id") or "").strip() or None
        if not user_email and not user_id:
            row = FigmaBillingRow(
                row_number=index,
                figma_user_id=None,
                user_email=None,
                user_name=None,
                seat_type="full",
                seat_credits_used=Decimal("0"),
                paid_credits_used=Decimal("0"),
                last_activity=None,
                usage_period_start=None,
                usage_period_end=None,
                raw_payload=dict(raw),
                error_reason="Missing user email or user ID",
            )
            rows.append(row)
            continue

        row = FigmaBillingRow(
            row_number=index,
            figma_user_id=user_id,
            user_email=user_email,
            user_name=str(_pick_mapped_value(raw, column_mapping, "user_name") or "").strip() or None,
            seat_type=_normalize_seat_type(
                str(_pick_mapped_value(raw, column_mapping, "seat_type") or "")
            ),
            seat_credits_used=_decimal(_pick_mapped_value(raw, column_mapping, "seat_credits_used")),
            paid_credits_used=_decimal(_pick_mapped_value(raw, column_mapping, "paid_credits_used")),
            last_activity=_parse_datetime(_pick_mapped_value(raw, column_mapping, "last_activity")),
            usage_period_start=_parse_date(
                _pick_mapped_value(raw, column_mapping, "usage_period_start")
            ),
            usage_period_end=_parse_date(_pick_mapped_value(raw, column_mapping, "usage_period_end")),
            raw_payload=dict(raw),
        )
        rows.append(row)

    valid_rows = [row for row in rows if row.error_reason is None]
    if not valid_rows:
        return FigmaParseResult(
            rows=rows,
            error_message="No valid Figma billing rows found. Check user and period columns.",
        )

    report_start, report_end = report_period_bounds(
        period_starts=[row.usage_period_start for row in valid_rows if row.usage_period_start],
        period_ends=[row.usage_period_end for row in valid_rows if row.usage_period_end],
    )
    for row in valid_rows:
        row.usage_period_start, row.usage_period_end = resolve_billing_period(
            row.usage_period_start,
            row.usage_period_end,
            report_start=report_start,
            report_end=report_end,
        )

    return FigmaParseResult(rows=rows, aggregates=[])


def aggregate_figma_billing_rows(
    rows: list[FigmaBillingRow],
    *,
    row_costs: list[tuple[Decimal, Decimal, Decimal]] | None = None,
) -> list[FigmaBillingAggregate]:
    """Group all user rows by usage period — one aggregate per period, not per user."""
    grouped: dict[tuple[date | None, date | None], list[int]] = {}
    for index, row in enumerate(rows):
        if row.error_reason is not None:
            continue
        key = (row.usage_period_start, row.usage_period_end)
        grouped.setdefault(key, []).append(index)

    aggregates: list[FigmaBillingAggregate] = []
    for (period_start, period_end), indexes in grouped.items():
        full_count = 0
        view_count = 0
        total_seat = Decimal("0")
        total_paid = Decimal("0")
        total = Decimal("0")
        for index in indexes:
            row = rows[index]
            if row.seat_type == "view":
                view_count += 1
            else:
                full_count += 1
            if row_costs and index < len(row_costs):
                seat_cost, paid_cost, row_total = row_costs[index]
            else:
                seat_cost = paid_cost = row_total = Decimal("0")
            total_seat += seat_cost
            total_paid += paid_cost
            total += row_total
        aggregates.append(
            FigmaBillingAggregate(
                usage_period_start=period_start,
                usage_period_end=period_end,
                total_seat_cost=total_seat,
                total_paid_cost=total_paid,
                total_cost=total,
                full_seat_count=full_count,
                view_seat_count=view_count,
                user_count=len(indexes),
                row_count=len(indexes),
            )
        )
    return aggregates


def summarize_figma_aggregates(aggregates: list[FigmaBillingAggregate]) -> dict[str, object]:
    total_seat = sum((row.total_seat_cost for row in aggregates), Decimal("0"))
    total_paid = sum((row.total_paid_cost for row in aggregates), Decimal("0"))
    total = sum((row.total_cost for row in aggregates), Decimal("0"))
    return {
        "total_seat_cost": float(total_seat),
        "total_paid_cost": float(total_paid),
        "total_cost": float(total),
        "full_seat_count": sum(row.full_seat_count for row in aggregates),
        "view_seat_count": sum(row.view_seat_count for row in aggregates),
        "user_count": sum(row.user_count for row in aggregates),
        "period_count": len(aggregates),
    }
