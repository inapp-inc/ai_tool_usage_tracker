"""Centralized RBAC dependency guards.

Usage in routers:
    current_user: User = Depends(require_team_admin_or_above)
    current_user: User = Depends(require_finance_viewer_access)
    current_user: User = Depends(require_auditor_access)
    managed_team_ids: list[uuid.UUID] = Depends(get_managed_team_ids)
"""

import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.teams.membership_repository import TeamMembershipRepository


async def require_team_admin_or_above(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow super_admin and team_admin. Reject all others with 403."""
    if current_user.role not in ("super_admin", "team_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


async def get_managed_team_ids(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[uuid.UUID]:
    """Return team IDs this user manages.

    - super_admin: returns [] (caller interprets as "all teams")
    - team_admin: returns UUIDs of active TeamMembership rows for this user
    """
    if current_user.role == "super_admin":
        return []
    repo = TeamMembershipRepository(session)
    return await repo.active_team_ids_for_user(current_user.id)


async def require_finance_viewer_access(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow super_admin and finance_viewer. Reject all others with 403."""
    if current_user.role not in ("super_admin", "finance_viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user


async def require_auditor_access(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow super_admin and auditor. Reject all others with 403."""
    if current_user.role not in ("super_admin", "auditor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return current_user
