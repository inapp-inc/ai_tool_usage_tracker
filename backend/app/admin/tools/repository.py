"""Tools data access."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.models.admin import Tool


class ToolRepository:
    """CRUD for admin.tools."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_tools(
        self,
        organization_id: uuid.UUID,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Tool], str | None]:
        stmt = select(Tool).where(Tool.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Tool.active == active)

        if cursor:
            try:
                parts = decode_cursor(cursor)
                cursor_name = parts["name"]
                cursor_id = uuid.UUID(parts["id"])
            except (CursorError, KeyError, ValueError) as exc:
                raise CursorError("Invalid pagination cursor") from exc
            stmt = stmt.where(
                tuple_(Tool.name, Tool.id) > tuple_(cursor_name, cursor_id)
            )

        stmt = stmt.order_by(Tool.name.asc(), Tool.id.asc()).limit(limit + 1)
        rows = list((await self._session.scalars(stmt)).all())

        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = encode_cursor(name=last.name, id=str(last.id))
            rows = rows[:limit]

        return rows, next_cursor

    async def get_by_id(
        self, organization_id: uuid.UUID, tool_id: uuid.UUID
    ) -> Tool | None:
        stmt = select(Tool).where(
            Tool.organization_id == organization_id,
            Tool.id == tool_id,
        )
        return await self._session.scalar(stmt)

    async def get_by_name(
        self, organization_id: uuid.UUID, name: str
    ) -> Tool | None:
        stmt = select(Tool).where(
            Tool.organization_id == organization_id,
            Tool.name == name,
        )
        return await self._session.scalar(stmt)

    async def add(self, tool: Tool) -> Tool:
        self._session.add(tool)
        await self._session.flush()
        return tool

    async def save(self, tool: Tool) -> Tool:
        await self._session.flush()
        return tool
