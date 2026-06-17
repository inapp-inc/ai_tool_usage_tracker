"""Team–tool assignment data access."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import TeamTool


class TeamToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_team(self, team_id: UUID) -> list[TeamTool]:
        result = await self._session.execute(
            select(TeamTool)
            .where(TeamTool.team_id == team_id)
            .order_by(TeamTool.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_team_and_tool(self, team_id: UUID, tool_id: UUID) -> TeamTool | None:
        result = await self._session.execute(
            select(TeamTool).where(
                TeamTool.team_id == team_id,
                TeamTool.tool_id == tool_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, assignment: TeamTool) -> TeamTool:
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def delete(self, assignment: TeamTool) -> None:
        await self._session.delete(assignment)
        await self._session.flush()
