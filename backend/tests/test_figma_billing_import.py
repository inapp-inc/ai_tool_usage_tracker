"""Tests for Figma billing CSV parser."""

from datetime import date
from decimal import Decimal

from app.figma.billing_import import (
    aggregate_figma_billing_rows,
    parse_figma_billing_csv,
    suggest_figma_column_mapping,
)
from app.figma.pricing import (
    FigmaTeamPricing,
    calculate_figma_row_costs,
    figma_configured_subscription,
    figma_paid_credit_cost,
)

FIGMA_CSV = """User ID,User name,User email,Seat type,Seat credits used,Paid credits used,Last activity,Usage period start,Usage period end
u1,Alice,alice@example.com,Full,100,50,2026-06-15,2026-06-01,2026-06-17
u2,Bob,bob@example.com,View,20,10,2026-06-16,2026-06-01,2026-06-17
u3,Carol,carol@example.com,full,0,0,2026-06-10,2026-06-01,2026-06-17
"""

MAPPING = suggest_figma_column_mapping(
    [
        "User ID",
        "User name",
        "User email",
        "Seat type",
        "Seat credits used",
        "Paid credits used",
        "Last activity",
        "Usage period start",
        "Usage period end",
    ]
)


def test_suggest_figma_column_mapping() -> None:
    assert MAPPING["user_email"] == "User email"
    assert MAPPING["usage_period_start"] == "Usage period start"
    assert MAPPING["seat_type"] == "Seat type"


def test_parse_figma_csv_keeps_all_users_in_period() -> None:
    result = parse_figma_billing_csv(FIGMA_CSV, column_mapping=MAPPING)
    assert result.error_message is None
    assert len(result.rows) == 3
    valid = [row for row in result.rows if row.error_reason is None]
    assert len(valid) == 3
    assert all(row.usage_period_start == date(2026, 6, 1) for row in valid)
    assert all(row.usage_period_end == date(2026, 6, 17) for row in valid)
    assert valid[0].seat_type == "full"
    assert valid[1].seat_type == "view"


def test_calculate_figma_row_costs_with_credits_per_usd() -> None:
    pricing = FigmaTeamPricing(
        full_seat_cost_usd=Decimal("55"),
        view_seat_cost_usd=Decimal("10"),
        credits_per_usd=Decimal("0.03"),
        included_credits_per_seat=Decimal("3500"),
        configured_seat_count=11,
    )
    seat_cost, paid_cost, total = calculate_figma_row_costs(
        seat_type="full",
        seat_credits_used=Decimal("100"),
        paid_credits_used=Decimal("1000"),
        pricing=pricing,
    )
    assert seat_cost == Decimal("0")
    assert paid_cost == Decimal("30")  # 1000 × $0.03
    assert total == Decimal("30")


def test_figma_paid_credit_cost_demo_totals() -> None:
    assert figma_paid_credit_cost(Decimal("4226"), Decimal("0.03")) == Decimal("126.78")
    pricing = FigmaTeamPricing(
        full_seat_cost_usd=Decimal("55"),
        view_seat_cost_usd=None,
        credits_per_usd=Decimal("0.03"),
        included_credits_per_seat=Decimal("3500"),
        configured_seat_count=11,
    )
    assert figma_configured_subscription(pricing, full_seat_count=3, view_seat_count=0) == Decimal(
        "605"
    )


def test_aggregate_figma_billing_rows_counts_seat_types() -> None:
    result = parse_figma_billing_csv(FIGMA_CSV, column_mapping=MAPPING)
    valid = [row for row in result.rows if row.error_reason is None]
    pricing = FigmaTeamPricing(
        full_seat_cost_usd=Decimal("15"),
        view_seat_cost_usd=Decimal("5"),
        credits_per_usd=Decimal("0.03"),
        included_credits_per_seat=None,
        configured_seat_count=None,
    )
    row_costs = [
        calculate_figma_row_costs(
            seat_type=row.seat_type,
            seat_credits_used=row.seat_credits_used,
            paid_credits_used=row.paid_credits_used,
            pricing=pricing,
        )
        for row in valid
    ]
    aggregates = aggregate_figma_billing_rows(valid, row_costs=row_costs)
    assert len(aggregates) == 1
    assert aggregates[0].user_count == 3
    assert aggregates[0].full_seat_count == 2
    assert aggregates[0].view_seat_count == 1
    # 50 + 10 paid credits × $0.03 = $1.80
    assert aggregates[0].total_paid_cost == Decimal("1.8")
