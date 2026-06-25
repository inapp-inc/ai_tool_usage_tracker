"""Tests for threshold evaluator breach detection."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.notifications import Threshold
from app.thresholds.evaluator import ThresholdEvaluator


def _threshold(**overrides) -> MagicMock:
    row = MagicMock(spec=Threshold)
    row.id = uuid4()
    row.organization_id = uuid4()
    row.active = True
    row.threshold_type = "cost_amount"
    row.limit_value = Decimal("1")
    row.severity = "warning"
    row.name = "Cost cap"
    row.scope = "organization"
    row.team_id = None
    row.tool_id = None
    row.notify_in_app = True
    for key, value in overrides.items():
        setattr(row, key, value)
    return row


@pytest.mark.asyncio
async def test_cost_breach_fires_when_current_exceeds_limit() -> None:
    threshold = _threshold()
    event = MagicMock()
    event.id = uuid4()
    event.message = "breach"

    evaluator = ThresholdEvaluator(MagicMock())
    evaluator._events = MagicMock()
    evaluator._events.has_unacknowledged = AsyncMock(return_value=False)
    evaluator._events.create = AsyncMock(return_value=event)
    evaluator._dashboard = MagicMock()
    evaluator._dashboard.get_threshold_current_value = AsyncMock(return_value=Decimal("12.50"))

    import app.thresholds.evaluator as evaluator_module

    deliver = AsyncMock(return_value=1)
    original = evaluator_module.deliver_threshold_breach_notifications
    evaluator_module.deliver_threshold_breach_notifications = deliver
    try:
        created = await evaluator.evaluate_threshold(threshold)
    finally:
        evaluator_module.deliver_threshold_breach_notifications = original

    assert created == 1
    assert threshold.active is False


@pytest.mark.asyncio
async def test_cost_breach_skips_when_below_limit() -> None:
    threshold = _threshold(limit_value=Decimal("100"))

    evaluator = ThresholdEvaluator(MagicMock())
    evaluator._events = MagicMock()
    evaluator._events.has_unacknowledged = AsyncMock(return_value=False)
    evaluator._events.create = AsyncMock()
    evaluator._dashboard = MagicMock()
    evaluator._dashboard.get_threshold_current_value = AsyncMock(return_value=Decimal("0.50"))

    created = await evaluator.evaluate_threshold(threshold)

    assert created == 0
    evaluator._events.create.assert_not_called()


@pytest.mark.asyncio
async def test_cost_breach_at_exact_limit_fires() -> None:
    threshold = _threshold(limit_value=Decimal("1"))

    evaluator = ThresholdEvaluator(MagicMock())
    evaluator._events = MagicMock()
    evaluator._events.has_unacknowledged = AsyncMock(return_value=False)
    evaluator._events.create = AsyncMock(return_value=MagicMock(id=uuid4()))
    evaluator._dashboard = MagicMock()
    evaluator._dashboard.get_threshold_current_value = AsyncMock(return_value=Decimal("1.00"))

    import app.thresholds.evaluator as evaluator_module

    original = evaluator_module.deliver_threshold_breach_notifications
    evaluator_module.deliver_threshold_breach_notifications = AsyncMock(return_value=1)
    try:
        created = await evaluator.evaluate_threshold(threshold)
    finally:
        evaluator_module.deliver_threshold_breach_notifications = original

    assert created == 1
