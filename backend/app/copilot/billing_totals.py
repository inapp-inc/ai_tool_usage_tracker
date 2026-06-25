"""Shared Copilot billing totals from parsed CSV rows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.billing_import import (
    AI_CREDITS_UNIT_TYPES,
    USER_MONTHS_UNIT_TYPES,
    extract_row_amounts,
)
from app.copilot.billing_period import resolve_billing_period
from app.models.ingestion import ParsedRow, Upload


@dataclass
class CopilotBillingQuantityTotals:
    total_quantity: int = 0
    ai_credits_quantity: int = 0
    user_months_quantity: int = 0


@dataclass
class CopilotBillingParsedTotals:
    net_total: Decimal = Decimal("0")
    gross_total: Decimal = Decimal("0")
    credits_gross: Decimal = Decimal("0")
    quantities: CopilotBillingQuantityTotals = field(default_factory=CopilotBillingQuantityTotals)
    gross_by_period: dict[tuple[date | None, date | None], Decimal] = field(default_factory=dict)
    gross_by_sku_period: dict[tuple[str, date | None, date | None], Decimal] = field(
        default_factory=dict
    )
    gross_by_day: dict[date, Decimal] = field(default_factory=dict)
    net_by_day: dict[date, Decimal] = field(default_factory=dict)


def _as_date(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def inclusive_date_range(start: date | None, end: date | None) -> list[date]:
    if start is None and end is None:
        return []
    if start is None:
        start = end
    if end is None:
        end = start
    if start is None or end is None:
        return []
    if start > end:
        start, end = end, start
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def row_attribution_dates(
    mapped: dict,
    *,
    fallback_start: date | None = None,
    fallback_end: date | None = None,
) -> list[date]:
    usage = _as_date(
        mapped.get("usage_date")
        or mapped.get("billing_date")
        or mapped.get("transaction_date")
    )
    if usage is not None:
        return [usage]

    start = _as_date(mapped.get("billing_period_start")) or fallback_start
    end = _as_date(mapped.get("billing_period_end")) or fallback_end
    start, end = resolve_billing_period(
        start,
        end,
        report_start=fallback_start,
        report_end=fallback_end,
    )
    return inclusive_date_range(start, end)


def prorated_row_amounts_for_day(
    mapped: dict,
    raw: dict | None,
    on_date: date,
    *,
    fallback_start: date | None = None,
    fallback_end: date | None = None,
) -> tuple[Decimal, Decimal, int]:
    dates = row_attribution_dates(
        mapped,
        fallback_start=fallback_start,
        fallback_end=fallback_end,
    )
    if not dates or on_date not in dates:
        return Decimal("0"), Decimal("0"), 0

    net, gross = extract_row_amounts(mapped, raw if isinstance(raw, dict) else None)
    count = len(dates)
    quantity = int(mapped.get("quantity") or 0)
    qty_share = quantity // count if quantity > 0 else 0
    return net / count, gross / count, qty_share


def _apply_row_to_totals(
    totals: CopilotBillingParsedTotals,
    mapped: dict,
    raw: dict | None,
    *,
    fallback_start: date | None = None,
    fallback_end: date | None = None,
) -> None:
    if not isinstance(mapped, dict):
        return

    net, gross = extract_row_amounts(mapped, raw if isinstance(raw, dict) else None)
    unit_type = str(mapped.get("unit_type") or "").strip().lower().replace("_", "-")
    quantity = int(mapped.get("quantity") or 0)

    totals.net_total += net
    totals.gross_total += gross
    if unit_type in AI_CREDITS_UNIT_TYPES:
        totals.credits_gross += gross
        totals.quantities.ai_credits_quantity += quantity
    if unit_type in USER_MONTHS_UNIT_TYPES:
        totals.quantities.user_months_quantity += quantity
    totals.quantities.total_quantity += quantity

    period_key = resolve_billing_period(
        _as_date(mapped.get("billing_period_start")) or fallback_start,
        _as_date(mapped.get("billing_period_end")) or fallback_end,
        report_start=fallback_start,
        report_end=fallback_end,
    )
    totals.gross_by_period[period_key] = totals.gross_by_period.get(period_key, Decimal("0")) + gross
    sku = str(mapped.get("sku") or "").strip().lower()
    sku_key = (sku, period_key[0], period_key[1])
    totals.gross_by_sku_period[sku_key] = totals.gross_by_sku_period.get(sku_key, Decimal("0")) + gross

    dates = row_attribution_dates(
        mapped,
        fallback_start=fallback_start,
        fallback_end=fallback_end,
    )
    if not dates:
        return
    daily_net = net / len(dates)
    daily_gross = gross / len(dates)
    for day in dates:
        totals.net_by_day[day] = totals.net_by_day.get(day, Decimal("0")) + daily_net
        totals.gross_by_day[day] = totals.gross_by_day.get(day, Decimal("0")) + daily_gross


def totals_from_mapped_rows(
    rows: list[tuple[dict, dict | None, date | None, date | None]],
) -> CopilotBillingParsedTotals:
    totals = CopilotBillingParsedTotals()
    for mapped, raw, fallback_start, fallback_end in rows:
        _apply_row_to_totals(
            totals,
            mapped,
            raw,
            fallback_start=fallback_start,
            fallback_end=fallback_end,
        )
    return totals


async def load_parsed_rows_for_uploads(
    session: AsyncSession,
    upload_ids: list[UUID],
) -> list[tuple[dict, dict | None, date | None, date | None]]:
    if not upload_ids:
        return []
    result = await session.execute(
        select(ParsedRow, Upload)
        .outerjoin(Upload, ParsedRow.upload_id == Upload.id)
        .where(ParsedRow.upload_id.in_(upload_ids))
    )
    rows: list[tuple[dict, dict | None, date | None, date | None]] = []
    for parsed, upload in result.all():
        mapped = parsed.mapped_payload if isinstance(parsed.mapped_payload, dict) else {}
        raw = parsed.raw_payload if isinstance(parsed.raw_payload, dict) else None
        fallback_start = upload.billing_period_start if upload is not None else None
        fallback_end = upload.billing_period_end if upload is not None else None
        rows.append((mapped, raw, fallback_start, fallback_end))
    return rows


async def totals_from_upload_ids(
    session: AsyncSession,
    upload_ids: list[UUID],
) -> CopilotBillingParsedTotals:
    return totals_from_mapped_rows(await load_parsed_rows_for_uploads(session, upload_ids))
