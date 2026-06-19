"""Aggregate usage and sync metrics for team list display."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Team, TeamTool, Tool
from app.models.collector import UsageEvent
from app.teams.cost_calculator import calculate_pricing_cost
from app.teams.pricing_resolution import resolve_team_tool_pricing
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import connected_to_catalogue_map, find_connected_for_catalogue
from app.tools.repository import ToolRepository
from app.usage.periods import current_month_window
from app.usage.aggregates import sum_org_cost, sum_tokens_and_cost_by_team


@dataclass(frozen=True)
class TeamMetrics:
    tokens_used: int = 0
    pricing_total: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")
    last_synced_at: datetime | None = None


class TeamMetricsLoader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._team_tools = TeamToolRepository(session)
        self._tools = ToolRepository(session)

    async def load_for_teams(
        self,
        organization_id: UUID,
        teams: list[Team],
        *,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> dict[UUID, TeamMetrics]:
        if not teams:
            return {}

        if from_dt is None or to_dt is None:
            from_dt, to_dt = current_month_window()

        team_ids = [team.id for team in teams]
        org_tools = await self._tools.list_by_organization(organization_id, active=None)
        id_to_catalogue = connected_to_catalogue_map(org_tools)
        team_tool_ids = self._team_tool_id_map(teams, id_to_catalogue)
        assignments_by_pair = await self._load_assignments(team_ids)
        for pair in assignments_by_pair:
            catalogue_id = id_to_catalogue.get(pair[1], pair[1])
            team_tool_ids.setdefault(pair[0], set()).add(catalogue_id)

        all_tool_ids = sorted({tool_id for ids in team_tool_ids.values() for tool_id in ids})
        tools_by_id = await self._load_tools(organization_id, all_tool_ids)

        usage_by_team = await sum_tokens_and_cost_by_team(
            self._session,
            organization_id,
            team_ids,
            from_dt,
            to_dt,
        )
        usage_by_team_tool = await self._usage_by_team_and_tool(
            organization_id,
            team_ids,
            from_dt,
            to_dt,
        )
        unscoped_cost = await self._unscoped_tool_cost(
            organization_id,
            team_ids,
            from_dt,
            to_dt,
        )

        metrics: dict[UUID, TeamMetrics] = {}
        for team in teams:
            tokens_used, total_cost = usage_by_team.get(team.id, (0, Decimal("0")))
            pricing_total = Decimal("0")

            for tool_id in team_tool_ids.get(team.id, set()):
                tool = tools_by_id.get(tool_id)
                if tool is None:
                    continue

                input_tokens, output_tokens, tool_total, _event_cost = self._usage_for_catalogue_tool(
                    team.id,
                    tool_id,
                    usage_by_team_tool,
                    id_to_catalogue,
                )

                assignment = assignments_by_pair.get((team.id, tool_id))
                pricing = resolve_team_tool_pricing(assignment, tool)
                pricing_total += calculate_pricing_cost(
                    pricing,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=tool_total,
                )

            pricing_total += unscoped_cost.get(team.id, Decimal("0"))
            last_synced_at = self._last_synced_at(
                team,
                team_tool_ids.get(team.id, set()),
                tools_by_id,
                org_tools,
            )

            metrics[team.id] = TeamMetrics(
                tokens_used=tokens_used,
                pricing_total=pricing_total,
                total_cost=total_cost,
                last_synced_at=last_synced_at,
            )

        return metrics

    async def _load_tools(
        self,
        organization_id: UUID,
        tool_ids: list[UUID],
    ) -> dict[UUID, Tool]:
        if not tool_ids:
            return {}
        tools = await self._tools.list_by_organization(organization_id, active=None, catalogue_only=True)
        wanted = set(tool_ids)
        return {tool.id: tool for tool in tools if tool.id in wanted}

    async def _load_assignments(
        self,
        team_ids: list[UUID],
    ) -> dict[tuple[UUID, UUID], TeamTool]:
        mapping: dict[tuple[UUID, UUID], TeamTool] = {}
        for team_id in team_ids:
            rows = await self._team_tools.list_by_team(team_id)
            for row in rows:
                mapping[(team_id, row.tool_id)] = row
        return mapping

    async def _usage_by_team_and_tool(
        self,
        organization_id: UUID,
        team_ids: list[UUID],
        from_dt: datetime,
        to_dt: datetime,
    ) -> dict[tuple[UUID, UUID], tuple[int, int, int, Decimal]]:
        result = await self._session.execute(
            select(
                UsageEvent.team_id,
                UsageEvent.tool_id,
                func.coalesce(func.sum(UsageEvent.input_tokens), 0),
                func.coalesce(func.sum(UsageEvent.output_tokens), 0),
                func.coalesce(func.sum(UsageEvent.total_tokens), 0),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .where(
                UsageEvent.organization_id == organization_id,
                UsageEvent.team_id.in_(team_ids),
                UsageEvent.tool_id.is_not(None),
                UsageEvent.occurred_at >= from_dt,
                UsageEvent.occurred_at <= to_dt,
            )
            .group_by(UsageEvent.team_id, UsageEvent.tool_id)
        )
        return {
            (team_id, tool_id): (
                int(input_tokens),
                int(output_tokens),
                int(total_tokens),
                Decimal(str(cost)),
            )
            for team_id, tool_id, input_tokens, output_tokens, total_tokens, cost in result.all()
            if team_id is not None and tool_id is not None
        }

    async def _unscoped_tool_cost(
        self,
        organization_id: UUID,
        team_ids: list[UUID],
        from_dt: datetime,
        to_dt: datetime,
    ) -> dict[UUID, Decimal]:
        """Usage without tool_id — count recorded cost toward pricing total fallback."""
        result = await self._session.execute(
            select(
                UsageEvent.team_id,
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .where(
                UsageEvent.organization_id == organization_id,
                UsageEvent.team_id.in_(team_ids),
                UsageEvent.tool_id.is_(None),
                UsageEvent.occurred_at >= from_dt,
                UsageEvent.occurred_at <= to_dt,
            )
            .group_by(UsageEvent.team_id)
        )
        return {
            team_id: Decimal(str(cost))
            for team_id, cost in result.all()
            if team_id is not None
        }

    @staticmethod
    def _usage_for_catalogue_tool(
        team_id: UUID,
        catalogue_tool_id: UUID,
        usage_by_team_tool: dict[tuple[UUID, UUID], tuple[int, int, int, Decimal]],
        id_to_catalogue: dict[UUID, UUID],
    ) -> tuple[int, int, int, Decimal]:
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        cost = Decimal("0")
        for (event_team_id, event_tool_id), values in usage_by_team_tool.items():
            if event_team_id != team_id:
                continue
            if id_to_catalogue.get(event_tool_id, event_tool_id) != catalogue_tool_id:
                continue
            input_tokens += values[0]
            output_tokens += values[1]
            total_tokens += values[2]
            cost += values[3]
        return input_tokens, output_tokens, total_tokens, cost

    @staticmethod
    def _team_tool_id_map(
        teams: list[Team],
        id_to_catalogue: dict[UUID, UUID],
    ) -> dict[UUID, set[UUID]]:
        mapping: dict[UUID, set[UUID]] = {}
        for team in teams:
            ids: set[UUID] = set()
            raw = team.tool_ids if isinstance(team.tool_ids, list) else []
            for item in raw:
                try:
                    raw_id = UUID(str(item))
                except ValueError:
                    continue
                ids.add(id_to_catalogue.get(raw_id, raw_id))
            mapping[team.id] = ids
        return mapping

    @staticmethod
    def _last_synced_at(
        team: Team,
        tool_ids: set[UUID],
        tools_by_id: dict[UUID, Tool],
        org_tools: list[Tool],
    ) -> datetime | None:
        latest: datetime | None = None
        for tool_id in tool_ids:
            tool = tools_by_id.get(tool_id)
            if tool is None:
                continue
            sync_tool = tool
            if tool.catalogue_only:
                connected = find_connected_for_catalogue(org_tools, tool_id)
                if connected is not None:
                    sync_tool = connected
            if sync_tool.last_sync_at is None:
                continue
            if latest is None or sync_tool.last_sync_at > latest:
                latest = sync_tool.last_sync_at
        return latest
