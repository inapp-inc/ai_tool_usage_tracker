"""Team membership data access."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Team, TeamMembership


class TeamMembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_for_team(self, team_id: UUID) -> list[TeamMembership]:
        result = await self._session.execute(
            select(TeamMembership)
            .where(
                TeamMembership.team_id == team_id,
                TeamMembership.removed_at.is_(None),
            )
            .order_by(TeamMembership.joined_at.asc())
        )
        return list(result.scalars().all())

    async def list_active_teams_for_user(self, user_id: UUID) -> list[tuple[TeamMembership, Team]]:
        result = await self._session.execute(
            select(TeamMembership, Team)
            .join(Team, Team.id == TeamMembership.team_id)
            .where(
                TeamMembership.user_id == user_id,
                TeamMembership.removed_at.is_(None),
            )
            .order_by(Team.name.asc())
        )
        return list(result.all())

    async def list_team_summaries_for_users(
        self,
        organization_id: UUID,
        user_ids: list[UUID],
    ) -> dict[UUID, list[tuple[Team, datetime]]]:
        if not user_ids:
            return {}

        result = await self._session.execute(
            select(TeamMembership.user_id, Team, TeamMembership.joined_at)
            .join(Team, Team.id == TeamMembership.team_id)
            .where(
                TeamMembership.organization_id == organization_id,
                TeamMembership.user_id.in_(user_ids),
                TeamMembership.removed_at.is_(None),
            )
        )
        grouped: dict[UUID, list[tuple[Team, datetime]]] = {}
        for user_id, team, joined_at in result.all():
            grouped.setdefault(user_id, []).append((team, joined_at))
        return grouped

    async def get_active(self, team_id: UUID, user_id: UUID) -> TeamMembership | None:
        result = await self._session.execute(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user_id,
                TeamMembership.removed_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def add(
        self,
        *,
        organization_id: UUID,
        team_id: UUID,
        user_id: UUID,
    ) -> TeamMembership:
        existing = await self.get_active(team_id, user_id)
        if existing is not None:
            return existing

        removed = await self._session.execute(
            select(TeamMembership).where(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == user_id,
                TeamMembership.removed_at.is_not(None),
            )
        )
        prior = removed.scalar_one_or_none()
        if prior is not None:
            prior.removed_at = None
            prior.joined_at = datetime.now(UTC)
            await self._session.flush()
            return prior

        membership = TeamMembership(
            organization_id=organization_id,
            team_id=team_id,
            user_id=user_id,
        )
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def remove(self, team_id: UUID, user_id: UUID) -> bool:
        membership = await self.get_active(team_id, user_id)
        if membership is None:
            return False
        membership.removed_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def sync_user_teams(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        team_ids: list[UUID],
    ) -> None:
        desired = set(team_ids)
        result = await self._session.execute(
            select(TeamMembership).where(
                TeamMembership.user_id == user_id,
                TeamMembership.organization_id == organization_id,
                TeamMembership.removed_at.is_(None),
            )
        )
        active = list(result.scalars().all())
        active_team_ids = {row.team_id for row in active}

        for team_id in desired - active_team_ids:
            await self.add(
                organization_id=organization_id,
                team_id=team_id,
                user_id=user_id,
            )

        for membership in active:
            if membership.team_id not in desired:
                membership.removed_at = datetime.now(UTC)

        await self._session.flush()

    async def active_team_ids_for_user(self, user_id: UUID) -> list[UUID]:
        result = await self._session.execute(
            select(TeamMembership.team_id).where(
                TeamMembership.user_id == user_id,
                TeamMembership.removed_at.is_(None),
            )
        )
        return list(result.scalars().all())
