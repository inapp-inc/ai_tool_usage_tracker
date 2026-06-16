"""My Usage endpoint — returns the caller's team memberships with usage stats."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import AuthenticatedUser
from app.dashboard.service import DashboardService
from app.db.session import get_session
from app.models.admin import Team, TeamMembership

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/me", summary="My team usage", operation_id="getMyUsage")
async def get_my_usage(
    from_value: str | None = Query(default=None, alias="from"),
    to_value: str | None = Query(default=None, alias="to"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return the caller's team memberships with current usage stats for each team.

    Period defaults to the last 30 days if not supplied.
    Any authenticated user may call this endpoint.
    """
    now = datetime.now(UTC)
    if from_value and to_value:
        try:
            from_dt = datetime.fromisoformat(from_value.replace("Z", "+00:00"))
            to_dt = datetime.fromisoformat(to_value.replace("Z", "+00:00"))
        except ValueError:
            from_dt = now - timedelta(days=30)
            to_dt = now
    else:
        from_dt = now - timedelta(days=30)
        to_dt = now

    if from_dt.tzinfo is None:
        from_dt = from_dt.replace(tzinfo=UTC)
    if to_dt.tzinfo is None:
        to_dt = to_dt.replace(tzinfo=UTC)

    membership_stmt = select(TeamMembership.team_id).where(
        TeamMembership.user_id == current_user.id,
        TeamMembership.organization_id == current_user.organization_id,
        TeamMembership.removed_at.is_(None),
    )
    result = await session.execute(membership_stmt)
    my_team_ids: set[uuid.UUID] = set(result.scalars().all())

    teams_by_id: dict[uuid.UUID, str] = {}
    if my_team_ids:
        teams_stmt = select(Team.id, Team.name).where(
            Team.id.in_(my_team_ids),
            Team.organization_id == current_user.organization_id,
        )
        teams_result = await session.execute(teams_stmt)
        teams_by_id = {row.id: row.name for row in teams_result}

    service = DashboardService(session)
    usage_result = await service.get_usage_by_team(
        current_user,
        from_dt=from_dt,
        to_dt=to_dt,
    )
    all_team_usage = usage_result.get("data", [])

    my_teams_usage = [
        row
        for row in all_team_usage
        if uuid.UUID(str(row.get("team_id", ""))) in my_team_ids
    ]

    usage_team_ids = {
        uuid.UUID(str(r.get("team_id", ""))) for r in my_teams_usage
    }
    for tid in my_team_ids:
        if tid not in usage_team_ids:
            my_teams_usage.append({
                "team_id": str(tid),
                "team_name": teams_by_id.get(tid, "Unknown Team"),
                "total_tokens": 0,
                "estimated_cost": 0.0,
            })

    return {
        "data": {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "display_name": current_user.display_name,
            "role": current_user.role,
            "period": {
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat(),
            },
            "teams": my_teams_usage,
        }
    }
