"""Idempotent seed/sync of built-in provider parents and products."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Provider, ProviderParent
from app.settings.builtin_catalog import (
    BUILTIN_PROVIDER_PARENTS,
    BUILTIN_PROVIDER_PRODUCTS,
    RETIRED_PRODUCT_SLUGS,
)


async def sync_builtin_providers(session: AsyncSession) -> None:
    """Upsert built-in catalogue — safe to run on every startup and in production."""
    for parent in BUILTIN_PROVIDER_PARENTS:
        row = await session.get(ProviderParent, parent.slug)
        if row is None:
            session.add(
                ProviderParent(
                    slug=parent.slug,
                    label=parent.label,
                    sort_order=parent.sort_order,
                )
            )
        else:
            row.label = parent.label
            row.sort_order = parent.sort_order

    for product in BUILTIN_PROVIDER_PRODUCTS:
        row = await session.get(Provider, product.slug)
        if row is None:
            session.add(
                Provider(
                    slug=product.slug,
                    label=product.label,
                    description=product.description,
                    parent_slug=product.parent_slug,
                    adapter_key=product.adapter_key,
                    requires_api_endpoint=product.requires_api_endpoint,
                    built_in=True,
                    active=True,
                    sort_order=product.sort_order,
                )
            )
        else:
            row.label = product.label
            row.description = product.description
            row.parent_slug = product.parent_slug
            row.adapter_key = product.adapter_key
            row.requires_api_endpoint = product.requires_api_endpoint
            row.built_in = True
            row.active = True
            row.sort_order = product.sort_order

    if RETIRED_PRODUCT_SLUGS:
        result = await session.execute(
            select(Provider).where(Provider.slug.in_(RETIRED_PRODUCT_SLUGS))
        )
        for row in result.scalars().all():
            row.active = False

    await session.commit()
