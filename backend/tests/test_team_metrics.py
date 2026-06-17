"""Tests for team pricing cost calculator and list metrics."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.teams.cost_calculator import calculate_pricing_cost
from app.teams.pricing_resolution import ResolvedTeamToolPricing


def _pricing(**overrides) -> ResolvedTeamToolPricing:
    defaults = {
        "pricing_model": "flat_token",
        "token_price": Decimal("0.003"),
        "output_token_price": Decimal("0.006"),
        "cost_per_seat": None,
        "seat_count": None,
        "package_allowance": None,
        "overage_price": None,
        "plan_name": None,
        "pricing_config": {"model": "per_token"},
        "source": "team_tool",
    }
    defaults.update(overrides)
    return ResolvedTeamToolPricing(**defaults)


def test_calculate_pricing_cost_per_token() -> None:
    pricing = _pricing()

    cost = calculate_pricing_cost(
        pricing,
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
    )

    assert cost == Decimal("0.006")


def test_calculate_pricing_cost_includes_seat_fixed_cost() -> None:
    pricing = _pricing(
        pricing_model="custom",
        token_price=Decimal("0"),
        output_token_price=None,
        cost_per_seat=Decimal("20"),
        seat_count=5,
        pricing_config={"model": "per_seat"},
    )

    cost = calculate_pricing_cost(
        pricing,
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
    )

    assert cost == Decimal("100")


def test_calculate_pricing_cost_package_overage() -> None:
    pricing = _pricing(
        pricing_model="package_with_overage",
        token_price=Decimal("0"),
        output_token_price=None,
        package_allowance=1000,
        overage_price=Decimal("0.002"),
        pricing_config={"model": "flat_fee", "flat_monthly_cost": 99},
    )

    cost = calculate_pricing_cost(
        pricing,
        input_tokens=800,
        output_tokens=700,
        total_tokens=1500,
    )

    assert cost == Decimal("99.001")
