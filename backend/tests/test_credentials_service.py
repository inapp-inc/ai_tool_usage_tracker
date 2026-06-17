"""Tests for credentials service (live provider connections)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.collector.adapters.base import ProviderValidationError
from app.credentials.schemas import CredentialCreateRequest, CredentialValidateRequest
from app.credentials.service import CredentialService


@pytest.mark.asyncio
async def test_list_credentials_maps_connected_tool_fields() -> None:
    org_id = uuid4()
    tool_id = uuid4()
    session = AsyncMock()

    tool = MagicMock()
    tool.id = tool_id
    tool.name = "Cursor Production"
    tool.vendor = "cursor"
    tool.api_endpoint = "https://api.cursor.com/health"
    tool.description = "Team Cursor key"
    tool.credential_label = "Cursor Production"
    tool.credential_expires_at = None
    tool.rotation_reminder_days = 14
    tool.active = True
    tool.api_token_ciphertext = "encrypted"
    tool.last_sync_at = None
    tool.created_at = MagicMock()
    tool.pricing_config = {
        "catalogue_tool_id": str(uuid4()),
        "catalogue_tool_name": "Cursor",
    }

    service = CredentialService(session)
    service._tools.list_by_organization = AsyncMock(return_value=[tool])
    service._teams.list_by_organization = AsyncMock(return_value=[])
    service._collectors_by_tool = AsyncMock(return_value={})

    with patch.object(CredentialService, "_mask_secret", return_value="sk-...abcd"):
        result = await service.list_credentials(org_id)

    service._tools.list_by_organization.assert_awaited_once_with(
        org_id,
        active=None,
        catalogue_only=False,
    )
    assert len(result.data) == 1
    assert result.data[0].catalogue_tool_name == "Cursor"
    assert result.data[0].masked_secret == "sk-...abcd"


def _mock_catalogue_tool(*, tool_id=None, vendor="openai", api_endpoint="https://api.openai.com/v1"):
    tool = MagicMock()
    tool.id = tool_id or uuid4()
    tool.name = "OpenAI"
    tool.vendor = vendor
    tool.api_endpoint = api_endpoint
    tool.pricing_model = "flat_token"
    tool.token_price = 0
    tool.package_allowance = None
    tool.overage_price = None
    tool.pricing_config = {}
    tool.description = "Catalogue entry"
    tool.catalogue_only = True
    tool.active = True
    return tool


def _mock_provider(*, slug="openai", built_in=True):
    provider = MagicMock()
    provider.slug = slug
    provider.built_in = built_in
    provider.active = True
    return provider


@pytest.mark.asyncio
async def test_validate_credential_returns_valid_on_success() -> None:
    org_id = uuid4()
    catalogue_tool = _mock_catalogue_tool()
    session = AsyncMock()
    service = CredentialService(session)
    service._require_catalogue_tool = AsyncMock(return_value=catalogue_tool)
    service._validate_catalogue_tool_for_connect = AsyncMock()

    with patch.object(
        CredentialService,
        "_validate_secret_for_tool",
        new=AsyncMock(),
    ) as validate_mock:
        result = await service.validate_credential(
            org_id,
            CredentialValidateRequest(
                tool_id=catalogue_tool.id,
                secret_value="sk-test-key-12345",
            ),
        )

    validate_mock.assert_awaited_once_with(catalogue_tool, "sk-test-key-12345")
    assert result.valid is True
    assert result.provider == "openai"


@pytest.mark.asyncio
async def test_validate_credential_raises_422_on_invalid_key() -> None:
    org_id = uuid4()
    catalogue_tool = _mock_catalogue_tool()
    session = AsyncMock()
    service = CredentialService(session)
    service._require_catalogue_tool = AsyncMock(return_value=catalogue_tool)
    service._validate_catalogue_tool_for_connect = AsyncMock()

    with patch.object(
        CredentialService,
        "_validate_secret_for_tool",
        new=AsyncMock(side_effect=ProviderValidationError("Invalid API key.")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await service.validate_credential(
                org_id,
                CredentialValidateRequest(
                    tool_id=catalogue_tool.id,
                    secret_value="bad-key",
                ),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Invalid API key."


@pytest.mark.asyncio
async def test_create_credential_raises_422_on_invalid_key() -> None:
    org_id = uuid4()
    catalogue_tool = _mock_catalogue_tool()
    team = MagicMock()
    team.id = uuid4()
    team.tool_ids = []
    session = AsyncMock()
    service = CredentialService(session)
    service._require_catalogue_tool = AsyncMock(return_value=catalogue_tool)
    service._require_team = AsyncMock(return_value=team)
    service._validate_catalogue_tool_for_connect = AsyncMock()
    service._tools.get_by_name = AsyncMock(return_value=None)

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
                    tool_id=catalogue_tool.id,
                    team_id=team.id,
                    secret_value="bad-key",
                ),
            )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Invalid API key."


@pytest.mark.asyncio
async def test_create_credential_sets_pull_interval_on_collector() -> None:
    org_id = uuid4()
    catalogue_tool = _mock_catalogue_tool()
    team = MagicMock()
    team.id = uuid4()
    team.name = "Engineering"
    team.tool_ids = []
    session = AsyncMock()
    service = CredentialService(session)
    service._require_catalogue_tool = AsyncMock(return_value=catalogue_tool)
    service._require_team = AsyncMock(return_value=team)
    service._validate_catalogue_tool_for_connect = AsyncMock()
    service._ensure_tool_on_team = AsyncMock()
    service._sync_collector_token = AsyncMock()
    service._tools.get_by_name = AsyncMock(return_value=None)

    created_tool = MagicMock()
    created_tool.id = uuid4()
    created_tool.name = "Prod key"
    created_tool.vendor = "openai"
    created_tool.api_endpoint = None
    created_tool.description = None
    created_tool.credential_label = "Prod key"
    created_tool.credential_expires_at = None
    created_tool.rotation_reminder_days = None
    created_tool.active = True
    created_tool.last_sync_at = None
    created_tool.created_at = MagicMock()
    created_tool.pricing_config = {
        "catalogue_tool_id": str(catalogue_tool.id),
        "catalogue_tool_name": catalogue_tool.name,
    }
    service._tools.create = AsyncMock(return_value=created_tool)

    created_collector = MagicMock()
    created_collector.pull_interval_minutes = 1440
    service._get_collector = AsyncMock(return_value=created_collector)

    with (
        patch.object(CredentialService, "_validate_secret_for_tool", new=AsyncMock()),
        patch.object(
            CredentialService,
            "_ensure_collector",
            new=AsyncMock(return_value=created_collector),
        ) as ensure_collector,
        patch.object(CredentialService, "_mask_secret", return_value="sk-...abcd"),
    ):
        result = await service.create_credential(
            org_id,
            CredentialCreateRequest(
                label="Prod key",
                tool_id=catalogue_tool.id,
                team_id=team.id,
                secret_value="sk-valid-key",
                pull_interval_minutes=1440,
            ),
        )

    ensure_collector.assert_awaited_once_with(created_tool, pull_interval_minutes=1440)
    assert result.credential.pull_interval_minutes == 1440
    service._tools.create.assert_awaited_once()
    assert service._tools.create.await_args.kwargs["catalogue_only"] is False
