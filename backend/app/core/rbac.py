"""Role-based access helpers (TASK-PLT-002 subset)."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.db.session import get_session
from app.models.admin import TeamMembership


async def require_super_admin(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Allow Super Admin only."""
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return current_user


async def require_team_admin_or_above(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Allow Super Admin or Team Admin. All other roles get 403."""
    if current_user.role not in ("super_admin", "team_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return current_user


async def require_finance_viewer_access(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Allow Super Admin or Finance Viewer. All other roles get 403.

    Finance Viewer is a parallel role to Team Admin — not a sub-role.
    Use this guard on read-only financial/reporting endpoints.
    """
    if current_user.role not in ("super_admin", "finance_viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    return current_user


async def get_managed_team_ids(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[uuid.UUID]:
    """
    Returns the team IDs the current user may administer.
    - Super Admin: returns [] (empty = no restriction, caller interprets as 'all teams').
    - Team Admin: returns the UUIDs of teams they are an active member of.
    """
    if current_user.role == "super_admin":
        return []

    stmt = select(TeamMembership.team_id).where(
        TeamMembership.user_id == current_user.id,
        TeamMembership.organization_id == current_user.organization_id,
        TeamMembership.removed_at.is_(None),
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
