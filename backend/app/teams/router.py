"""Teams REST API — OpenAPI /teams/*."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.teams.schemas import (
    TeamCreateRequest,
    TeamListResponse,
    TeamMemberAddRequest,
    TeamMemberListResponse,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.teams.service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])

WRITE_ROLES = frozenset({"super_admin"})


def get_team_service(session: AsyncSession = Depends(get_session)) -> TeamService:
    return TeamService(session)


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


@router.get("", response_model=TeamListResponse)
async def list_teams(
    active: bool | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamListResponse:
    return await service.list_teams(current_user, active=active)


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    body: TeamCreateRequest,
    current_user: User = Depends(require_super_admin),
    service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    return await service.create_team(current_user, body)


@router.get("/{team_id}/members", response_model=TeamMemberListResponse)
async def list_team_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamMemberListResponse:
    return await service.list_team_members(current_user, team_id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: UUID,
    body: TeamMemberAddRequest,
    current_user: User = Depends(require_super_admin),
    service: TeamService = Depends(get_team_service),
) -> TeamMemberResponse:
    return await service.add_team_member(current_user, team_id, body.user_id)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(require_super_admin),
    service: TeamService = Depends(get_team_service),
) -> None:
    await service.remove_team_member(current_user, team_id, user_id)


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    return await service.get_team(current_user, team_id)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    body: TeamUpdateRequest,
    current_user: User = Depends(require_super_admin),
    service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    return await service.update_team(current_user, team_id, body)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(require_super_admin),
    service: TeamService = Depends(get_team_service),
) -> None:
    await service.delete_team(current_user, team_id)
