"""Tests for provider parent companies API."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.settings.service import ProviderService


@pytest.mark.asyncio
async def test_list_provider_parents_returns_seed_companies() -> None:
    session = AsyncMock()
    service = ProviderService(session)

    parent = MagicMock()
    parent.slug = "microsoft"
    parent.label = "Microsoft"
    parent.sort_order = 40
    service._parents.list_parents = AsyncMock(return_value=[parent])

    result = await service.list_provider_parents()

    assert len(result.data) == 1
    assert result.data[0].slug == "microsoft"
    assert result.data[0].label == "Microsoft"
