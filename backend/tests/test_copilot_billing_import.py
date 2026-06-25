"""Tests for GitHub Copilot billing CSV parser."""

from datetime import date
from decimal import Decimal

from app.copilot.billing_import import (
    aggregate_copilot_billing,
    apply_configured_subscription,
    extract_row_amounts,
    parse_copilot_billing_csv,
    summarize_aggregates,
)
from app.copilot.billing_totals import prorated_row_amounts_for_day, totals_from_mapped_rows

SAMPLE_CSV = """sku,unit_type,monthly_amount,net_amount,gross_amount,quantity,billing_period_start,billing_period_end,user_login
copilot_for_business,ai_credits,950.00,,150.00,1,2026-06-01,2026-06-30,
copilot_for_business,user-months,,38.00,76.00,2,2026-06-01,2026-06-30,dev-user-1
copilot_ai_credit,ai_credits,,,120.50,500,2026-06-01,2026-06-30,
"""

MAPPING = {
    "sku": "sku",
    "unit_type": "unit_type",
    "monthly_amount": "monthly_amount",
    "net_amount": "net_amount",
    "gross_amount": "gross_amount",
    "quantity": "quantity",
    "billing_period_start": "billing_period_start",
    "billing_period_end": "billing_period_end",
    "user_login": "user_login",
}


def test_parse_copilot_for_business_totals() -> None:
    result = parse_copilot_billing_csv(SAMPLE_CSV, column_mapping=MAPPING)
    assert result.error_message is None
    assert len(result.rows) == 3

    business = [row for row in result.aggregates if row.sku == "copilot_for_business"]
    assert len(business) == 1
    assert business[0].monthly_cost_limit == Decimal("0")
    assert business[0].additional_cost == Decimal("38.00")
    assert business[0].credits_cost == Decimal("150.00")
    assert business[0].total_cost == Decimal("226.00")
    assert business[0].seat_count == 2


def test_summarize_aggregates_uses_gross_total() -> None:
    result = parse_copilot_billing_csv(SAMPLE_CSV, column_mapping=MAPPING)
    summary = summarize_aggregates(
        result.aggregates,
        configured_subscription=Decimal("900.00"),
    )
    assert summary["monthly_cost_limit"] == 900.0
    assert summary["additional_cost"] == 38.0
    assert summary["credits_cost"] == 270.5
    assert summary["total_cost"] == 346.5


def test_apply_configured_subscription_does_not_change_gross_total() -> None:
    result = parse_copilot_billing_csv(SAMPLE_CSV, column_mapping=MAPPING)
    apply_configured_subscription(result.aggregates, Decimal("900.00"))
    business = next(row for row in result.aggregates if row.sku == "copilot_for_business")
    credits = next(row for row in result.aggregates if row.sku == "copilot_ai_credit")
    assert business.monthly_cost_limit == Decimal("900.00")
    assert business.total_cost == Decimal("226.00")
    assert credits.monthly_cost_limit == Decimal("0")
    assert credits.total_cost == Decimal("120.50")


def test_extract_row_amounts_falls_back_to_net_for_gross() -> None:
    net, gross = extract_row_amounts(
        {"net_amount": "38.00", "gross_amount": "0"},
        {"net_amount": "38.00"},
    )
    assert net == Decimal("38.00")
    assert gross == Decimal("38.00")


def test_extract_row_amounts_reads_raw_headers() -> None:
    net, gross = extract_row_amounts(
        {},
        {"Gross Amount": "120.50", "Net Amount": "10.00"},
    )
    assert net == Decimal("10.00")
    assert gross == Decimal("120.50")


def test_unknown_sku_flags_row() -> None:
    csv_text = "sku,unit_type\nunknown_sku,ai_credits\n"
    result = parse_copilot_billing_csv(
        csv_text,
        column_mapping={"sku": "sku", "unit_type": "unit_type"},
    )
    assert result.error_message is not None or any(row.error_reason for row in result.rows)


def test_aggregate_empty_rows() -> None:
    assert aggregate_copilot_billing([]) == []


def test_daily_proration_spreads_gross_across_period() -> None:
    mapped = {
        "gross_amount": "300",
        "net_amount": "30",
        "quantity": 30,
        "billing_period_start": "2026-06-01",
        "billing_period_end": "2026-06-30",
        "user_login": "dev-user-1",
        "sku": "copilot_for_business",
        "unit_type": "user-months",
    }
    totals = totals_from_mapped_rows([(mapped, None, None, None)])
    assert totals.gross_total == Decimal("300")
    assert len(totals.gross_by_day) == 30
    assert totals.gross_by_day[date(2026, 6, 1)] == Decimal("10")
    net, gross, qty = prorated_row_amounts_for_day(mapped, None, date(2026, 6, 3))
    assert net == Decimal("1")
    assert gross == Decimal("10")
    assert qty == 1


GITHUB_REPORT_CSV = """date,username,sku,unit_type,gross_amount,net_amount,quantity
2026-06-01,dev-user-1,copilot_for_business,ai_credits,10.00,0,1
2026-06-10,dev-user-1,copilot_for_business,ai_credits,10.00,0,1
2026-06-17,dev-user-1,copilot_for_business,ai_credits,10.00,0,1
"""

GITHUB_MAPPING = {
    "sku": "sku",
    "unit_type": "unit_type",
    "gross_amount": "gross_amount",
    "net_amount": "net_amount",
    "quantity": "quantity",
    "usage_date": "date",
    "user_login": "username",
}


def test_github_report_dates_set_billing_period_from_min_max_date() -> None:
    result = parse_copilot_billing_csv(GITHUB_REPORT_CSV, column_mapping=GITHUB_MAPPING)
    assert result.error_message is None
    assert len(result.rows) == 3
    assert all(row.billing_period_start == date(2026, 6, 1) for row in result.rows)
    assert all(row.billing_period_end == date(2026, 6, 17) for row in result.rows)
    assert result.aggregates[0].billing_period_end == date(2026, 6, 17)


def test_github_report_daily_totals_only_on_present_dates() -> None:
    result = parse_copilot_billing_csv(GITHUB_REPORT_CSV, column_mapping=GITHUB_MAPPING)
    rows = [
        (
            {
                "sku": row.sku,
                "unit_type": row.unit_type,
                "gross_amount": str(row.gross_amount),
                "net_amount": str(row.net_amount),
                "quantity": row.quantity,
                "usage_date": row.usage_date.isoformat() if row.usage_date else None,
                "billing_period_start": row.billing_period_start.isoformat()
                if row.billing_period_start
                else None,
                "billing_period_end": row.billing_period_end.isoformat()
                if row.billing_period_end
                else None,
            },
            row.raw_payload,
            date(2026, 6, 1),
            date(2026, 6, 17),
        )
        for row in result.rows
    ]
    totals = totals_from_mapped_rows(rows)
    assert len(totals.gross_by_day) == 3
    assert totals.gross_by_day[date(2026, 6, 17)] == Decimal("10")
    assert date(2026, 6, 18) not in totals.gross_by_day
