"""Calculate cost from resolved team–tool pricing and token usage."""

from decimal import Decimal

from app.teams.pricing_resolution import ResolvedTeamToolPricing


def _per_1k_cost(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    return value / Decimal("1000")


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

    fixed = Decimal("0")
    if pricing.cost_per_seat is not None and pricing.seat_count:
        fixed += pricing.cost_per_seat * Decimal(pricing.seat_count)

    flat_monthly = config.get("flat_monthly_cost")
    if flat_monthly is not None:
        try:
            fixed += Decimal(str(flat_monthly))
        except Exception:  # noqa: BLE001
            pass

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

    if pricing.pricing_model == "custom" and frontend_model == "per_seat":
        return fixed

    return fixed + variable
