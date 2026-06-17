"""Tests for team–tool assignments and pricing resolution."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.admin import TeamTool, Tool
from app.teams.pricing_resolution import resolve_team_tool_pricing
from app.teams.schemas import TeamToolAssignRequest
from app.teams.team_tool_service import TeamToolService
from app.tools.service import ToolService

def _tool(**overrides) -> Tool:
    tool = MagicMock(spec=Tool)
    tool.id = overrides.get("id", uuid4())
    tool.name = overrides.get("name", "OpenAI")
    tool.pricing_model = overrides.get("pricing_model", "flat_token")
    tool.token_price = overrides.get("token_price", Decimal("0.002"))
    tool.package_allowance = overrides.get("package_allowance", None)
    tool.overage_price = overrides.get("overage_price", None)
    tool.pricing_config = overrides.get(
        "pricing_config",
        {"output_cost_per_1k": "0.006", "model": "per_token"},
    )
    return tool


def _assignment(**overrides) -> TeamTool:
    assignment = MagicMock(spec=TeamTool)
    assignment.pricing_model = overrides.get("pricing_model", "flat_token")
    assignment.token_price = overrides.get("token_price", Decimal("0.005"))
    assignment.output_token_price = overrides.get("output_token_price", None)
    assignment.cost_per_seat = overrides.get("cost_per_seat", None)
    assignment.seat_count = overrides.get("seat_count", None)
    assignment.package_allowance = overrides.get("package_allowance", None)
    assignment.overage_price = overrides.get("overage_price", None)
    assignment.plan_name = overrides.get("plan_name", None)
    assignment.pricing_config = overrides.get("pricing_config", {})
    return assignment


def test_resolve_team_tool_pricing_uses_team_override() -> None:
    tool = _tool(token_price=Decimal("0.002"))
    assignment = _assignment(token_price=Decimal("0.005"))

    resolved = resolve_team_tool_pricing(assignment, tool)

    assert resolved.source == "team_tool"
    assert resolved.token_price == Decimal("0.005")
    assert resolved.output_token_price == Decimal("0.006")


def test_resolve_team_tool_pricing_falls_back_to_tool_default() -> None:
    tool = _tool(
        token_price=Decimal("0.003"),
        package_allowance=1_000_000,
        overage_price=Decimal("0.001"),
    )

    resolved = resolve_team_tool_pricing(None, tool)

    assert resolved.source == "tool_default"
    assert resolved.token_price == Decimal("0.003")
    assert resolved.package_allowance == 1_000_000
    assert resolved.overage_price == Decimal("0.001")


@pytest.mark.asyncio
async def test_create_assignment_persists_pricing_fields() -> None:
    org_id = uuid4()
    team_id = uuid4()
    tool_id = uuid4()
    user = MagicMock()
    user.role = "super_admin"
    user.organization_id = org_id
    user.id = uuid4()

    team = MagicMock()
    team.id = team_id
    team.tool_ids = []

    tool = _tool(id=tool_id)

    session = AsyncMock()
    service = TeamToolService(session)
    service._require_team_access = AsyncMock(return_value=team)
    service._require_tool = AsyncMock(return_value=tool)
    service._team_tools.get_by_team_and_tool = AsyncMock(return_value=None)
    service._team_tools.create = AsyncMock(side_effect=lambda row: row)

    body = TeamToolAssignRequest(
        tool_id=tool_id,
        pricing_model="flat_token",
        token_price=Decimal("0.004"),
        output_token_price=Decimal("0.008"),
    )

    with patch.object(TeamToolService, "_to_response") as to_response:
        to_response.return_value = MagicMock()
        await service.create_assignment(user, team_id, body)

    created = service._team_tools.create.await_args.args[0]
    assert created.token_price == Decimal("0.004")
    assert created.output_token_price == Decimal("0.008")
    service._session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_team_admin_denied_for_unassigned_team() -> None:
    org_id = uuid4()
    team_id = uuid4()
    user = MagicMock()
    user.role = "team_admin"
    user.organization_id = org_id
    user.id = uuid4()

    team = MagicMock()
    team.id = team_id

    session = AsyncMock()
    service = TeamToolService(session)
    service._teams.get_by_id = AsyncMock(return_value=team)
    service._memberships.active_team_ids_for_user = AsyncMock(return_value=[])

    with pytest.raises(HTTPException) as exc_info:
        await service.list_assignments(user, team_id)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_sync_team_tools_skips_tools_without_credentials() -> None:
    org_id = uuid4()
    team_id = uuid4()
    tool_id = uuid4()
    user = MagicMock()
    user.role = "super_admin"
    user.organization_id = org_id
    user.id = uuid4()

    team = MagicMock()
    team.id = team_id
    team.tool_ids = [str(tool_id)]

    tool = MagicMock()
    tool.id = tool_id
    tool.name = "OpenAI"
    tool.api_token_ciphertext = ""

    session = AsyncMock()
    service = TeamToolService(session)
    service._require_team_access = AsyncMock(return_value=team)
    service._collect_team_tool_ids = AsyncMock(return_value=[tool_id])
    service._tools.get_by_id = AsyncMock(return_value=tool)

    with patch.object(ToolService, "_decrypt_api_key", return_value=""):
        result = await service.sync_team_tools(user, team_id)

    assert result.synced_count == 0
    assert result.skipped_count == 1
    assert result.results[0].status == "skipped"
