"""Verify Teams list cost matches dashboard usage-by-team for the same period."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.dashboard.scope import DashboardScope
from app.dashboard.service import DashboardService
from app.usage.aggregates import sum_tokens_and_cost_by_team
from app.usage.periods import current_month_window


@pytest.mark.asyncio
async def test_sum_tokens_and_cost_by_team_uses_org_and_team_filters() -> None:
    org_id = uuid4()
    team_id = uuid4()
    from_dt, to_dt = current_month_window()

    session = MagicMock()
    result = MagicMock()
    result.all.return_value = [(team_id, 5000, Decimal("12.50"))]
    session.execute = AsyncMock(return_value=result)

    totals = await sum_tokens_and_cost_by_team(
        session,
        org_id,
        [team_id],
        from_dt,
        to_dt,
    )

    assert totals[team_id] == (5000, Decimal("12.50"))
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_dashboard_usage_by_team_matches_shared_aggregate_without_tool_filter() -> None:
    org_id = uuid4()
    team_id = uuid4()
    from_dt = datetime(2026, 6, 1, tzinfo=UTC)
    to_dt = datetime(2026, 6, 17, tzinfo=UTC)

    team = MagicMock()
    team.id = team_id
    team.name = "Engineering"

    service = DashboardService(MagicMock())
    service._org_team_ids = AsyncMock(return_value=[team_id])
    service._teams = MagicMock()
    service._teams.list_by_organization = AsyncMock(return_value=[team])
    service._last_updated_at = AsyncMock(return_value=to_dt)

    expected_map = {team_id: (1000, Decimal("25.00"))}

    async def fake_sum(session, organization_id, team_ids, start, end):
        assert organization_id == org_id
        assert team_ids == [team_id]
        assert start == from_dt
        assert end == to_dt
        return expected_map

    import app.dashboard.service as dashboard_module

    original = dashboard_module.sum_tokens_and_cost_by_team
    dashboard_module.sum_tokens_and_cost_by_team = fake_sum
    try:
        scope = DashboardScope(
            organization_id=org_id,
            allowed_team_ids=None,
            user_id=None,
            user_email=None,
        )
        response = await service.get_usage_by_team(scope, from_dt, to_dt)
    finally:
        dashboard_module.sum_tokens_and_cost_by_team = original

    assert len(response.data) == 1
    assert response.data[0].team_id == team_id
    assert response.data[0].estimated_cost == Decimal("25.00")
    assert response.data[0].total_tokens == 1000
