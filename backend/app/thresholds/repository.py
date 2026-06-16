"""Threshold data access."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import Threshold, ThresholdEvent


class ThresholdRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(self, organization_id: UUID) -> list[Threshold]:
        result = await self._session.execute(
            select(Threshold)
            .where(Threshold.organization_id == organization_id)
            .order_by(Threshold.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, threshold_id: UUID, organization_id: UUID) -> Threshold | None:
        result = await self._session.execute(
            select(Threshold).where(
                Threshold.id == threshold_id,
                Threshold.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        threshold_type: str,
        scope: str,
        limit_value: Decimal,
        severity: str,
        notify_email: bool,
        notify_in_app: bool,
        webhook_url: str | None,
        email_recipients: list[str],
        active: bool = True,
        tool_id: UUID | None = None,
        team_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> Threshold:
        row = Threshold(
            organization_id=organization_id,
            name=name,
            threshold_type=threshold_type,
            scope=scope,
            tool_id=tool_id,
            team_id=team_id,
            user_id=user_id,
            limit_value=limit_value,
            severity=severity,
            notify_email=notify_email,
            notify_in_app=notify_in_app,
            webhook_url=webhook_url,
            email_recipients=email_recipients,
            active=active,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete(self, row: Threshold) -> None:
        await self._session.delete(row)
        await self._session.flush()


class ThresholdEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(self, organization_id: UUID) -> list[ThresholdEvent]:
        result = await self._session.execute(
            select(ThresholdEvent)
            .where(ThresholdEvent.organization_id == organization_id)
            .order_by(ThresholdEvent.triggered_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, event_id: UUID, organization_id: UUID) -> ThresholdEvent | None:
        result = await self._session.execute(
            select(ThresholdEvent).where(
                ThresholdEvent.id == event_id,
                ThresholdEvent.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def stats_for_thresholds(
        self,
        organization_id: UUID,
        threshold_ids: list[UUID],
    ) -> dict[UUID, tuple[int, object]]:
        if not threshold_ids:
            return {}

        result = await self._session.execute(
            select(
                ThresholdEvent.threshold_id,
                func.count(ThresholdEvent.id),
                func.max(ThresholdEvent.triggered_at),
            )
            .where(
                ThresholdEvent.organization_id == organization_id,
                ThresholdEvent.threshold_id.in_(threshold_ids),
            )
            .group_by(ThresholdEvent.threshold_id)
        )
        return {
            threshold_id: (int(count), last_triggered)
            for threshold_id, count, last_triggered in result.all()
        }
