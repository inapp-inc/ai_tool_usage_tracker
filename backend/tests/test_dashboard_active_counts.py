"""Tests for dashboard active inventory counts."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.dashboard.scope import DashboardScope
from app.dashboard.service import DashboardService


@pytest.mark.asyncio
async def test_get_active_counts_org_wide_matches_tools_module() -> None:
    org_id = uuid4()
    team_a = uuid4()
    team_b = uuid4()

    team_one = MagicMock()
    team_one.id = team_a
    team_one.active = True
    team_one.tool_ids = []

    team_two = MagicMock()
    team_two.id = team_b
    team_two.active = False
    team_two.tool_ids = []

    catalogue_tools = [MagicMock() for _ in range(7)]

    service = DashboardService(MagicMock())
    service._teams = MagicMock()
    service._teams.list_by_organization = AsyncMock(return_value=[team_one, team_two])
    service._tools = MagicMock()
    service._tools.list_by_organization = AsyncMock(return_value=catalogue_tools)

    scope = DashboardScope(organization_id=org_id, user_id=None, user_email=None, allowed_team_ids=None)
    result = await service.get_active_counts(scope)

    assert result.active_tools == 7
    assert result.active_teams == 1
    service._tools.list_by_organization.assert_awaited_once_with(
        org_id,
        active=None,
        catalogue_only=True,
    )


@pytest.mark.asyncio
async def test_get_active_counts_for_team_uses_assigned_catalogue_tools() -> None:
    org_id = uuid4()
    team_id = uuid4()
    catalogue_a = uuid4()
    catalogue_b = uuid4()

    team = MagicMock()
    team.id = team_id
    team.active = True
    team.tool_ids = [str(catalogue_a), str(catalogue_b)]

    service = DashboardService(MagicMock())
    service._teams = MagicMock()
    service._teams.list_by_organization = AsyncMock(return_value=[team])
    service._team_tools = MagicMock()
    service._team_tools.list_by_team = AsyncMock(return_value=[])

    scope = DashboardScope(organization_id=org_id, user_id=None, user_email=None, allowed_team_ids=None)
    result = await service.get_active_counts(scope, team_id=team_id)

    assert result.active_tools == 2
    assert result.active_teams == 1
