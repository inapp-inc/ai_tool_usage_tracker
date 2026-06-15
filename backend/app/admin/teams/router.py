"""Teams API routes (FR-ADM-002)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.teams.schemas import (
    TeamCreateRequest,
    TeamListResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.admin.teams.service import TeamConflictError, TeamNotFoundError, TeamService
from app.core.pagination import CursorError
from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get(
    "",
    response_model=TeamListResponse,
    summary="List teams",
    operation_id="listTeams",
)
async def list_teams(
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamListResponse:
    service = TeamService(session)
    try:
        return await service.list_teams(
            current_user, active=active, limit=limit, cursor=cursor
        )
    except CursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create team",
    operation_id="createTeam",
)
async def create_team(
    body: TeamCreateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    service = TeamService(session)
    try:
        return await service.create_team(current_user, body)
    except TeamConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team with this name already exists in your organization.",
        ) from exc


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team by ID",
    operation_id="getTeam",
)
async def get_team(
    team_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    service = TeamService(session)
    try:
        return await service.get_team(current_user, team_id)
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found.",
        ) from exc


@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    operation_id="updateTeam",
)
async def update_team(
    team_id: uuid.UUID,
    body: TeamUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> TeamResponse:
    service = TeamService(session)
    try:
        return await service.update_team(current_user, team_id, body)
    except TeamNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found.",
        ) from exc
    except TeamConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A team with this name already exists in your organization.",
        ) from exc
