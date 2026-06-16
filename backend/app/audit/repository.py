"""Audit log data access."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_entries(
        self,
        organization_id: UUID,
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
        actor_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        q: str | None = None,
        limit: int = 100,
        cursor: datetime | None = None,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).where(AuditLog.organization_id == organization_id)

        if from_dt is not None:
            stmt = stmt.where(AuditLog.created_at >= from_dt)
        if to_dt is not None:
            stmt = stmt.where(AuditLog.created_at <= to_dt)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(
                    AuditLog.description.ilike(pattern),
                    AuditLog.actor_email.ilike(pattern),
                    AuditLog.actor_display_name.ilike(pattern),
                    AuditLog.resource_name.ilike(pattern),
                    AuditLog.action.ilike(pattern),
                )
            )
        if cursor is not None:
            stmt = stmt.where(AuditLog.created_at < cursor)

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit + 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
