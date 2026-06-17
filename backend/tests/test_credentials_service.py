"""Tests for tool-backed credentials service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.collector.adapters.base import ProviderValidationError
from app.credentials.schemas import CredentialCreateRequest, CredentialValidateRequest
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


def _mock_tool(*, tool_id=None, vendor="openai", api_endpoint="https://api.openai.com/v1"):
    tool = MagicMock()
    tool.id = tool_id or uuid4()
    tool.name = "Test Tool"
    tool.vendor = vendor
    tool.api_endpoint = api_endpoint
    tool.pricing_config = {}
    tool.description = None
    tool.credential_label = None
    tool.credential_environment = "production"
    tool.credential_expires_at = None
    tool.rotation_reminder_days = None
    tool.active = True
    tool.api_token_ciphertext = ""
    tool.last_sync_at = None
    tool.created_at = MagicMock()
    return tool


@pytest.mark.asyncio
async def test_validate_credential_returns_valid_on_success() -> None:
    org_id = uuid4()
    tool = _mock_tool()
    session = AsyncMock()
    service = CredentialService(session)
    service._require_tool = AsyncMock(return_value=tool)

    with patch.object(
        CredentialService,
        "_validate_secret_for_tool",
        new=AsyncMock(),
    ) as validate_mock:
        result = await service.validate_credential(
            org_id,
            CredentialValidateRequest(tool_id=tool.id, secret_value="sk-test-key-12345"),
        )

    validate_mock.assert_awaited_once_with(tool, "sk-test-key-12345")
    assert result.valid is True
    assert result.provider == "openai"
    assert result.message == "API key verified."


@pytest.mark.asyncio
async def test_validate_credential_raises_422_on_invalid_key() -> None:
    org_id = uuid4()
    tool = _mock_tool()
    session = AsyncMock()
    service = CredentialService(session)
    service._require_tool = AsyncMock(return_value=tool)

    with patch.object(
        CredentialService,
        "_validate_secret_for_tool",
        new=AsyncMock(side_effect=ProviderValidationError("Invalid API key.")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.validate_credential(
                org_id,
                CredentialValidateRequest(tool_id=tool.id, secret_value="bad-key"),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Invalid API key."


@pytest.mark.asyncio
async def test_create_credential_raises_422_on_invalid_key() -> None:
    org_id = uuid4()
    tool = _mock_tool()
    team = MagicMock()
    team.id = uuid4()
    team.tool_ids = []
    session = AsyncMock()
    service = CredentialService(session)
    service._require_tool = AsyncMock(return_value=tool)
    service._require_team = AsyncMock(return_value=team)

    with patch.object(
        CredentialService,
        "_validate_secret_for_tool",
        new=AsyncMock(side_effect=ProviderValidationError("Invalid API key.")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.create_credential(
                org_id,
                CredentialCreateRequest(
                    label="Prod key",
                    tool_id=tool.id,
                    team_id=team.id,
                    secret_value="bad-key",
                ),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Invalid API key."
