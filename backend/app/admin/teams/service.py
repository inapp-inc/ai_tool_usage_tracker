"""Team management business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.teams.repository import TeamRepository
from app.admin.teams.schemas import (
    PaginationMeta,
    TeamCreateRequest,
    TeamListResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.auth.service import AuthenticatedUser
from app.core.pagination import CursorError
from app.models.admin import Team


class TeamConflictError(Exception):
    """Team name already exists."""


class TeamNotFoundError(Exception):
    """Team not found."""


class TeamService:
    """Team CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)

    async def _to_response(self, team: Team) -> TeamResponse:
        member_count = await self._teams.count_members(team.id)
        return TeamResponse(
            id=team.id,
            organization_id=team.organization_id,
            name=team.name,
            description=team.description,
            active=team.active,
            member_count=member_count,
            settings=team.settings or {},
            created_at=team.created_at,
        )

    async def list_teams(
        self,
        user: AuthenticatedUser,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> TeamListResponse:
        rows, next_cursor = await self._teams.list_teams(
            user.organization_id,
            active=active,
            limit=limit,
            cursor=cursor,
        )
        data = [await self._to_response(row) for row in rows]
        return TeamListResponse(
            data=data,
            meta=PaginationMeta(
                limit=limit,
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            ),
        )

    async def get_team(
        self, user: AuthenticatedUser, team_id: uuid.UUID
    ) -> TeamResponse:
        team = await self._teams.get_by_id(user.organization_id, team_id)
        if team is None:
            raise TeamNotFoundError
        return await self._to_response(team)

    async def create_team(
        self, user: AuthenticatedUser, body: TeamCreateRequest
    ) -> TeamResponse:
        team = Team(
            organization_id=user.organization_id,
            name=body.name.strip(),
            description=body.description,
            settings=body.settings,
        )
        try:
            await self._teams.add(team)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise TeamConflictError from exc
        await self._session.refresh(team)
        return await self._to_response(team)

    async def update_team(
        self,
        user: AuthenticatedUser,
        team_id: uuid.UUID,
        body: TeamUpdateRequest,
    ) -> TeamResponse:
        team = await self._teams.get_by_id(user.organization_id, team_id)
        if team is None:
            raise TeamNotFoundError

        updates = body.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        if "settings" in updates and updates["settings"] is not None:
            merged = {**(team.settings or {}), **updates["settings"]}
            updates["settings"] = merged

        for field, value in updates.items():
            setattr(team, field, value)
        team.updated_at = datetime.now(UTC)

        try:
            await self._teams.save(team)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise TeamConflictError from exc
        await self._session.refresh(team)
        return await self._to_response(team)
