"""Cost calculation rules for normalized vendor events."""

from __future__ import annotations

from decimal import Decimal

from app.normalization.schemas import (
    NormalizedLicenseEvent,
    NormalizedProductivityEvent,
    NormalizedTokenEvent,
)


def apply_token_cost_from_api(event: NormalizedTokenEvent) -> NormalizedTokenEvent:
    if event.charged_cents_usd is not None and event.charged_cents_usd > 0:
        return _replace_token(
            event,
            estimated_cost_usd=event.charged_cents_usd,
            cost_rule_applied="api_charged_cents",
            cost_matches_rule=True,
        )
    if event.estimated_cost_usd > 0:
        return _replace_token(
            event,
            cost_rule_applied=event.cost_rule_applied or "api_cost_field",
            cost_matches_rule=True,
        )
    return event


def apply_token_cost_from_pricing(
    event: NormalizedTokenEvent,
    *,
    input_price_per_million: Decimal,
    output_price_per_million: Decimal,
) -> NormalizedTokenEvent:
    if event.estimated_cost_usd > 0 or (event.charged_cents_usd and event.charged_cents_usd > 0):
        return apply_token_cost_from_api(event)

    input_cost = (Decimal(event.parsed_input_tokens) / Decimal("1000000")) * input_price_per_million
    output_cost = (Decimal(event.parsed_output_tokens) / Decimal("1000000")) * output_price_per_million
    total = input_cost + output_cost
    return _replace_token(
        event,
        estimated_cost_usd=total,
        cost_rule_applied=(
            f"(input/1M×{input_price_per_million})+(output/1M×{output_price_per_million})"
        ),
        cost_matches_rule=True,
    )


def apply_productivity_seat_cost(
    event: NormalizedProductivityEvent,
    *,
    monthly_package_cost: Decimal,
    assigned_seats: int,
) -> NormalizedProductivityEvent:
    if assigned_seats <= 0:
        per_seat = Decimal("0")
        rule = "no assigned seats"
    else:
        per_seat = monthly_package_cost / Decimal(assigned_seats)
        rule = f"{monthly_package_cost} / {assigned_seats} seats"
    return NormalizedProductivityEvent(
        **{
            **event.__dict__,
            "estimated_cost": per_seat,
            "cost_rule": rule,
        }
    )


def apply_license_seat_cost(
    event: NormalizedLicenseEvent,
    *,
    monthly_package_cost: Decimal,
    assigned_licenses: int,
) -> NormalizedLicenseEvent:
    if assigned_licenses <= 0:
        per_license = Decimal("0")
        rule = "no assigned licenses"
    else:
        per_license = monthly_package_cost / Decimal(assigned_licenses)
        rule = f"{monthly_package_cost} / {assigned_licenses} licenses"
    return NormalizedLicenseEvent(
        **{
            **event.__dict__,
            "estimated_monthly_cost": per_license,
            "cost_rule": rule,
        }
    )


def _replace_token(event: NormalizedTokenEvent, **updates: object) -> NormalizedTokenEvent:
    data = {**event.__dict__, **updates}
    return NormalizedTokenEvent(**data)
