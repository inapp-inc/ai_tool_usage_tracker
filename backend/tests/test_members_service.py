"""Tests for unified members list service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.members.service import MembersService


@pytest.mark.asyncio
async def test_list_members_invited_excludes_tool_rows() -> None:
    org_id = uuid4()
    user_id = uuid4()
    session = AsyncMock()

    user = MagicMock()
    user.id = user_id
    user.email = "dev@acme.example"
    user.display_name = "Dev User"
    user.role = "team_member"
    user.active = True
    user.last_login_at = None
    user.created_at = MagicMock()

    service = MembersService(session)
    service._users.list_by_organization = AsyncMock(return_value=[user])
    service._memberships.list_team_summaries_for_users = AsyncMock(return_value={})
    service._teams.list_by_organization = AsyncMock(return_value=[])

    result = await service.list_members(org_id, view="invited")

    assert len(result.data) == 1
    assert result.data[0].source == "platform"
    assert result.data[0].email == "dev@acme.example"


@pytest.mark.asyncio
async def test_list_members_all_merges_tool_only_emails() -> None:
    org_id = uuid4()
    team_id = uuid4()
    tool_id = uuid4()
    session = AsyncMock()

    service = MembersService(session)
    service._users.list_by_organization = AsyncMock(return_value=[])
    service._memberships.list_team_summaries_for_users = AsyncMock(return_value={})

    team = MagicMock()
    team.id = team_id
    team.name = "Engineering"
    service._teams.list_by_organization = AsyncMock(return_value=[team])

    from app.teams.tool_members import ToolMemberEntry

    tool_entry = ToolMemberEntry(
        email="cursor@acme.example",
        name="Cursor User",
        tool_id=tool_id,
        tool_name="Cursor",
    )

    with patch(
        "app.members.service.fetch_tool_members_for_team",
        new_callable=AsyncMock,
        return_value=[tool_entry],
    ):
        result = await service.list_members(org_id, view="all")

    assert len(result.data) == 1
    assert result.data[0].source == "tool"
    assert result.data[0].email == "cursor@acme.example"
    assert result.data[0].teams[0].name == "Engineering"
