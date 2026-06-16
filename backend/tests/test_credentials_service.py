"""Tests for tool-backed credentials service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.credentials.service import CredentialService


@pytest.mark.asyncio
async def test_list_credentials_maps_tool_fields() -> None:
    org_id = uuid4()
    tool_id = uuid4()
    session = AsyncMock()

    tool = MagicMock()
    tool.id = tool_id
    tool.name = "Cursor"
    tool.description = "Team Cursor key"
    tool.credential_label = "Cursor Production"
    tool.credential_environment = "production"
    tool.credential_expires_at = None
    tool.rotation_reminder_days = 14
    tool.active = True
    tool.api_token_ciphertext = "encrypted"
    tool.last_sync_at = None
    tool.created_at = MagicMock()

    service = CredentialService(session)
    service._tools.list_by_organization = AsyncMock(return_value=[tool])
    service._teams.list_by_organization = AsyncMock(return_value=[])

    with patch.object(CredentialService, "_mask_secret", return_value="sk-...abcd"):
        result = await service.list_credentials(org_id)

    assert len(result.data) == 1
    assert result.data[0].id == tool_id
    assert result.data[0].label == "Cursor Production"
    assert result.data[0].masked_secret == "sk-...abcd"
    assert result.data[0].status == "active"
