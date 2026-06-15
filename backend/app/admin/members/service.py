"""Member management business logic."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.members.schemas import (
    MemberInviteRequest,
    MemberListResponse,
    MemberResponse,
    MemberTeamRef,
    MemberUpdateRequest,
)
from app.core.security import hash_password, normalize_email
from app.models.admin import Team, TeamMembership
from app.models.auth import User


ROLE_MAP_TO_BACKEND = {
    "super_admin": "super_admin",
    "team_admin": "team_admin",
    "finance_viewer": "finance_viewer",
    "team_member": "team_member",
    "auditor": "auditor",
}


class MemberNotFoundError(Exception):
    """Member not found."""


class MemberConflictError(Exception):
    """Member email already exists."""


class MemberService:
    """Organization member operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _teams_for_user(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[MemberTeamRef]:
        stmt = (
            select(Team.id, Team.name)
            .join(TeamMembership, TeamMembership.team_id == Team.id)
            .where(
                TeamMembership.organization_id == organization_id,
                TeamMembership.user_id == user_id,
                TeamMembership.removed_at.is_(None),
                Team.active.is_(True),
            )
        )
        rows = (await self._session.execute(stmt)).all()
        return [MemberTeamRef(id=row.id, name=row.name) for row in rows]

    async def _to_response(
        self, user: User, organization_id: uuid.UUID
    ) -> MemberResponse:
        teams = await self._teams_for_user(organization_id, user.id)
        return MemberResponse(
            id=user.id,
            name=user.display_name or user.email.split("@")[0],
            email=user.email,
            platform_role=user.role,
            teams=teams,
            status="active" if user.active else "inactive",
            last_active_at=user.last_login_at,
            created_at=user.created_at,
        )

    async def list_members(
        self, organization_id: uuid.UUID, *, team_id: uuid.UUID | None = None
    ) -> MemberListResponse:
        stmt = select(User).where(User.organization_id == organization_id)
        if team_id is not None:
            stmt = stmt.join(
                TeamMembership,
                TeamMembership.user_id == User.id,
            ).where(
                TeamMembership.team_id == team_id,
                TeamMembership.removed_at.is_(None),
            )
        stmt = stmt.order_by(User.display_name.asc(), User.email.asc())
        users = list((await self._session.scalars(stmt)).unique().all())
        data = [await self._to_response(user, organization_id) for user in users]
        return MemberListResponse(data=data)

    async def invite_member(
        self, organization_id: uuid.UUID, body: MemberInviteRequest
    ) -> MemberResponse:
        email = normalize_email(str(body.email))
        existing = await self._session.scalar(
            select(User).where(User.email == email)
        )
        if existing is not None:
            raise MemberConflictError

        role = ROLE_MAP_TO_BACKEND.get(body.platform_role, body.platform_role)
        user = User(
            organization_id=organization_id,
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(16)),
            display_name=body.name.strip(),
            role=role,
            active=True,
        )
        self._session.add(user)
        await self._session.flush()

        for team_id in body.team_ids:
            membership = TeamMembership(
                organization_id=organization_id,
                team_id=team_id,
                user_id=user.id,
            )
            self._session.add(membership)

        await self._session.commit()
        await self._session.refresh(user)
        return await self._to_response(user, organization_id)

    async def update_member(
        self,
        organization_id: uuid.UUID,
        member_id: uuid.UUID,
        body: MemberUpdateRequest,
    ) -> MemberResponse:
        user = await self._session.scalar(
            select(User).where(
                User.id == member_id,
                User.organization_id == organization_id,
            )
        )
        if user is None:
            raise MemberNotFoundError

        if body.name is not None:
            user.display_name = body.name.strip()
        if body.platform_role is not None:
            user.role = ROLE_MAP_TO_BACKEND.get(body.platform_role, body.platform_role)
        if body.status is not None:
            user.active = body.status == "active"
        user.updated_at = datetime.now(UTC)

        if body.team_ids is not None:
            existing = list(
                (
                    await self._session.scalars(
                        select(TeamMembership).where(
                            TeamMembership.organization_id == organization_id,
                            TeamMembership.user_id == user.id,
                            TeamMembership.removed_at.is_(None),
                        )
                    )
                ).all()
            )
            desired = set(body.team_ids)
            current = {row.team_id for row in existing}
            for row in existing:
                if row.team_id not in desired:
                    row.removed_at = datetime.now(UTC)
            for team_id in desired - current:
                self._session.add(
                    TeamMembership(
                        organization_id=organization_id,
                        team_id=team_id,
                        user_id=user.id,
                    )
                )

        await self._session.commit()
        await self._session.refresh(user)
        return await self._to_response(user, organization_id)

    async def remove_member(
        self, organization_id: uuid.UUID, member_id: uuid.UUID
    ) -> None:
        user = await self._session.scalar(
            select(User).where(
                User.id == member_id,
                User.organization_id == organization_id,
            )
        )
        if user is None:
            raise MemberNotFoundError
        user.active = False
        user.updated_at = datetime.now(UTC)
        await self._session.commit()
