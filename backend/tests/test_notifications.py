"""Tests for in-app notifications and threshold delivery."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.notifications import Threshold, ThresholdEvent
from app.notifications.delivery import deliver_threshold_breach_notifications, resolve_recipient_user_ids
from app.notifications.service import NotificationService
from app.thresholds.evaluator import ThresholdEvaluator


@pytest.mark.asyncio
async def test_resolve_recipient_user_ids_org_scope() -> None:
    org_id = uuid4()
    admin = MagicMock()
    admin.id = uuid4()
    admin.role = "super_admin"
    member = MagicMock()
    member.id = uuid4()
    member.role = "team_member"

    session = MagicMock()
    users_repo = MagicMock()
    users_repo.list_by_organization = AsyncMock(return_value=[admin, member])

    threshold = MagicMock(spec=Threshold)
    threshold.organization_id = org_id
    threshold.scope = "organization"
    threshold.team_id = None
    threshold.user_id = None

    from app.notifications import delivery as delivery_module

    original = delivery_module.UserAdminRepository
    delivery_module.UserAdminRepository = MagicMock(return_value=users_repo)
    try:
        result = await resolve_recipient_user_ids(session, threshold)
    finally:
        delivery_module.UserAdminRepository = original

    assert result == [admin.id]


@pytest.mark.asyncio
async def test_deliver_threshold_breach_skips_when_in_app_disabled() -> None:
    threshold = MagicMock(spec=Threshold)
    threshold.notify_in_app = False
    event = MagicMock(spec=ThresholdEvent)

    count = await deliver_threshold_breach_notifications(
        MagicMock(),
        threshold=threshold,
        event=event,
        current_value="100",
    )
    assert count == 0


@pytest.mark.asyncio
async def test_threshold_evaluator_skips_when_unacknowledged_exists() -> None:
    threshold_id = uuid4()
    org_id = uuid4()
    threshold = MagicMock(spec=Threshold)
    threshold.id = threshold_id
    threshold.organization_id = org_id
    threshold.active = True

    evaluator = ThresholdEvaluator(MagicMock())
    evaluator._thresholds = MagicMock()
    evaluator._thresholds.list_by_organization = AsyncMock(return_value=[threshold])
    evaluator._events = MagicMock()
    evaluator._events.has_unacknowledged = AsyncMock(return_value=True)
    evaluator._dashboard = MagicMock()
    evaluator._dashboard.get_threshold_current_value = AsyncMock()

    created = await evaluator.evaluate_organization(org_id)

    assert created == 0
    evaluator._dashboard.get_threshold_current_value.assert_not_called()


@pytest.mark.asyncio
async def test_threshold_evaluator_creates_notifications_on_breach() -> None:
    org_id = uuid4()
    threshold = MagicMock(spec=Threshold)
    threshold.id = uuid4()
    threshold.organization_id = org_id
    threshold.active = True
    threshold.limit_value = Decimal("100")
    threshold.threshold_type = "token_count"
    threshold.severity = "warning"
    threshold.name = "Token cap"
    threshold.team_id = None
    threshold.notify_in_app = True

    event = MagicMock(spec=ThresholdEvent)
    event.id = uuid4()
    event.message = "breach"

    evaluator = ThresholdEvaluator(MagicMock())
    evaluator._thresholds = MagicMock()
    evaluator._thresholds.list_by_organization = AsyncMock(return_value=[threshold])
    evaluator._events = MagicMock()
    evaluator._events.has_unacknowledged = AsyncMock(return_value=False)
    evaluator._events.create = AsyncMock(return_value=event)
    evaluator._dashboard = MagicMock()
    evaluator._dashboard.get_threshold_current_value = AsyncMock(return_value=Decimal("150"))
    evaluator._evaluate_threshold = AsyncMock(return_value=2)

    created = await evaluator.evaluate_organization(org_id)
    assert created == 2


@pytest.mark.asyncio
async def test_notification_service_mark_all_read() -> None:
    user = MagicMock()
    user.id = uuid4()
    user.organization_id = uuid4()

    service = NotificationService(MagicMock())
    service._repo = MagicMock()
    service._repo.mark_all_read = AsyncMock(return_value=3)
    service._session = MagicMock()
    service._session.commit = AsyncMock()

    result = await service.mark_all_read(user)

    assert result.marked_read == 3
    service._session.commit.assert_awaited_once()
