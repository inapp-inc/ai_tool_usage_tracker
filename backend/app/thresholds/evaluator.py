"""Evaluate active thresholds and fire in-app notifications on breach."""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.service import DashboardService
from app.models.notifications import Threshold
from app.notifications.delivery import deliver_threshold_breach_notifications
from app.thresholds.repository import ThresholdEventRepository, ThresholdRepository

logger = logging.getLogger(__name__)


class ThresholdEvaluator:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._thresholds = ThresholdRepository(session)
        self._events = ThresholdEventRepository(session)
        self._dashboard = DashboardService(session)

    async def evaluate_organization(self, organization_id: UUID) -> int:
        """Evaluate all active thresholds for an org. Returns notifications created."""
        rows = await self._thresholds.list_by_organization(organization_id)
        active = [row for row in rows if row.active]
        created = 0
        for threshold in active:
            created += await self._evaluate_threshold(threshold)
        return created

    async def evaluate_threshold(self, threshold: Threshold) -> int:
        """Evaluate a single threshold (e.g. immediately after create/update)."""
        if not threshold.active:
            return 0
        return await self._evaluate_threshold(threshold)

    async def _evaluate_threshold(self, threshold: Threshold) -> int:
        if await self._events.has_unacknowledged(threshold.id, threshold.organization_id):
            return 0

        current = await self._dashboard.get_threshold_current_value(
            threshold.organization_id,
            threshold,
        )
        if not self._is_breach(threshold, current):
            return 0

        message = self._build_message(threshold, current)
        event = await self._events.create(
            organization_id=threshold.organization_id,
            threshold_id=threshold.id,
            severity=threshold.severity,
            message=message,
            team_id=threshold.team_id,
        )
        count = await deliver_threshold_breach_notifications(
            self._session,
            threshold=threshold,
            event=event,
            current_value=str(current),
        )
        logger.info(
            "Threshold breach | org=%s threshold=%s notifications=%s",
            threshold.organization_id,
            threshold.id,
            count,
        )
        return count

    @staticmethod
    def _is_breach(threshold: Threshold, current: Decimal) -> bool:
        return current >= threshold.limit_value

    @staticmethod
    def _build_message(threshold: Threshold, current: Decimal) -> str:
        if threshold.threshold_type == "cost_amount":
            return (
                f"Cost ${current:.2f} reached the limit of ${threshold.limit_value:.2f} "
                f"for rule \"{threshold.name}\"."
            )
        if threshold.threshold_type == "package_utilization_pct":
            return (
                f"Budget usage {current:.1f}% reached the limit of {threshold.limit_value}% "
                f"for rule \"{threshold.name}\"."
            )
        return (
            f"Token usage {int(current):,} reached the limit of {int(threshold.limit_value):,} "
            f"for rule \"{threshold.name}\"."
        )
