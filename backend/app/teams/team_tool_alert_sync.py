"""Sync team tool USD alert settings to admin threshold rules."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.admin import Team, TeamTool, Tool
from app.models.notifications import Threshold
from app.thresholds.evaluator import ThresholdEvaluator


def _alert_rule_name(tool_name: str, team_name: str) -> str:
    return f"{tool_name} cost alert — {team_name}"


async def sync_team_tool_cost_alert(
    session: AsyncSession,
    *,
    organization_id: UUID,
    team: Team,
    tool: Tool,
    assignment: TeamTool,
) -> None:
    """Create, update, or deactivate a cost threshold rule from team tool alert settings."""
    config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
    rule_id_raw = config.get("alert_threshold_rule_id")
    existing: Threshold | None = None
    if rule_id_raw:
        try:
            rule_id = UUID(str(rule_id_raw))
        except ValueError:
            rule_id = None
        else:
            existing = await session.get(Threshold, rule_id)

    if existing is None:
        result = await session.execute(
            select(Threshold).where(
                Threshold.organization_id == organization_id,
                Threshold.team_id == team.id,
                Threshold.tool_id == tool.id,
                Threshold.threshold_type == "cost_amount",
            )
        )
        existing = result.scalars().first()

    limit = assignment.alert_threshold_usd
    if limit is None and assignment.monthly_budget is not None and assignment.alert_threshold is not None:
        limit = assignment.monthly_budget * (assignment.alert_threshold / Decimal("100"))

    if limit is None or limit <= 0:
        if existing is not None:
            existing.active = False
        return

    name = _alert_rule_name(tool.name, team.name)
    if existing is None:
        row = Threshold(
            organization_id=organization_id,
            name=name,
            threshold_type="cost_amount",
            scope="tool",
            tool_id=tool.id,
            team_id=team.id,
            limit_value=limit,
            severity="warning",
            notify_email=True,
            notify_in_app=True,
            active=True,
        )
        session.add(row)
        await session.flush()
        config = dict(config)
        config["alert_threshold_rule_id"] = str(row.id)
        assignment.pricing_config = config
        flag_modified(assignment, "pricing_config")
        await ThresholdEvaluator(session).evaluate_threshold(row)
        return

    existing.name = name
    existing.limit_value = limit
    existing.scope = "tool"
    existing.tool_id = tool.id
    existing.team_id = team.id
    existing.threshold_type = "cost_amount"
    existing.active = True
    config = dict(config)
    config["alert_threshold_rule_id"] = str(existing.id)
    assignment.pricing_config = config
    flag_modified(assignment, "pricing_config")
    await ThresholdEvaluator(session).evaluate_threshold(existing)
