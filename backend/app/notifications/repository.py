"""In-app notification data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notifications import InAppNotification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        *,
        unread_only: bool = False,
        limit: int = 20,
    ) -> list[InAppNotification]:
        query = (
            select(InAppNotification)
            .where(
                InAppNotification.user_id == user_id,
                InAppNotification.organization_id == organization_id,
            )
            .order_by(InAppNotification.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            query = query.where(InAppNotification.read.is_(False))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count_unread(self, user_id: UUID, organization_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(InAppNotification.id)).where(
                InAppNotification.user_id == user_id,
                InAppNotification.organization_id == organization_id,
                InAppNotification.read.is_(False),
            )
        )
        return int(result.scalar_one())

    async def get_by_id(
        self,
        notification_id: UUID,
        user_id: UUID,
        organization_id: UUID,
    ) -> InAppNotification | None:
        result = await self._session.execute(
            select(InAppNotification).where(
                InAppNotification.id == notification_id,
                InAppNotification.user_id == user_id,
                InAppNotification.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_read(self, row: InAppNotification) -> None:
        if row.read:
            return
        row.read = True
        row.read_at = datetime.now(UTC)
        await self._session.flush()

    async def mark_all_read(self, user_id: UUID, organization_id: UUID) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            update(InAppNotification)
            .where(
                InAppNotification.user_id == user_id,
                InAppNotification.organization_id == organization_id,
                InAppNotification.read.is_(False),
            )
            .values(read=True, read_at=now)
        )
        await self._session.flush()
        return int(result.rowcount or 0)

    async def create(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str | None,
        payload: dict,
        severity: str | None = None,
        threshold_event_id: UUID | None = None,
    ) -> InAppNotification:
        row = InAppNotification(
            organization_id=organization_id,
            user_id=user_id,
            notification_type=notification_type,
            severity=severity,
            title=title,
            body=body,
            payload=payload,
            threshold_event_id=threshold_event_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row
