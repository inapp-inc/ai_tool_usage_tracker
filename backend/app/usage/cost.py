"""Effective cost expressions for usage events (Cursor included vs billable)."""

from decimal import Decimal

from sqlalchemy import ColumnElement, and_, case, func

from app.models.collector import UsageEvent


def usage_event_effective_cost_sql() -> ColumnElement:
    """Billable cost, or plan-included reference cost for Cursor included rows."""
    return case(
        (
            and_(
                UsageEvent.included_in_plan.is_(True),
                UsageEvent.provider == "cursor",
            ),
            func.coalesce(UsageEvent.reference_cost, 0),
        ),
        else_=UsageEvent.estimated_cost,
    )


def cursor_included_cost_from_event(event: dict, token_usage: dict) -> Decimal:
    """USD value of tokens consumed from the plan (included kind)."""
    try:
        total_cents = token_usage.get("totalCents")
        if total_cents is not None:
            return Decimal(str(total_cents)) / Decimal("100")
    except Exception:  # noqa: BLE001
        pass
    try:
        charged = event.get("chargedCents")
        if charged is not None:
            return Decimal(str(charged)) / Decimal("100")
    except Exception:  # noqa: BLE001
        pass
    return Decimal("0")


def cursor_billable_cost_from_event(event: dict, token_usage: dict) -> Decimal:
    """Additional USD billed beyond the plan (non-included kind)."""
    try:
        charged = event.get("chargedCents")
        if charged is not None:
            return Decimal(str(charged)) / Decimal("100")
    except Exception:  # noqa: BLE001
        pass
    try:
        total_cents = token_usage.get("totalCents")
        if total_cents is not None:
            return Decimal(str(total_cents)) / Decimal("100")
    except Exception:  # noqa: BLE001
        pass
    return Decimal("0")
