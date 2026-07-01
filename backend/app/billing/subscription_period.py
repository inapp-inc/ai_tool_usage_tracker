"""Subscription-anchored billing periods (e.g. 14th → 13th when start is Jan 14)."""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def _clamp_day(year: int, month: int, day: int) -> date:
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def next_subscription_period_start(anchor: date, period_start: date) -> date:
    """First day of the billing period immediately after ``period_start``."""
    month = period_start.month + 1
    year = period_start.year
    if month > 12:
        month = 1
        year += 1
    return _clamp_day(year, month, anchor.day)


def subscription_period_for_date(anchor: date, on_date: date) -> tuple[date, date]:
    """Return inclusive (start, end) for the subscription period containing ``on_date``."""
    start = _clamp_day(on_date.year, on_date.month, anchor.day)
    if on_date < start:
        month = on_date.month - 1
        year = on_date.year
        if month < 1:
            month = 12
            year -= 1
        start = _clamp_day(year, month, anchor.day)
    end = next_subscription_period_start(anchor, start) - timedelta(days=1)
    return start, end


def subscription_periods_overlapping(
    anchor: date,
    from_date: date,
    to_date: date,
) -> list[tuple[date, date]]:
    """List subscription billing periods that overlap ``[from_date, to_date]``."""
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    periods: list[tuple[date, date]] = []
    start, end = subscription_period_for_date(anchor, from_date)
    while start <= to_date:
        if end >= from_date:
            periods.append((start, end))
        start = next_subscription_period_start(anchor, start)
        end = next_subscription_period_start(anchor, start) - timedelta(days=1)
    return periods


def row_activity_date(
    *,
    last_activity: date | None = None,
    usage_period_start: date | None = None,
    usage_period_end: date | None = None,
) -> date | None:
    if usage_period_start is not None:
        return usage_period_start
    if last_activity is not None:
        return last_activity
    return usage_period_end


def effective_subscription_query_range(
    subscription_start: date | None,
    from_date: date,
    to_date: date,
) -> tuple[date, date]:
    """
    Map the Insights date picker range onto subscription billing cycles.

    Returns the union of all subscription cycles that overlap the selected range.
    Without a subscription anchor, returns the requested range unchanged.
    """
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    if subscription_start is None:
        return from_date, to_date

    periods = subscription_periods_overlapping(subscription_start, from_date, to_date)
    if not periods:
        return subscription_period_for_date(subscription_start, to_date)
    return periods[0][0], periods[-1][1]
