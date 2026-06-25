"""Tests for Copilot billing period helpers."""

from datetime import date
from decimal import Decimal

from app.copilot.billing_import import CopilotBillingAggregate
from app.copilot.billing_period import (
    normalize_billing_period,
    period_from_aggregates,
    report_period_bounds,
    resolve_billing_period,
)


def test_period_from_aggregates_uses_csv_dates() -> None:
    aggregates = [
        CopilotBillingAggregate(
            sku="copilot_for_business",
            billing_period_start=date(2026, 5, 1),
            billing_period_end=date(2026, 5, 31),
            monthly_cost_limit=Decimal("100"),
            additional_cost=Decimal("0"),
            credits_cost=Decimal("0"),
            total_cost=Decimal("100"),
            seat_count=1,
            row_count=1,
        )
    ]
    start, end = period_from_aggregates(aggregates)
    assert start == date(2026, 5, 1)
    assert end == date(2026, 5, 31)


def test_period_from_aggregates_falls_back_to_anchor_month() -> None:
    aggregates = [
        CopilotBillingAggregate(
            sku="copilot_for_business",
            billing_period_start=None,
            billing_period_end=None,
            monthly_cost_limit=Decimal("100"),
            additional_cost=Decimal("0"),
            credits_cost=Decimal("0"),
            total_cost=Decimal("100"),
            seat_count=1,
            row_count=1,
        )
    ]
    start, end = period_from_aggregates(aggregates, fallback_anchor=date(2026, 6, 15))
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 30)


def test_normalize_billing_period_uses_month_end_when_requested() -> None:
    start, end = normalize_billing_period(date(2026, 6, 1), None, infer_month_end=True)
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 30)


def test_resolve_billing_period_uses_report_end_not_month_end() -> None:
    start, end = resolve_billing_period(
        date(2026, 6, 1),
        None,
        report_end=date(2026, 6, 17),
    )
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 17)


def test_report_period_bounds_from_usage_dates() -> None:
    start, end = report_period_bounds(
        usage_dates=[date(2026, 6, 1), date(2026, 6, 17), date(2026, 6, 10)],
    )
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 17)


def test_period_from_aggregates_with_start_only_rows() -> None:
    aggregates = [
        CopilotBillingAggregate(
            sku="copilot_for_business",
            billing_period_start=date(2026, 6, 1),
            billing_period_end=None,
            monthly_cost_limit=Decimal("100"),
            additional_cost=Decimal("0"),
            credits_cost=Decimal("0"),
            total_cost=Decimal("100"),
            seat_count=1,
            row_count=1,
        )
    ]
    start, end = period_from_aggregates(
        aggregates,
        report_start=date(2026, 6, 1),
        report_end=date(2026, 6, 17),
    )
    assert start == date(2026, 6, 1)
    assert end == date(2026, 6, 17)
