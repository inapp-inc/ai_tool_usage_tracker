"""Seed built-in catalogue tool rows per organization."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.token_crypto import encrypt_token
from app.models.admin import Tool
from app.models.auth import Organization
from app.settings.builtin_catalog import (
    BUILTIN_PROVIDER_PRODUCTS,
    COPILOT_DEFAULT_API_ENDPOINT,
    COPILOT_INTEGRATION_CONFIG,
)
from app.tools.pricing import normalize_pricing_config


def _pick_canonical_catalogue_row(rows: list[Tool]) -> Tool:
    """Prefer an existing built-in row, otherwise the oldest catalogue entry."""
    return sorted(rows, key=lambda row: (not row.built_in, row.created_at))[0]


def _retire_duplicate_catalogue_rows(canonical: Tool, rows: list[Tool]) -> None:
    """Deactivate extra catalogue-only rows for the same vendor."""
    for row in rows:
        if row.id == canonical.id:
            continue
        if not row.catalogue_only:
            continue
        row.active = False
        row.built_in = False


async def sync_org_builtin_catalogue_tools(
    session: AsyncSession,
    organization_id: UUID,
) -> None:
    """Upsert one non-deletable catalogue tool per built-in provider for an org."""
    for product in BUILTIN_PROVIDER_PRODUCTS:
        if product.slug == "custom":
            continue

        result = await session.execute(
            select(Tool).where(
                Tool.organization_id == organization_id,
                Tool.catalogue_only.is_(True),
                Tool.vendor == product.slug,
            )
        )
        existing_rows = list(result.scalars().all())
        if not existing_rows:
            pricing_config = normalize_pricing_config(
                "flat_token",
                {"provider_slug": product.slug},
                package_allowance=None,
                overage_price=None,
            )
            session.add(
                Tool(
                    organization_id=organization_id,
                    name=product.label,
                    vendor=product.slug,
                    description=product.description,
                    api_endpoint=COPILOT_DEFAULT_API_ENDPOINT if product.slug == "copilot" else None,
                    integration_config=dict(COPILOT_INTEGRATION_CONFIG)
                    if product.slug == "copilot"
                    else {},
                    pricing_model="flat_token",
                    token_price=Decimal("0"),
                    package_allowance=None,
                    overage_price=None,
                    pricing_config=pricing_config,
                    active=True,
                    api_token_ciphertext=encrypt_token(""),
                    sync_status="inactive",
                    catalogue_only=True,
                    built_in=True,
                )
            )
            continue

        canonical = _pick_canonical_catalogue_row(existing_rows)
        _retire_duplicate_catalogue_rows(canonical, existing_rows)

        canonical.built_in = True
        canonical.catalogue_only = True
        canonical.active = True
        canonical.name = product.label
        if product.description:
            canonical.description = product.description
        if product.slug == "copilot":
            canonical.api_endpoint = COPILOT_DEFAULT_API_ENDPOINT
            if not isinstance(canonical.integration_config, dict) or not canonical.integration_config.get(
                "usage"
            ):
                canonical.integration_config = dict(COPILOT_INTEGRATION_CONFIG)


async def sync_all_org_builtin_catalogue_tools(session: AsyncSession) -> None:
    """Provision built-in catalogue tools for every organization — safe on every startup."""
    result = await session.execute(select(Organization))
    for org in result.scalars().all():
        await sync_org_builtin_catalogue_tools(session, org.id)
    await session.commit()
