"""Calculate cost from resolved team–tool pricing and token usage."""

from decimal import Decimal
from typing import Any

from app.teams.pricing_resolution import ResolvedTeamToolPricing


def _per_1k_cost(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return value / Decimal("1000")


def _int_from_config(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _decimal_from_config(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None


def _subscription_fixed_cost(
    pricing: ResolvedTeamToolPricing,
    frontend_model: str,
) -> Decimal:
    """Configured monthly subscription cost from team-tool pricing."""
    config = pricing.pricing_config
    seat_count = pricing.seat_count or _int_from_config(config.get("seat_count"))

    if frontend_model == "per_team":
        unit = _decimal_from_config(config.get("cost_per_team")) or _decimal_from_config(
            config.get("flat_monthly_cost"),
        )
        if unit is not None and seat_count:
            return unit * Decimal(seat_count)
        return Decimal("0")

    if frontend_model == "per_seat":
        unit = (
            pricing.cost_per_seat
            or _decimal_from_config(config.get("cost_per_seat"))
            or _decimal_from_config(config.get("full_seat_cost_usd"))
        )
        if unit is not None and seat_count:
            return unit * Decimal(seat_count)
        return Decimal("0")

    flat_monthly = _decimal_from_config(config.get("flat_monthly_cost"))
    if flat_monthly is not None:
        return flat_monthly

    if pricing.cost_per_seat is not None and seat_count:
        return pricing.cost_per_seat * Decimal(seat_count)

    return Decimal("0")


def calculate_pricing_cost(
    pricing: ResolvedTeamToolPricing,
    *,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
) -> Decimal:
    """Apply team–tool pricing to aggregated token usage for the period."""
    config = pricing.pricing_config
    frontend_model = str(config.get("model") or pricing.pricing_model)

    fixed = _subscription_fixed_cost(pricing, frontend_model)

    variable = Decimal("0")
    total = max(total_tokens, input_tokens + output_tokens)

    if pricing.pricing_model == "flat_token" or frontend_model in {"per_token", "hybrid"}:
        input_rate = _per_1k_cost(pricing.token_price)
        output_rate = _per_1k_cost(pricing.output_token_price)
        variable += input_rate * Decimal(input_tokens)
        variable += output_rate * Decimal(output_tokens)

    if pricing.pricing_model == "package_with_overage" or frontend_model in {
        "flat_fee",
        "hybrid",
    }:
        included = pricing.package_allowance or 0
        overage_tokens = max(total - included, 0)
        if overage_tokens > 0 and pricing.overage_price is not None:
            variable += _per_1k_cost(pricing.overage_price) * Decimal(overage_tokens)

    if pricing.pricing_model == "custom" and frontend_model in {"per_seat", "per_team"}:
        return fixed

    return fixed + variable
