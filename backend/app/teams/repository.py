"""Team data access."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Team


class TeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active: bool | None = None,
    ) -> list[Team]:
        stmt = select(Team).where(Team.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Team.active == active)
        stmt = stmt.order_by(Team.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_organizations(
        self,
        organization_ids: list[UUID],
        *,
        active: bool | None = None,
    ) -> list[Team]:
        if not organization_ids:
            return []
        stmt = select(Team).where(Team.organization_id.in_(organization_ids))
        if active is not None:
            stmt = stmt.where(Team.active == active)
        stmt = stmt.order_by(Team.organization_id.asc(), Team.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, team_id: UUID, organization_id: UUID) -> Team | None:
        result = await self._session.execute(
            select(Team).where(
                Team.id == team_id,
                Team.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_unscoped(self, team_id: UUID) -> Team | None:
        result = await self._session.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, organization_id: UUID, name: str) -> Team | None:
        normalized = name.strip()
        result = await self._session.execute(
            select(Team).where(
                Team.organization_id == organization_id,
                func.lower(Team.name) == normalized.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        description: str | None,
        token_budget: int | None = None,
        cost_budget: Decimal | None = None,
        tool_ids: list[str] | None = None,
    ) -> Team:
        team = Team(
            organization_id=organization_id,
            name=name.strip(),
            description=description.strip() if description else None,
            active=True,
            token_budget=token_budget,
            cost_budget=cost_budget,
            tool_ids=tool_ids or [],
        )
        self._session.add(team)
        await self._session.flush()
        return team

    async def delete(self, team: Team) -> None:
        await self._session.delete(team)
        await self._session.flush()
