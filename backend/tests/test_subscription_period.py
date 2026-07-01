"""Tests for subscription-anchored billing periods."""

from datetime import date

from app.billing.subscription_period import (
    next_subscription_period_start,
    subscription_period_for_date,
    subscription_periods_overlapping,
)


def test_subscription_period_for_date_same_month() -> None:
    anchor = date(2026, 1, 14)
    start, end = subscription_period_for_date(anchor, date(2026, 1, 20))
    assert start == date(2026, 1, 14)
    assert end == date(2026, 2, 13)


def test_subscription_period_for_date_before_anchor_day() -> None:
    anchor = date(2026, 1, 14)
    start, end = subscription_period_for_date(anchor, date(2026, 2, 10))
    assert start == date(2026, 1, 14)
    assert end == date(2026, 2, 13)


def test_subscription_period_for_date_after_anchor_day() -> None:
    anchor = date(2026, 1, 14)
    start, end = subscription_period_for_date(anchor, date(2026, 2, 20))
    assert start == date(2026, 2, 14)
    assert end == date(2026, 3, 13)


def test_next_subscription_period_start() -> None:
    anchor = date(2026, 1, 14)
    assert next_subscription_period_start(anchor, date(2026, 1, 14)) == date(2026, 2, 14)


def test_subscription_periods_overlapping() -> None:
    anchor = date(2026, 1, 14)
    periods = subscription_periods_overlapping(
        anchor,
        date(2026, 2, 1),
        date(2026, 3, 20),
    )
    assert periods == [
        (date(2026, 1, 14), date(2026, 2, 13)),
        (date(2026, 2, 14), date(2026, 3, 13)),
    ]


def test_effective_subscription_query_range() -> None:
    from app.billing.subscription_period import effective_subscription_query_range

    anchor = date(2026, 1, 14)
    start, end = effective_subscription_query_range(
        anchor,
        date(2026, 6, 1),
        date(2026, 6, 30),
    )
    assert start == date(2026, 5, 14)
    assert end == date(2026, 7, 13)


def test_effective_subscription_query_range_spans_multi_month_selection() -> None:
    from app.billing.subscription_period import effective_subscription_query_range

    anchor = date(2026, 1, 14)
    start, end = effective_subscription_query_range(
        anchor,
        date(2026, 4, 1),
        date(2026, 7, 31),
    )
    assert start == date(2026, 3, 14)
    assert end == date(2026, 8, 13)
