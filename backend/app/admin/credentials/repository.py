"""Credentials data access."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.models.admin import Credential


class CredentialRepository:
    """CRUD for admin.credentials."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_credentials(
        self,
        organization_id: uuid.UUID,
        *,
        tool_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Credential], str | None]:
        stmt = select(Credential).where(
            Credential.organization_id == organization_id,
            Credential.deleted_at.is_(None),
        )
        if tool_id is not None:
            stmt = stmt.where(Credential.tool_id == tool_id)
        if team_id is not None:
            stmt = stmt.where(Credential.team_id == team_id)

        if cursor:
            try:
                parts = decode_cursor(cursor)
                cursor_created = datetime.fromisoformat(
                    parts["created_at"].replace("Z", "+00:00")
                )
                cursor_id = uuid.UUID(parts["id"])
            except (CursorError, KeyError, ValueError) as exc:
                raise CursorError("Invalid pagination cursor") from exc
            stmt = stmt.where(
                tuple_(Credential.created_at, Credential.id)
                < tuple_(cursor_created, cursor_id)
            )

        stmt = stmt.order_by(
            Credential.created_at.desc(), Credential.id.desc()
        ).limit(limit + 1)
        rows = list((await self._session.scalars(stmt)).all())

        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = encode_cursor(
                created_at=last.created_at.isoformat(),
                id=str(last.id),
            )
            rows = rows[:limit]

        return rows, next_cursor

    async def get_by_id(
        self, organization_id: uuid.UUID, credential_id: uuid.UUID
    ) -> Credential | None:
        stmt = select(Credential).where(
            Credential.organization_id == organization_id,
            Credential.id == credential_id,
            Credential.deleted_at.is_(None),
        )
        return await self._session.scalar(stmt)

    async def get_primary_for_tool(
        self, organization_id: uuid.UUID, tool_id: uuid.UUID
    ) -> Credential | None:
        stmt = (
            select(Credential)
            .where(
                Credential.organization_id == organization_id,
                Credential.tool_id == tool_id,
                Credential.deleted_at.is_(None),
                Credential.status == "active",
            )
            .order_by(Credential.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def add(self, credential: Credential) -> Credential:
        self._session.add(credential)
        await self._session.flush()
        return credential

    async def save(self, credential: Credential) -> Credential:
        await self._session.flush()
        return credential
