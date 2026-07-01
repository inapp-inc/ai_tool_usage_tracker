"""RBAC scope resolution for dashboard queries."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.org_scope import OperatingOrgScope
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository

ORG_WIDE_ROLES = frozenset({"super_admin", "org_admin"})


@dataclass(frozen=True)
class DashboardScope:
    organization_id: UUID
    allowed_team_ids: list[UUID] | None
    user_id: UUID | None
    user_email: str | None


async def resolve_dashboard_scope(
    session: AsyncSession,
    user: User,
    *,
    team_id: UUID | None = None,
    org_scope: OperatingOrgScope | None = None,
) -> DashboardScope:
    """Resolve which usage rows the caller may see."""
    if org_scope is not None and org_scope.is_super_admin and org_scope.single_org_id is not None:
        org_id = org_scope.single_org_id
    else:
        org_id = user.organization_id

    memberships = TeamMembershipRepository(session)
    teams = TeamRepository(session)

    if user.role_name in ORG_WIDE_ROLES:
        if team_id is not None:
            if user.role_name == "super_admin":
                team = await teams.get_by_id_unscoped(team_id)
            else:
                team = await teams.get_by_id(team_id, org_id)
            if team is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
            org_id = team.organization_id
            return DashboardScope(
                organization_id=org_id,
                allowed_team_ids=[team_id],
                user_id=None,
                user_email=None,
            )
        return DashboardScope(
            organization_id=org_id,
            allowed_team_ids=None,
            user_id=None,
            user_email=None,
        )

    if user.role_name == "team_admin":
        team_ids = await memberships.active_team_ids_for_user(user.id)
        if not team_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No team access configured.",
            )
        if team_id is not None:
            if team_id not in team_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this team.",
                )
            return DashboardScope(
                organization_id=org_id,
                allowed_team_ids=[team_id],
                user_id=None,
                user_email=None,
            )
        return DashboardScope(
            organization_id=org_id,
            allowed_team_ids=team_ids,
            user_id=None,
            user_email=None,
        )

    # team_member — own usage only
    if team_id is not None:
        member_team_ids = await memberships.active_team_ids_for_user(user.id)
        if team_id not in member_team_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this team.",
            )
    return DashboardScope(
        organization_id=org_id,
        allowed_team_ids=[team_id] if team_id is not None else None,
        user_id=user.id,
        user_email=user.email,
    )
