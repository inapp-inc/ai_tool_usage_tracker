"""Tests for synced member persistence and team member resolution."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.collector.adapters.base import ProviderMember
from app.models.admin import Tool
from app.teams.tool_members import fetch_tool_members_for_team
from app.tools.synced_members import read_synced_members, store_synced_members


def test_store_and_read_synced_members() -> None:
    tool = Tool(
        organization_id=uuid4(),
        name="Cursor Prod",
        vendor="cursor",
        description=None,
        api_endpoint=None,
        pricing_model="flat_token",
        token_price=0,
        package_allowance=None,
        overage_price=None,
        pricing_config={},
        active=True,
        api_token_ciphertext="enc",
        sync_status="inactive",
        catalogue_only=False,
    )
    store_synced_members(
        tool,
        [
            ProviderMember(email="dev@acme.example", name="Dev User"),
            ProviderMember(email="lead@acme.example", name="Lead"),
        ],
    )

    assert tool.member_count == 2
    members = read_synced_members(tool)
    assert len(members) == 2
    assert members[0].email == "dev@acme.example"


@pytest.mark.asyncio
async def test_fetch_tool_members_for_team_uses_connected_credentials() -> None:
    org_id = uuid4()
    team_id = uuid4()
    catalogue_id = uuid4()
    connected_id = uuid4()

    team = MagicMock()
    team.id = team_id
    team.organization_id = org_id
    team.tool_ids = [str(catalogue_id)]

    connected = MagicMock()
    connected.id = connected_id
    connected.name = "Cursor Prod"
    connected.vendor = "cursor"
    connected.active = True
    connected.catalogue_only = False
    connected.api_endpoint = "https://api.cursor.com/health"
    connected.api_token_ciphertext = "enc"
    connected.pricing_config = {
        "catalogue_tool_id": str(catalogue_id),
        "team_id": str(team_id),
        "synced_members": [
            {"email": "dev@acme.example", "name": "Dev User"},
        ],
    }

    catalogue_tool = MagicMock()
    catalogue_tool.id = catalogue_id
    catalogue_tool.name = "Cursor"
    catalogue_tool.catalogue_only = True

    session = AsyncMock()
    tools_repo = MagicMock()
    tools_repo.list_by_organization = AsyncMock(return_value=[catalogue_tool, connected])
    tools_repo.list_connected_for_team = AsyncMock(return_value=[connected])
    tools_repo.get_by_id = AsyncMock(return_value=catalogue_tool)

    team_tools_repo = MagicMock()
    team_tools_repo.list_by_team = AsyncMock(return_value=[])

    with patch("app.teams.tool_members.ToolRepository", return_value=tools_repo):
        with patch("app.teams.tool_members.TeamToolRepository", return_value=team_tools_repo):
            entries = await fetch_tool_members_for_team(session, team)

    assert len(entries) == 1
    assert entries[0].email == "dev@acme.example"
    assert entries[0].tool_name == "Cursor"
    assert entries[0].tool_id == catalogue_id
