"""Tests for tools pricing helpers."""

from decimal import Decimal

import pytest

from app.tools.pricing import (
    normalize_pricing_config,
    normalize_vendor,
    pricing_config_for_response,
    validate_vendor,
)


def test_normalize_vendor_aliases() -> None:
    assert normalize_vendor("OpenAI") == "openai"
    assert normalize_vendor("Azure OpenAI") == "azure_openai"


def test_validate_vendor_accepts_figma() -> None:
    assert validate_vendor("figma") == "figma"


def test_validate_vendor_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Unsupported vendor"):
        validate_vendor("unknown-vendor")


def test_normalize_pricing_config_mirrors_columns() -> None:
    config = normalize_pricing_config(
        "package_with_overage",
        {"plan_name": "Team Pro", "flat_monthly_cost": 99},
        package_allowance=1_000_000,
        overage_price=Decimal("0.002"),
    )
    assert config["plan_name"] == "Team Pro"
    assert config["included_tokens"] == 1_000_000
    assert config["overage_rate"] == 0.002
    assert config["model"] == "flat_fee"


def test_pricing_config_for_response_includes_flat_fee_fields() -> None:
    config = pricing_config_for_response(
        "package_with_overage",
        {"plan_name": "Team Pro"},
        package_allowance=500_000,
        overage_price=Decimal("0.003"),
    )
    assert config["plan_name"] == "Team Pro"
    assert config["included_tokens"] == 500_000
    assert config["overage_rate"] == 0.003
