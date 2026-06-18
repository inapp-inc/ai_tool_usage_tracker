"""Tests for built-in provider catalogue seed."""

import pytest

from app.settings.builtin_catalog import (
    BUILTIN_PRODUCT_SLUGS,
    BUILTIN_PROVIDER_PRODUCTS,
    RETIRED_PRODUCT_SLUGS,
)
from app.settings.seed import sync_builtin_providers


def test_builtin_catalog_includes_required_products() -> None:
    slugs = {product.slug for product in BUILTIN_PROVIDER_PRODUCTS}
    assert slugs >= {
        "openai",
        "anthropic",
        "google",
        "azure_openai",
        "copilot",
        "bedrock",
        "cursor",
        "figma",
        "custom",
    }


def test_retired_slugs_not_in_active_catalogue() -> None:
    assert not RETIRED_PRODUCT_SLUGS & BUILTIN_PRODUCT_SLUGS


@pytest.mark.asyncio
async def test_sync_builtin_providers_upserts_parents_and_products() -> None:
    from unittest.mock import AsyncMock, MagicMock

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
    )

    await sync_builtin_providers(session)

    assert session.add.call_count > 0
    session.commit.assert_awaited_once()
