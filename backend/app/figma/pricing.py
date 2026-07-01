"""Figma team pricing helpers for CSV cost calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.admin import TeamTool


@dataclass(frozen=True)
class FigmaTeamPricing:
    full_seat_cost_usd: Decimal | None
    view_seat_cost_usd: Decimal | None
    """USD cost per paid credit (e.g. 0.03 from $30 per 1000 credits)."""
    credits_per_usd: Decimal | None
    included_credits_per_seat: Decimal | None
    configured_seat_count: int | None


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except Exception:
        return None
    if parsed <= 0:
        return None
    return parsed


def figma_pricing_from_assignment(assignment: TeamTool | None) -> FigmaTeamPricing:
    if assignment is None:
        return FigmaTeamPricing(None, None, None, None, None)

    config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
    credits_per_usd = _decimal_or_none(
        config.get("credits_per_usd") or config.get("credit_amount")
    )
    full_seat = _decimal_or_none(config.get("full_seat_cost_usd")) or _decimal_or_none(
        assignment.cost_per_seat
    ) or _decimal_or_none(config.get("cost_per_seat"))
    view_seat = _decimal_or_none(config.get("view_seat_cost_usd"))
    included = _decimal_or_none(config.get("included_credits_per_seat"))
    seat_count_raw = config.get("seat_count") or assignment.seat_count
    seat_count = int(seat_count_raw) if seat_count_raw not in (None, "") else None
    if seat_count is not None and seat_count <= 0:
        seat_count = None
    return FigmaTeamPricing(
        full_seat_cost_usd=full_seat,
        view_seat_cost_usd=view_seat,
        credits_per_usd=credits_per_usd,
        included_credits_per_seat=included,
        configured_seat_count=seat_count,
    )


def figma_configured_subscription(
    pricing: FigmaTeamPricing,
    *,
    full_seat_count: int = 0,
    view_seat_count: int = 0,
) -> Decimal:
    """
    Monthly subscription from team config (e.g. 11 seats × $55).

    Uses configured seat count when set; otherwise falls back to import seat counts.
    """
    if pricing.full_seat_cost_usd and pricing.configured_seat_count:
        total = pricing.full_seat_cost_usd * Decimal(pricing.configured_seat_count)
        if pricing.view_seat_cost_usd and view_seat_count:
            total += pricing.view_seat_cost_usd * Decimal(view_seat_count)
        return total
    full_total = (pricing.full_seat_cost_usd or Decimal("0")) * Decimal(full_seat_count)
    view_total = (pricing.view_seat_cost_usd or Decimal("0")) * Decimal(view_seat_count)
    return full_total + view_total


@dataclass(frozen=True)
class FigmaImportPeriodSlice:
    usage_period_start: date | None
    usage_period_end: date | None
    full_seat_count: int
    view_seat_count: int
    paid_cost_usd: Decimal
    paid_credits: Decimal = Decimal("0")


def figma_billing_cycle_key(
    subscription_start: date | None,
    usage_period_start: date | None,
    usage_period_end: date | None,
) -> tuple[date, date] | None:
    """Normalize an import usage window onto one subscription billing cycle."""
    if usage_period_start is None:
        return None
    if subscription_start is not None:
        from app.billing.subscription_period import subscription_period_for_date

        return subscription_period_for_date(subscription_start, usage_period_start)
    return (usage_period_start, usage_period_end or usage_period_start)


def merge_figma_import_slices_by_cycle(
    slices: list[FigmaImportPeriodSlice],
    subscription_start: date | None,
) -> list[FigmaImportPeriodSlice]:
    """Merge import rows that belong to the same subscription billing cycle."""
    merged: dict[tuple[date, date], FigmaImportPeriodSlice] = {}
    for slice_ in slices:
        cycle_key = figma_billing_cycle_key(
            subscription_start,
            slice_.usage_period_start,
            slice_.usage_period_end,
        )
        if cycle_key is None:
            continue
        existing = merged.get(cycle_key)
        if existing is None:
            merged[cycle_key] = FigmaImportPeriodSlice(
                usage_period_start=cycle_key[0],
                usage_period_end=cycle_key[1],
                full_seat_count=slice_.full_seat_count,
                view_seat_count=slice_.view_seat_count,
                paid_cost_usd=slice_.paid_cost_usd,
                paid_credits=slice_.paid_credits,
            )
            continue
        merged[cycle_key] = FigmaImportPeriodSlice(
            usage_period_start=cycle_key[0],
            usage_period_end=cycle_key[1],
            full_seat_count=max(existing.full_seat_count, slice_.full_seat_count),
            view_seat_count=max(existing.view_seat_count, slice_.view_seat_count),
            paid_cost_usd=existing.paid_cost_usd + slice_.paid_cost_usd,
            paid_credits=existing.paid_credits + slice_.paid_credits,
        )
    return [merged[key] for key in sorted(merged.keys())]


def figma_split_costs_from_import_slices(
    slices: list[FigmaImportPeriodSlice],
    pricing: FigmaTeamPricing,
    subscription_start: date | None,
) -> tuple[Decimal, Decimal, list[FigmaImportPeriodSlice]]:
    """
    Return subscription, additional paid-credit cost, and cycle-merged slices.

    Subscription is counted once per billing cycle even when multiple imports
    overlap the same cycle (for example calendar-month and anchored-period CSVs).
    """
    merged = merge_figma_import_slices_by_cycle(slices, subscription_start)
    subscription = Decimal("0")
    additional = Decimal("0")
    has_seat_pricing = pricing.full_seat_cost_usd is not None or pricing.view_seat_cost_usd is not None
    for slice_ in merged:
        if has_seat_pricing:
            subscription += figma_configured_subscription(
                pricing,
                full_seat_count=slice_.full_seat_count,
                view_seat_count=slice_.view_seat_count,
            )
        additional += slice_.paid_cost_usd
    return subscription, additional, merged


def figma_paid_credit_cost(
    paid_credits: Decimal,
    usd_per_credit: Decimal | None,
) -> Decimal:
    """Additional USD cost from paid credits: credits × USD per credit."""
    if usd_per_credit is None or usd_per_credit <= 0:
        return Decimal("0")
    return paid_credits * usd_per_credit


def calculate_figma_row_costs(
    *,
    seat_type: str,
    seat_credits_used: Decimal,
    paid_credits_used: Decimal,
    pricing: FigmaTeamPricing,
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Return (seat_cost_usd, paid_cost_usd, total_cost_usd).

    Seat credits used are included in the subscription package configured at team
    creation — they are tracked for reporting but not costed again from CSV.

    Import overage (paid credits purchased after package exhaustion):
      paid_cost_usd = paid_credits_used × usd_per_paid_credit

    Example: $30 per 1000 credits → enter 0.03; 1000 paid credits → $30 additional.

    Subscription (seats × monthly seat price) is computed at insights level from team config.
    """
    _ = (
        seat_type,
        seat_credits_used,
        pricing.full_seat_cost_usd,
        pricing.view_seat_cost_usd,
        pricing.included_credits_per_seat,
    )
    usd_per_credit = pricing.credits_per_usd
    paid_cost_usd = (
        paid_credits_used * usd_per_credit
        if usd_per_credit is not None and usd_per_credit > 0
        else Decimal("0")
    )
    seat_cost_usd = Decimal("0")
    total = paid_cost_usd
    return seat_cost_usd, paid_cost_usd, total
