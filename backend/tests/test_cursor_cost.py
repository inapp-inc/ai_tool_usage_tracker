"""Tests for Cursor effective cost helpers."""

from decimal import Decimal

from app.usage.cost import (
    cursor_billable_cost_from_event,
    cursor_included_cost_from_event,
)


def test_included_cost_prefers_total_cents() -> None:
    event = {"kind": "Included in Business", "chargedCents": 14.68865}
    token_usage = {"totalCents": 31.781}
    assert cursor_included_cost_from_event(event, token_usage) == Decimal("0.31781")


def test_included_cost_falls_back_to_charged_cents() -> None:
    event = {"kind": "Included in Business", "chargedCents": 14.68865}
    assert cursor_included_cost_from_event(event, {}) == Decimal("0.1468865")


def test_billable_cost_uses_charged_cents() -> None:
    event = {"kind": "Usage-based", "chargedCents": 14.68865}
    token_usage = {"totalCents": 31.781}
    assert cursor_billable_cost_from_event(event, token_usage) == Decimal("0.1468865")
