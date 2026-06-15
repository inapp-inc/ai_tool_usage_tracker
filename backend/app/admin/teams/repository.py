"""Teams data access."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import CursorError, decode_cursor, encode_cursor
from app.models.admin import Team, TeamMembership


class TeamRepository:
    """CRUD for admin.teams."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_teams(
        self,
        organization_id: uuid.UUID,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Team], str | None]:
        stmt = select(Team).where(Team.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Team.active == active)

        if cursor:
            try:
                parts = decode_cursor(cursor)
                cursor_name = parts["name"]
                cursor_id = uuid.UUID(parts["id"])
            except (CursorError, KeyError, ValueError) as exc:
                raise CursorError("Invalid pagination cursor") from exc
            stmt = stmt.where(
                tuple_(Team.name, Team.id) > tuple_(cursor_name, cursor_id)
            )

        stmt = stmt.order_by(Team.name.asc(), Team.id.asc()).limit(limit + 1)
        rows = list((await self._session.scalars(stmt)).all())

        next_cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            next_cursor = encode_cursor(name=last.name, id=str(last.id))
            rows = rows[:limit]

        return rows, next_cursor

    async def get_by_id(
        self, organization_id: uuid.UUID, team_id: uuid.UUID
    ) -> Team | None:
        stmt = select(Team).where(
            Team.organization_id == organization_id,
            Team.id == team_id,
        )
        return await self._session.scalar(stmt)

    async def count_members(self, team_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(TeamMembership)
            .where(
                TeamMembership.team_id == team_id,
                TeamMembership.removed_at.is_(None),
            )
        )
        return int(await self._session.scalar(stmt) or 0)

    async def add(self, team: Team) -> Team:
        self._session.add(team)
        await self._session.flush()
        return team

    async def save(self, team: Team) -> Team:
        await self._session.flush()
        return team
