"""Parse GitHub Copilot billing CSV exports (SKU / unit_type rules)."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.copilot.billing_period import report_period_bounds, resolve_billing_period

KNOWN_SKUS = frozenset({"copilot_for_business", "copilot_ai_credit"})

AI_CREDITS_UNIT_TYPES = frozenset({"ai-credits", "ai credits", "ai_credits"})
USER_MONTHS_UNIT_TYPES = frozenset({"user-months", "user months", "user_months"})

COPILOT_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "sku": ("sku", "product_sku", "product"),
    "unit_type": ("unit_type", "unittype", "unit type"),
    "monthly_amount": ("monthly_amount", "monthlyamount", "amount", "monthly cost"),
    "net_amount": ("net_amount", "netamount", "net amount"),
    "gross_amount": ("gross_amount", "grossamount", "gross amount"),
    "quantity": ("quantity", "qty"),
    "billing_period_start": (
        "billing_period_start",
        "period_start",
        "start_date",
        "billing_start",
        "report_start_date",
        "report_start",
        "report period start",
    ),
    "billing_period_end": (
        "billing_period_end",
        "period_end",
        "end_date",
        "billing_end",
        "report_end_date",
        "report_end",
        "report period end",
    ),
    "usage_date": (
        "usage_date",
        "billing_date",
        "transaction_date",
        "date",
        "report_day",
        "report_date",
    ),
    "user_login": ("user_login", "login", "username", "user"),
}

COPILOT_MAPPING_FIELD_LABELS: dict[str, str] = {
    "sku": "SKU",
    "unit_type": "Unit type",
    "monthly_amount": "Monthly amount (USD)",
    "net_amount": "Net amount (USD)",
    "gross_amount": "Gross amount (USD)",
    "quantity": "Quantity",
    "billing_period_start": "Billing period start",
    "billing_period_end": "Billing period end",
    "usage_date": "Usage date",
    "user_login": "User login",
}


@dataclass
class CopilotBillingRow:
    row_number: int
    sku: str
    unit_type: str
    monthly_amount: Decimal
    net_amount: Decimal
    gross_amount: Decimal
    quantity: int
    billing_period_start: date | None
    billing_period_end: date | None
    usage_date: date | None
    user_login: str | None
    raw_payload: dict[str, Any]
    error_reason: str | None = None


@dataclass
class CopilotBillingAggregate:
    sku: str
    billing_period_start: date | None
    billing_period_end: date | None
    monthly_cost_limit: Decimal
    additional_cost: Decimal
    credits_cost: Decimal
    total_cost: Decimal
    seat_count: int | None
    row_count: int


@dataclass
class CopilotParseResult:
    rows: list[CopilotBillingRow] = field(default_factory=list)
    aggregates: list[CopilotBillingAggregate] = field(default_factory=list)
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
    aliases = COPILOT_FIELD_ALIASES.get(field, ())
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
            from datetime import datetime

            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _normalize_unit_type(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def suggest_copilot_column_mapping(headers: list[str]) -> dict[str, str | None]:
    normalized_headers = {_normalize_key(header): header for header in headers}
    mapping: dict[str, str | None] = {}
    for field, aliases in COPILOT_FIELD_ALIASES.items():
        matched = None
        for alias in aliases:
            header = normalized_headers.get(_normalize_key(alias))
            if header:
                matched = header
                break
        mapping[field] = matched
    return mapping


def parse_copilot_billing_csv(
    content: str,
    *,
    column_mapping: dict[str, str | None],
) -> CopilotParseResult:
    try:
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return CopilotParseResult(error_message="CSV file is empty or missing a header row.")
    except csv.Error as exc:
        return CopilotParseResult(error_message=f"Invalid CSV: {exc}")

    if not any(column for column in column_mapping.values() if column):
        return CopilotParseResult(error_message="Map at least one CSV column before continuing.")

    rows: list[CopilotBillingRow] = []
    for index, raw in enumerate(reader, start=1):
        if not raw:
            continue
        sku = str(_pick_mapped_value(raw, column_mapping, "sku") or "").strip().lower()
        unit_type = _normalize_unit_type(str(_pick_mapped_value(raw, column_mapping, "unit_type") or ""))
        usage_date = _parse_date(_pick_mapped_value(raw, column_mapping, "usage_date"))
        raw_period_start = _parse_date(_pick_mapped_value(raw, column_mapping, "billing_period_start"))
        raw_period_end = _parse_date(_pick_mapped_value(raw, column_mapping, "billing_period_end"))
        row = CopilotBillingRow(
            row_number=index,
            sku=sku,
            unit_type=unit_type,
            monthly_amount=_decimal(_pick_mapped_value(raw, column_mapping, "monthly_amount")),
            net_amount=_decimal(_pick_mapped_value(raw, column_mapping, "net_amount")),
            gross_amount=_decimal(_pick_mapped_value(raw, column_mapping, "gross_amount")),
            quantity=int(_decimal(_pick_mapped_value(raw, column_mapping, "quantity"))),
            billing_period_start=raw_period_start,
            billing_period_end=raw_period_end,
            usage_date=usage_date,
            user_login=(
                str(_pick_mapped_value(raw, column_mapping, "user_login") or "").strip() or None
            ),
            raw_payload=dict(raw),
        )
        if not sku:
            row.error_reason = "Missing SKU"
        elif sku not in KNOWN_SKUS:
            row.error_reason = f"Unknown SKU '{sku}'"
        elif not unit_type:
            row.error_reason = "Missing unit type"
        rows.append(row)

    valid_rows = [row for row in rows if row.error_reason is None]
    if not valid_rows:
        return CopilotParseResult(
            rows=rows,
            error_message="No valid Copilot billing rows found. Check SKU and unit_type columns.",
        )

    report_start, report_end = report_period_bounds(
        usage_dates=[row.usage_date for row in valid_rows if row.usage_date],
        period_starts=[row.billing_period_start for row in valid_rows if row.billing_period_start],
        period_ends=[row.billing_period_end for row in valid_rows if row.billing_period_end],
    )
    for row in valid_rows:
        row.billing_period_start, row.billing_period_end = resolve_billing_period(
            row.billing_period_start,
            row.billing_period_end,
            report_start=report_start,
            report_end=report_end,
        )

    return CopilotParseResult(rows=rows, aggregates=aggregate_copilot_billing(valid_rows))


def aggregate_copilot_billing(rows: list[CopilotBillingRow]) -> list[CopilotBillingAggregate]:
    grouped: dict[tuple[str, date | None, date | None], list[CopilotBillingRow]] = {}
    for row in rows:
        key = (row.sku, row.billing_period_start, row.billing_period_end)
        grouped.setdefault(key, []).append(row)

    aggregates: list[CopilotBillingAggregate] = []
    for (sku, period_start, period_end), bucket in grouped.items():
        monthly_cost_limit = Decimal("0")
        additional_cost = Decimal("0")
        credits_cost = Decimal("0")
        seat_count: int | None = None

        for row in bucket:
            additional_cost += row.net_amount
            if row.unit_type in AI_CREDITS_UNIT_TYPES:
                credits_cost += row.gross_amount
            if row.unit_type in USER_MONTHS_UNIT_TYPES and row.quantity > 0:
                seat_count = (seat_count or 0) + row.quantity

        total = sum((row.gross_amount for row in bucket), Decimal("0"))
        aggregates.append(
            CopilotBillingAggregate(
                sku=sku,
                billing_period_start=period_start,
                billing_period_end=period_end,
                monthly_cost_limit=monthly_cost_limit,
                additional_cost=additional_cost,
                credits_cost=credits_cost,
                total_cost=total,
                seat_count=seat_count,
                row_count=len(bucket),
            )
        )
    return aggregates


def _pick_from_raw(raw: dict[str, Any], field: str) -> Decimal:
    normalized = {_normalize_key(k): v for k, v in raw.items()}
    for alias in COPILOT_FIELD_ALIASES.get(field, ()):
        value = normalized.get(_normalize_key(alias))
        if value is not None and str(value).strip() != "":
            return _decimal(value)
    return Decimal("0")


def extract_row_amounts(
    mapped: dict[str, Any],
    raw: dict[str, Any] | None = None,
) -> tuple[Decimal, Decimal]:
    """Return (net_amount, gross_amount) with CSV header fallbacks."""
    net = _decimal(mapped.get("net_amount"))
    gross = _decimal(mapped.get("gross_amount"))
    if raw:
        if net == 0:
            net = _pick_from_raw(raw, "net_amount")
        if gross == 0:
            gross = _pick_from_raw(raw, "gross_amount")
    if gross == 0 and net > 0:
        gross = net
    return net, gross


def apply_configured_subscription(
    aggregates: list[CopilotBillingAggregate],
    configured_subscription: Decimal | None,
) -> None:
    """Attach team-configured subscription limit and recompute stored totals."""
    if not aggregates:
        return
    subscription = configured_subscription or Decimal("0")

    for aggregate in aggregates:
        if aggregate.sku == "copilot_for_business" and subscription > 0:
            aggregate.monthly_cost_limit = subscription
        else:
            aggregate.monthly_cost_limit = Decimal("0")


def summarize_aggregates(
    aggregates: list[CopilotBillingAggregate],
    *,
    configured_subscription: Decimal | None = None,
) -> dict[str, Any]:
    additional_cost = sum((row.additional_cost for row in aggregates), Decimal("0"))
    credits_cost = sum((row.credits_cost for row in aggregates), Decimal("0"))
    monthly_cost_limit = configured_subscription or Decimal("0")
    total_cost = sum((row.total_cost for row in aggregates), Decimal("0"))
    return {
        "monthly_cost_limit": float(monthly_cost_limit),
        "additional_cost": float(additional_cost),
        "credits_cost": float(credits_cost),
        "total_cost": float(total_cost),
        "sku_breakdown": [
            {
                "sku": row.sku,
                "billing_period_start": row.billing_period_start.isoformat()
                if row.billing_period_start
                else None,
                "billing_period_end": row.billing_period_end.isoformat()
                if row.billing_period_end
                else None,
                "monthly_cost_limit": float(row.monthly_cost_limit),
                "additional_cost": float(row.additional_cost),
                "total_cost": float(row.total_cost),
                "seat_count": row.seat_count,
                "row_count": row.row_count,
            }
            for row in aggregates
        ],
    }
