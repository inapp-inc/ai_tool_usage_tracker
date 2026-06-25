"""Sync tool_packages rows for catalogue tools."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Tool, ToolPackage
from app.tools.billing_types import billing_type_for_vendor
from app.tools.package_catalog import packages_for_vendor


async def sync_packages_for_catalogue_tool(
    session: AsyncSession,
    tool: Tool,
) -> None:
    """Upsert built-in packages for a catalogue tool row."""
    if not tool.catalogue_only:
        return

    vendor = tool.vendor
    default_billing_type = billing_type_for_vendor(vendor)
    seeds = packages_for_vendor(vendor)
    if not seeds:
        return

    result = await session.execute(
        select(ToolPackage).where(ToolPackage.tool_id == tool.id)
    )
    existing_by_name = {row.package_name: row for row in result.scalars().all()}

    for seed in seeds:
        billing_type = seed.billing_type or default_billing_type
        row = existing_by_name.get(seed.package_name)
        if row is None:
            session.add(
                ToolPackage(
                    tool_id=tool.id,
                    package_name=seed.package_name,
                    billing_type=billing_type,
                    monthly_price=seed.monthly_price,
                    yearly_price=seed.yearly_price,
                    token_limit=seed.token_limit,
                    request_limit=seed.request_limit,
                    seat_limit=seed.seat_limit,
                    credit_limit=seed.credit_limit,
                    is_active=True,
                )
            )
            continue

        row.billing_type = billing_type
        row.monthly_price = seed.monthly_price
        row.yearly_price = seed.yearly_price
        row.token_limit = seed.token_limit
        row.request_limit = seed.request_limit
        row.seat_limit = seed.seat_limit
        row.credit_limit = seed.credit_limit
        row.is_active = True


async def sync_packages_for_organization(
    session: AsyncSession,
    organization_id: UUID,
) -> None:
    result = await session.execute(
        select(Tool).where(
            Tool.organization_id == organization_id,
            Tool.catalogue_only.is_(True),
            Tool.active.is_(True),
        )
    )
    for tool in result.scalars().all():
        await sync_packages_for_catalogue_tool(session, tool)
