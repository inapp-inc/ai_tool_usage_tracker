"""Tests for dashboard trend gap filling."""

from datetime import UTC, datetime
from decimal import Decimal

from app.dashboard.service import _fill_daily_trend_gaps
from app.dashboard.schemas import TrendPoint


def test_fill_daily_trend_gaps_zero_fills_missing_days() -> None:
    points = [
        TrendPoint(
            period_start=datetime(2026, 6, 1, tzinfo=UTC),
            total_tokens=100,
            estimated_cost=Decimal("1.25"),
            included_cost=Decimal("1.25"),
            billable_cost=Decimal("0"),
            breakdown_available=True,
        ),
        TrendPoint(
            period_start=datetime(2026, 6, 3, tzinfo=UTC),
            total_tokens=50,
            estimated_cost=Decimal("0.50"),
            included_cost=Decimal("0.50"),
            billable_cost=Decimal("0"),
            breakdown_available=True,
        ),
    ]
    filled = _fill_daily_trend_gaps(
        points,
        datetime(2026, 6, 1, tzinfo=UTC),
        datetime(2026, 6, 3, 23, 59, 59, tzinfo=UTC),
        breakdown_available=True,
    )
    assert len(filled) == 3
    assert filled[0].total_tokens == 100
    assert filled[1].total_tokens == 0
    assert filled[1].estimated_cost == Decimal("0")
    assert filled[2].total_tokens == 50
