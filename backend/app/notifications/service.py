"""In-app notification business logic."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.notifications import InAppNotification
from app.notifications.repository import NotificationRepository
from app.notifications.schemas import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def list_notifications(
        self,
        user: User,
        *,
        unread_only: bool = False,
        limit: int = 20,
    ) -> NotificationListResponse:
        rows = await self._repo.list_for_user(
            user.id,
            user.organization_id,
            unread_only=unread_only,
            limit=min(max(limit, 1), 50),
        )
        return NotificationListResponse(data=[self._to_response(row) for row in rows])

    async def unread_count(self, user: User) -> UnreadCountResponse:
        count = await self._repo.count_unread(user.id, user.organization_id)
        return UnreadCountResponse(unread_count=count)

    async def mark_read(
        self,
        user: User,
        notification_id: UUID,
    ) -> NotificationResponse:
        row = await self._repo.get_by_id(notification_id, user.id, user.organization_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found.",
            )
        await self._repo.mark_read(row)
        await self._session.commit()
        await self._session.refresh(row)
        return self._to_response(row)

    async def mark_all_read(self, user: User) -> MarkAllReadResponse:
        marked = await self._repo.mark_all_read(user.id, user.organization_id)
        await self._session.commit()
        return MarkAllReadResponse(marked_read=marked)

    @staticmethod
    def _to_response(row: InAppNotification) -> NotificationResponse:
        return NotificationResponse(
            id=row.id,
            notification_type=row.notification_type,
            severity=row.severity,
            title=row.title,
            body=row.body,
            payload=row.payload or {},
            read=row.read,
            read_at=row.read_at,
            created_at=row.created_at,
        )
