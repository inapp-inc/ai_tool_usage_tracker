"""Audit log query and export."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.repository import AuditLogRepository
from app.audit.schemas import (
    AuditLogEntryResponse,
    AuditLogExportRequest,
    AuditLogListResponse,
    PaginationMeta,
)
from app.models.audit import AuditLog
from app.models.auth import User

READ_ROLES = frozenset({"super_admin", "auditor"})


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AuditLogRepository(session)

    def ensure_read_access(self, user: User) -> None:
        if user.role not in READ_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

    async def list_logs(
        self,
        user: User,
        *,
        from_dt: datetime | None,
        to_dt: datetime | None,
        actor_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        q: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> AuditLogListResponse:
        self.ensure_read_access(user)
        cursor_dt = datetime.fromisoformat(cursor.replace("Z", "+00:00")) if cursor else None
        rows = await self._repo.list_entries(
            user.organization_id,
            from_dt=from_dt,
            to_dt=to_dt,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            q=q,
            limit=limit,
            cursor=cursor_dt,
        )
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = page[-1].created_at.isoformat() if has_more and page else None
        return AuditLogListResponse(
            data=[self._to_response(row) for row in page],
            meta=PaginationMeta(limit=limit, has_more=has_more, next_cursor=next_cursor),
        )

    async def export_csv(self, user: User, body: AuditLogExportRequest) -> Response:
        self.ensure_read_access(user)
        rows = await self._repo.list_entries(
            user.organization_id,
            from_dt=body.from_dt,
            to_dt=body.to_dt,
            actor_id=body.actor_id,
            action=body.action,
            resource_type=body.resource_type,
            q=body.q,
            limit=5000,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Time",
                "Category",
                "Action",
                "Description",
                "Performed By",
                "Email",
                "Role",
                "Target",
                "Outcome",
                "IP",
                "Correlation ID",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.created_at.astimezone(UTC).isoformat(),
                    row.resource_type,
                    row.action,
                    row.description,
                    row.actor_display_name or "",
                    row.actor_email or "",
                    row.actor_role or "",
                    row.resource_name or "",
                    row.outcome,
                    row.source_ip or "",
                    row.correlation_id or "",
                ]
            )
        filename = f"audit-log-{datetime.now(UTC).date().isoformat()}.csv"
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @staticmethod
    def _to_response(row: AuditLog) -> AuditLogEntryResponse:
        return AuditLogEntryResponse(
            id=row.id,
            actor_id=row.actor_id,
            actor_email=row.actor_email,
            actor_display_name=row.actor_display_name,
            actor_role=row.actor_role,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            resource_name=row.resource_name,
            description=row.description,
            outcome=row.outcome,  # type: ignore[arg-type]
            source_ip=row.source_ip,
            correlation_id=row.correlation_id,
            created_at=row.created_at,
        )
