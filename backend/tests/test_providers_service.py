"""Tests for provider settings service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.settings.schemas import ProviderCreateRequest
from app.settings.service import ProviderService


@pytest.mark.asyncio
async def test_create_provider_persists_custom_slug() -> None:
    session = AsyncMock()
    service = ProviderService(session)
    service._providers.get_by_slug = AsyncMock(return_value=None)

    created = MagicMock()
    created.slug = "my_internal_llm"
    created.label = "My Internal LLM"
    created.description = "Private gateway"
    created.logo_url = None
    created.parent = None
    created.parent_slug = None
    created.adapter_key = None
    created.requires_api_endpoint = False
    created.built_in = False
    created.active = True
    created.sort_order = 0
    service._providers.create = AsyncMock(return_value=created)

    result = await service.create_provider(
        ProviderCreateRequest(
            slug="my_internal_llm",
            label="My Internal LLM",
            description="Private gateway",
        )
    )

    assert result.slug == "my_internal_llm"
    assert result.built_in is False
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_built_in_provider_returns_409() -> None:
    session = AsyncMock()
    service = ProviderService(session)
    built_in = MagicMock()
    built_in.built_in = True
    service._providers.get_by_slug = AsyncMock(return_value=built_in)

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_provider("openai")

    assert exc_info.value.status_code == 409
