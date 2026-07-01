"""Organization-wide cost rollup from connected tools (not team aggregates)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.billing_totals import (
    compute_copilot_billed_split_from_parsed,
    totals_from_upload_ids,
)
from app.copilot.service import CopilotAnalyticsService
from app.models.collector import UsageEvent
from app.models.copilot import CopilotBillingImport
from app.models.figma import FigmaBillingImport
from app.models.ingestion import Upload
from app.models.admin import TeamTool
from app.teams.cost_calculator import calculate_pricing_cost
from app.teams.copilot_billing_metrics import (
    active_upload_filter,
    copilot_import_overlaps_period,
)
from app.teams.figma_billing_metrics import figma_import_overlaps_period
from app.teams.pricing_resolution import resolve_team_tool_pricing
from app.teams.repository import TeamRepository
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import connected_to_catalogue_map, usage_tool_ids_for_filter
from app.tools.repository import ToolRepository
from app.usage.cost import usage_event_effective_cost_sql


@dataclass(frozen=True)
class OrgToolCostSummary:
    tools_cost: Decimal
    additional_billable_cost: Decimal
    total_cost: Decimal
    connected_tool_count: int


@dataclass(frozen=True)
class _CopilotToolSplit:
    subscription: Decimal
    additional: Decimal
    total: Decimal


@dataclass(frozen=True)
class _FigmaToolSplit:
    subscription: Decimal
    additional: Decimal
    total: Decimal


async def summarize_organization_tool_costs(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_ids: list[UUID] | None = None,
) -> OrgToolCostSummary:
    """
    Sum pricing and billable spend across connected tools in an organization.

    Organization total cost = total tools cost + additional billable cost.
    Each catalogue tool is counted once (multiple credentials do not duplicate usage).
    """
    tools_repo = ToolRepository(session)
    teams_repo = TeamRepository(session)
    team_tools_repo = TeamToolRepository(session)

    all_tools = await tools_repo.list_by_organization(organization_id, active=None)
    connected_tools = [tool for tool in all_tools if not tool.catalogue_only and tool.active]

    id_to_catalogue = connected_to_catalogue_map(all_tools)
    catalogue_by_id = {tool.id: tool for tool in all_tools if tool.catalogue_only}

    teams = await teams_repo.list_by_organization(organization_id, active=None)
    if team_ids is not None:
        allowed = set(team_ids)
        teams = [team for team in teams if team.id in allowed]

    usage_by_tool = await _usage_by_tool(
        session,
        organization_id,
        from_dt,
        to_dt,
        team_ids=team_ids,
    )
    copilot_uploads_by_tool = await _copilot_upload_ids_by_tool(
        session,
        organization_id,
        from_dt,
        to_dt,
        team_ids=team_ids,
    )
    figma_uploads_by_tool = await _figma_upload_ids_by_tool(
        session,
        organization_id,
        from_dt,
        to_dt,
        team_ids=team_ids,
    )

    catalogue_ids: set[UUID] = set()
    for connected in connected_tools:
        catalogue_ids.add(id_to_catalogue.get(connected.id, connected.id))
    for tool_id in copilot_uploads_by_tool:
        catalogue_ids.add(id_to_catalogue.get(tool_id, tool_id))
    for tool_id in figma_uploads_by_tool:
        catalogue_ids.add(id_to_catalogue.get(tool_id, tool_id))
    for tool_id in usage_by_tool:
        catalogue_ids.add(id_to_catalogue.get(tool_id, tool_id))

    if not catalogue_ids:
        return OrgToolCostSummary(
            tools_cost=Decimal("0"),
            additional_billable_cost=Decimal("0"),
            total_cost=Decimal("0"),
            connected_tool_count=0,
        )

    assignment_by_catalogue = await _best_assignment_by_catalogue(
        team_tools_repo,
        teams,
        catalogue_ids,
    )
    copilot_by_tool = await _copilot_split_by_tool(
        session,
        copilot_uploads_by_tool,
        assignment_by_catalogue,
        id_to_catalogue,
    )
    figma_by_tool = await _figma_split_by_tool(
        session,
        figma_uploads_by_tool,
        assignment_by_catalogue,
        id_to_catalogue,
    )
    unscoped_cost = await _unscoped_org_cost(
        session,
        organization_id,
        from_dt,
        to_dt,
        team_ids=team_ids,
    )

    tools_cost = Decimal("0")
    additional_billable = Decimal("0")

    for catalogue_id in sorted(catalogue_ids):
        catalogue_tool = catalogue_by_id.get(catalogue_id)
        if catalogue_tool is None:
            continue

        copilot_key = _import_tool_key(catalogue_id, id_to_catalogue, copilot_by_tool)
        figma_key = _import_tool_key(catalogue_id, id_to_catalogue, figma_by_tool)

        if copilot_key is not None:
            split = copilot_by_tool[copilot_key]
            tools_cost += split.subscription
            additional_billable += split.additional
            continue

        if figma_key is not None:
            split = figma_by_tool[figma_key]
            tools_cost += split.subscription
            additional_billable += split.additional
            continue

        event_ids = usage_tool_ids_for_filter(all_tools, catalogue_id)
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0
        raw_spend = Decimal("0")
        for event_tool_id in event_ids:
            row = usage_by_tool.get(event_tool_id)
            if row is None:
                continue
            input_tokens += row[0]
            output_tokens += row[1]
            total_tokens += row[2]
            raw_spend += row[3]

        assignment = assignment_by_catalogue.get(catalogue_id)
        pricing = resolve_team_tool_pricing(assignment, catalogue_tool)
        tool_pricing = calculate_pricing_cost(
            pricing,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

        tools_cost += tool_pricing
        additional_billable += max(raw_spend - tool_pricing, Decimal("0"))

    additional_billable += unscoped_cost

    return OrgToolCostSummary(
        tools_cost=tools_cost,
        additional_billable_cost=additional_billable,
        total_cost=tools_cost + additional_billable,
        connected_tool_count=len(catalogue_ids),
    )


async def _best_assignment_by_catalogue(
    team_tools_repo: TeamToolRepository,
    teams: list,
    catalogue_ids: set[UUID],
) -> dict[UUID, TeamTool]:
    """Prefer team-tool rows that define pricing over catalogue defaults."""
    best: dict[UUID, TeamTool] = {}
    for team in teams:
        assignments = await team_tools_repo.list_by_team(team.id)
        for assignment in assignments:
            if assignment.tool_id not in catalogue_ids:
                continue
            current = best.get(assignment.tool_id)
            if current is None:
                best[assignment.tool_id] = assignment
                continue
            if assignment.pricing_model and not current.pricing_model:
                best[assignment.tool_id] = assignment
    return best


def _import_tool_key(
    catalogue_id: UUID,
    id_to_catalogue: dict[UUID, UUID],
    splits: dict[UUID, _CopilotToolSplit | _FigmaToolSplit],
) -> UUID | None:
    if catalogue_id in splits:
        return catalogue_id
    for tool_id in splits:
        if id_to_catalogue.get(tool_id, tool_id) == catalogue_id:
            return tool_id
    return None


async def _usage_by_tool(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_ids: list[UUID] | None = None,
) -> dict[UUID, tuple[int, int, int, Decimal]]:
    conditions = [
        UsageEvent.organization_id == organization_id,
        UsageEvent.tool_id.is_not(None),
        UsageEvent.occurred_at >= from_dt,
        UsageEvent.occurred_at <= to_dt,
    ]
    if team_ids is not None:
        conditions.append(UsageEvent.team_id.in_(team_ids))

    result = await session.execute(
        select(
            UsageEvent.tool_id,
            func.coalesce(func.sum(UsageEvent.input_tokens), 0),
            func.coalesce(func.sum(UsageEvent.output_tokens), 0),
            func.coalesce(func.sum(UsageEvent.total_tokens), 0),
            func.coalesce(func.sum(usage_event_effective_cost_sql()), 0),
        )
        .where(*conditions)
        .group_by(UsageEvent.tool_id)
    )
    return {
        tool_id: (
            int(input_tokens),
            int(output_tokens),
            int(total_tokens),
            Decimal(str(cost)),
        )
        for tool_id, input_tokens, output_tokens, total_tokens, cost in result.all()
        if tool_id is not None
    }


async def _unscoped_org_cost(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_ids: list[UUID] | None = None,
) -> Decimal:
    conditions = [
        UsageEvent.organization_id == organization_id,
        UsageEvent.tool_id.is_(None),
        UsageEvent.occurred_at >= from_dt,
        UsageEvent.occurred_at <= to_dt,
    ]
    if team_ids is not None:
        conditions.append(UsageEvent.team_id.in_(team_ids))

    result = await session.execute(
        select(func.coalesce(func.sum(usage_event_effective_cost_sql()), 0)).where(*conditions)
    )
    return Decimal(str(result.scalar_one() or 0))


async def _copilot_upload_ids_by_tool(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_ids: list[UUID] | None = None,
) -> dict[UUID, set[UUID]]:
    from_date = from_dt.date()
    to_date = to_dt.date()
    stmt = (
        select(CopilotBillingImport.tool_id, CopilotBillingImport.upload_id)
        .outerjoin(Upload, CopilotBillingImport.upload_id == Upload.id)
        .where(
            CopilotBillingImport.organization_id == organization_id,
            CopilotBillingImport.tool_id.isnot(None),
            CopilotBillingImport.upload_id.isnot(None),
            active_upload_filter(),
        )
        .where(copilot_import_overlaps_period(from_date, to_date))
    )
    if team_ids is not None:
        stmt = stmt.where(CopilotBillingImport.team_id.in_(team_ids))

    result = await session.execute(stmt)
    uploads_by_tool: dict[UUID, set[UUID]] = {}
    for tool_id, upload_id in result.all():
        if tool_id is None or upload_id is None:
            continue
        uploads_by_tool.setdefault(tool_id, set()).add(upload_id)
    return uploads_by_tool


async def _figma_upload_ids_by_tool(
    session: AsyncSession,
    organization_id: UUID,
    from_dt: datetime,
    to_dt: datetime,
    *,
    team_ids: list[UUID] | None = None,
) -> dict[UUID, set[UUID]]:
    from_date = from_dt.date()
    to_date = to_dt.date()
    stmt = (
        select(FigmaBillingImport.tool_id, FigmaBillingImport.upload_id)
        .outerjoin(Upload, FigmaBillingImport.upload_id == Upload.id)
        .where(
            FigmaBillingImport.organization_id == organization_id,
            FigmaBillingImport.tool_id.isnot(None),
            FigmaBillingImport.upload_id.isnot(None),
            active_upload_filter(),
        )
        .where(figma_import_overlaps_period(from_date, to_date))
    )
    if team_ids is not None:
        stmt = stmt.where(FigmaBillingImport.team_id.in_(team_ids))

    result = await session.execute(stmt)
    uploads_by_tool: dict[UUID, set[UUID]] = {}
    for tool_id, upload_id in result.all():
        if tool_id is None or upload_id is None:
            continue
        uploads_by_tool.setdefault(tool_id, set()).add(upload_id)
    return uploads_by_tool


async def _copilot_split_by_tool(
    session: AsyncSession,
    uploads_by_tool: dict[UUID, set[UUID]],
    assignment_by_catalogue: dict[UUID, TeamTool],
    id_to_catalogue: dict[UUID, UUID],
) -> dict[UUID, _CopilotToolSplit]:
    splits: dict[UUID, _CopilotToolSplit] = {}
    for tool_id, upload_ids in uploads_by_tool.items():
        if not upload_ids:
            continue
        parsed = await totals_from_upload_ids(session, list(upload_ids))
        if parsed.net_total <= 0 and parsed.credits_gross <= 0 and parsed.gross_total <= 0:
            continue

        catalogue_id = id_to_catalogue.get(tool_id, tool_id)
        assignment = assignment_by_catalogue.get(catalogue_id)
        _, _, configured_subscription, _ = CopilotAnalyticsService._configured_copilot_pricing(
            assignment
        )
        subscription = configured_subscription or Decimal("0")
        subscription, additional, total = compute_copilot_billed_split_from_parsed(
            parsed,
            configured_subscription,
        )
        if total <= 0:
            continue
        splits[tool_id] = _CopilotToolSplit(
            subscription=subscription,
            additional=additional,
            total=total,
        )
    return splits


async def _figma_split_by_tool(
    session: AsyncSession,
    uploads_by_tool: dict[UUID, set[UUID]],
    assignment_by_catalogue: dict[UUID, TeamTool],
    id_to_catalogue: dict[UUID, UUID],
) -> dict[UUID, _FigmaToolSplit]:
    from app.figma.pricing import (
        FigmaImportPeriodSlice,
        figma_pricing_from_assignment,
        figma_split_costs_from_import_slices,
    )

    splits: dict[UUID, _FigmaToolSplit] = {}
    for tool_id, upload_ids in uploads_by_tool.items():
        if not upload_ids:
            continue
        result = await session.execute(
            select(
                FigmaBillingImport.usage_period_start,
                FigmaBillingImport.usage_period_end,
                FigmaBillingImport.full_seat_count,
                FigmaBillingImport.view_seat_count,
                FigmaBillingImport.total_paid_cost,
            ).where(
                FigmaBillingImport.tool_id == tool_id,
                FigmaBillingImport.upload_id.in_(upload_ids),
            )
        )
        slices = [
            FigmaImportPeriodSlice(
                usage_period_start=start,
                usage_period_end=end,
                full_seat_count=int(full_count or 0),
                view_seat_count=int(view_count or 0),
                paid_cost_usd=Decimal(str(paid or 0)),
            )
            for start, end, full_count, view_count, paid in result.all()
            if start is not None or Decimal(str(paid or 0)) > 0
        ]
        if not slices:
            continue

        catalogue_id = id_to_catalogue.get(tool_id, tool_id)
        assignment = assignment_by_catalogue.get(catalogue_id)
        pricing = figma_pricing_from_assignment(assignment)
        subscription_start = assignment.subscription_start if assignment else None
        sub, add, _merged = figma_split_costs_from_import_slices(
            slices,
            pricing,
            subscription_start,
        )
        if sub <= 0 and add <= 0:
            continue
        splits[tool_id] = _FigmaToolSplit(
            subscription=sub,
            additional=add,
            total=sub + add,
        )
    return splits

