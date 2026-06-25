"""Evaluate synced team-tool cost threshold after billing CSV import."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import TeamTool
from app.models.notifications import Threshold
from app.thresholds.evaluator import ThresholdEvaluator


async def evaluate_import_cost_alert(
    session: AsyncSession,
    assignment: TeamTool,
) -> int:
    """
    Re-run threshold evaluation for a team tool's synced cost alert rule.

    Returns notification count when a breach fires (rule is then deactivated).
    """
    config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
    rule_id_raw = config.get("alert_threshold_rule_id")
    if not rule_id_raw:
        return 0
    try:
        rule_id = UUID(str(rule_id_raw))
    except ValueError:
        return 0

    threshold = await session.get(Threshold, rule_id)
    if threshold is None or not threshold.active:
        return 0

    return await ThresholdEvaluator(session).evaluate_threshold(threshold)
