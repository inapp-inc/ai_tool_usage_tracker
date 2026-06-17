"""Organization user admin — list, invite, update, deactivate."""

import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repositories import UserRepository
from app.core.security import hash_password
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository
from app.users.repository import UserAdminRepository
from app.users.schemas import (
    PaginationMeta,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserTeamSummary,
    UserUpdateRequest,
)

ADMIN_ROLES = frozenset({"super_admin", "team_admin"})


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserAdminRepository(session)
        self._auth_users = UserRepository(session)
        self._memberships = TeamMembershipRepository(session)
        self._teams = TeamRepository(session)

    async def list_users(
        self,
        organization_id: UUID,
        team_ids: list[UUID] | None = None,
    ) -> UserListResponse:
        rows = await self._users.list_by_organization(organization_id)

        if team_ids is not None:
            member_user_ids: set[UUID] = set()
            for team_id in team_ids:
                active = await self._memberships.list_active_for_team(team_id)
                for m in active:
                    member_user_ids.add(m.user_id)
            rows = [r for r in rows if r.id in member_user_ids]

        summaries = await self._memberships.list_team_summaries_for_users(
            organization_id,
            [row.id for row in rows],
        )
        return UserListResponse(
            data=[self._to_response(row, summaries.get(row.id, [])) for row in rows],
            meta=PaginationMeta(has_more=False),
        )

    async def get_user(self, organization_id: UUID, user_id: UUID) -> UserResponse:
        user = await self._require_user(organization_id, user_id)
        teams = await self._memberships.list_active_teams_for_user(user_id)
        return self._to_response(
            user,
            [(team, membership.joined_at) for membership, team in teams],
        )

    async def create_user(
        self,
        organization_id: UUID,
        body: UserCreateRequest,
    ) -> UserResponse:
        existing = await self._users.get_by_email(organization_id, body.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists in the organization.",
            )

        await self._validate_team_ids(organization_id, body.team_ids)

        password = body.password or secrets.token_urlsafe(16)
        user = await self._auth_users.create(
            organization_id=organization_id,
            email=body.email,
            password_hash=hash_password(password),
            display_name=body.display_name.strip() if body.display_name else None,
            role=body.role,
        )

        for team_id in body.team_ids:
            await self._memberships.add(
                organization_id=organization_id,
                team_id=team_id,
                user_id=user.id,
            )

        await self._session.commit()
        await self._session.refresh(user)
        return await self.get_user(organization_id, user.id)

    async def update_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        body: UserUpdateRequest,
    ) -> UserResponse:
        user = await self._require_user(organization_id, user_id)
        updates = body.model_fields_set

        if "display_name" in updates:
            user.display_name = body.display_name.strip() if body.display_name else None

        if "role" in updates and body.role is not None:
            user.role = body.role

        if "active" in updates and body.active is not None:
            user.active = body.active

        if "team_ids" in updates and body.team_ids is not None:
            await self._validate_team_ids(organization_id, body.team_ids)
            await self._memberships.sync_user_teams(
                organization_id=organization_id,
                user_id=user.id,
                team_ids=body.team_ids,
            )

        await self._session.commit()
        await self._session.refresh(user)
        return await self.get_user(organization_id, user.id)

    async def deactivate_user(self, organization_id: UUID, user_id: UUID) -> None:
        user = await self._require_user(organization_id, user_id)
        user.active = False
        await self._session.commit()

    async def _require_user(self, organization_id: UUID, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id, organization_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def _validate_team_ids(
        self,
        organization_id: UUID,
        team_ids: list[UUID],
    ) -> None:
        for team_id in team_ids:
            team = await self._teams.get_by_id(team_id, organization_id)
            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Team not found: {team_id}",
                )

    @staticmethod
    def _to_response(
        user: User,
        team_rows: list[tuple],
    ) -> UserResponse:
        teams = [
            UserTeamSummary(
                id=team.id,
                name=team.name,
                joined_at=joined_at,
            )
            for team, joined_at in team_rows
        ]
        return UserResponse(
            id=user.id,
            organization_id=user.organization_id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,  # type: ignore[arg-type]
            active=user.active,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            teams=teams,
        )
