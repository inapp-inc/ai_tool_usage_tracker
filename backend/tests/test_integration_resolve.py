"""Tests for resolve_tool_polling_context."""

from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.integration.resolve import resolve_tool_polling_context
from app.models.admin import Tool


def _tool(**overrides) -> Tool:
    tool = MagicMock(spec=Tool)
    tool.id = overrides.get("id", uuid4())
    tool.pricing_config = overrides.get("pricing_config", {})
    tool.api_endpoint = overrides.get("api_endpoint")
    tool.integration_config = overrides.get("integration_config", {})
    return tool


@pytest.mark.asyncio
async def test_resolve_merges_organization_id_from_catalogue() -> None:
    catalogue_id = uuid4()
    connected = _tool(
        pricing_config={"catalogue_tool_id": str(catalogue_id)},
        integration_config={},
    )
    catalogue = _tool(
        id=catalogue_id,
        pricing_config={"organization_id": "acme-corp"},
        api_endpoint="https://api.github.com",
        integration_config={"usage": {"url": "https://example.com"}},
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=catalogue)

    pricing_config, api_endpoint, integration_config = await resolve_tool_polling_context(
        session,
        connected,
    )

    assert pricing_config["organization_id"] == "acme-corp"
    assert api_endpoint == "https://api.github.com"
    assert integration_config.get("usage")
