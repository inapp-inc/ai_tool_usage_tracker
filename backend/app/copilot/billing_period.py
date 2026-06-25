"""Resolve billing period dates for Copilot CSV imports."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.copilot.billing_import import CopilotBillingAggregate


def month_end(value: date) -> date:
    last_day = calendar.monthrange(value.year, value.month)[1]
    return value.replace(day=last_day)


def report_period_bounds(
    *,
    usage_dates: Iterable[date] | None = None,
    period_starts: Iterable[date] | None = None,
    period_ends: Iterable[date] | None = None,
) -> tuple[date | None, date | None]:
    """Derive report start/end from row usage dates and explicit period columns (YYYY-MM-DD)."""
    starts = list(usage_dates or []) + list(period_starts or [])
    ends = list(usage_dates or []) + list(period_ends or [])
    if not starts and not ends:
        return None, None
    start = min(starts) if starts else None
    end = max(ends) if ends else None
    if start is not None and end is not None and end < start:
        start, end = end, start
    return start, end


def resolve_billing_period(
    period_start: date | None,
    period_end: date | None,
    *,
    report_start: date | None = None,
    report_end: date | None = None,
) -> tuple[date | None, date | None]:
    """Prefer explicit row dates, then report bounds. Does not infer calendar month-end."""
    start = period_start or report_start
    end = period_end or report_end
    if start is None:
        return None, end
    if end is None:
        return start, None
    if end < start:
        return end, start
    return start, end


def normalize_billing_period(
    period_start: date | None,
    period_end: date | None,
    *,
    report_start: date | None = None,
    report_end: date | None = None,
    infer_month_end: bool = False,
) -> tuple[date | None, date | None]:
    """Resolve billing period; optionally infer month-end when end is missing."""
    start, end = resolve_billing_period(
        period_start,
        period_end,
        report_start=report_start,
        report_end=report_end,
    )
    if start is not None and end is None and infer_month_end:
        return start, month_end(start)
    return start, end


def period_from_aggregates(
    aggregates: list[CopilotBillingAggregate],
    *,
    fallback_anchor: date | None = None,
    report_start: date | None = None,
    report_end: date | None = None,
) -> tuple[date | None, date | None]:
    from app.copilot.billing_import import CopilotBillingAggregate as _Aggregate

    normalized: list[tuple[date, date]] = []
    for row in aggregates:
        if not isinstance(row, _Aggregate):
            continue
        start, end = normalize_billing_period(
            row.billing_period_start,
            row.billing_period_end,
            report_start=report_start,
            report_end=report_end,
        )
        if start is not None and end is not None:
            normalized.append((start, end))

    if normalized:
        return min(start for start, _end in normalized), max(end for _start, end in normalized)

    bounds = report_period_bounds(period_starts=[report_start] if report_start else None, period_ends=[report_end] if report_end else None)
    if bounds[0] is not None and bounds[1] is not None:
        return bounds

    if fallback_anchor is None:
        return None, None
    return normalize_billing_period(
        fallback_anchor.replace(day=1),
        month_end(fallback_anchor),
        infer_month_end=True,
    )
