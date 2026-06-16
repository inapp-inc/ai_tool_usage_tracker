"""Append-only audit event recorder."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.descriptions import build_description
from app.models.audit import AuditLog
from app.models.auth import User

logger = logging.getLogger(__name__)


class AuditRecorder:
    """Records immutable audit rows; failures are logged and do not raise."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        *,
        organization_id: UUID,
        actor: User | None,
        action: str,
        resource_type: str,
        resource_id: UUID | str | None = None,
        resource_name: str | None = None,
        description: str | None = None,
        outcome: str = "success",
        source_ip: str | None = None,
        correlation_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            row = AuditLog(
                organization_id=organization_id,
                actor_id=actor.id if actor else None,
                actor_email=actor.email if actor else None,
                actor_display_name=actor.display_name if actor else None,
                actor_role=actor.role if actor else None,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id is not None else None,
                resource_name=resource_name,
                description=description
                or build_description(action, resource_name=resource_name),
                outcome=outcome,
                source_ip=source_ip,
                correlation_id=correlation_id,
                metadata_json=metadata or {},
            )
            self._session.add(row)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            logger.exception("Failed to write audit log for action=%s", action)
