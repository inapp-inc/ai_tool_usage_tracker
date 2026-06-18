"""Tool data access."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Tool
from app.tools.catalogue import (
    connected_to_catalogue_map,
    find_connected_for_catalogue,
    find_connected_for_team,
)


class ToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active: bool | None = None,
        catalogue_only: bool | None = None,
    ) -> list[Tool]:
        stmt = select(Tool).where(Tool.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Tool.active == active)
        if catalogue_only is not None:
            stmt = stmt.where(Tool.catalogue_only == catalogue_only)
        stmt = stmt.order_by(Tool.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, tool_id: UUID, organization_id: UUID) -> Tool | None:
        result = await self._session.execute(
            select(Tool).where(
                Tool.id == tool_id,
                Tool.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, organization_id: UUID, name: str) -> Tool | None:
        normalized = name.strip()
        result = await self._session.execute(
            select(Tool).where(
                Tool.organization_id == organization_id,
                func.lower(Tool.name) == normalized.lower(),
            )
        )
        return result.scalar_one_or_none()

    async def get_catalogue_by_vendor(
        self,
        organization_id: UUID,
        vendor: str,
    ) -> Tool | None:
        result = await self._session.execute(
            select(Tool).where(
                Tool.organization_id == organization_id,
                Tool.catalogue_only.is_(True),
                Tool.vendor == vendor,
                Tool.active.is_(True),
            )
        )
        rows = list(result.scalars().all())
        if not rows:
            return None
        return sorted(rows, key=lambda row: (not row.built_in, row.created_at))[0]

    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        vendor: str,
        description: str | None,
        api_endpoint: str | None,
        pricing_model: str,
        token_price: Decimal,
        package_allowance: int | None,
        overage_price: Decimal | None,
        pricing_config: dict,
        integration_config: dict | None = None,
        api_token_ciphertext: str,
        catalogue_only: bool = False,
        built_in: bool = False,
    ) -> Tool:
        tool = Tool(
            organization_id=organization_id,
            name=name.strip(),
            vendor=vendor,
            description=description.strip() if description else None,
            api_endpoint=api_endpoint,
            integration_config=integration_config or {},
            pricing_model=pricing_model,
            token_price=token_price,
            package_allowance=package_allowance,
            overage_price=overage_price,
            pricing_config=pricing_config,
            active=True,
            api_token_ciphertext=api_token_ciphertext,
            sync_status="inactive",
            catalogue_only=catalogue_only,
            built_in=built_in,
        )
        self._session.add(tool)
        await self._session.flush()
        return tool

    async def delete(self, tool: Tool) -> None:
        await self._session.delete(tool)
        await self._session.flush()

    async def find_connected_for_catalogue(
        self,
        organization_id: UUID,
        catalogue_tool_id: UUID,
    ) -> Tool | None:
        connected = await self.list_by_organization(
            organization_id,
            active=None,
            catalogue_only=False,
        )
        return find_connected_for_catalogue(connected, catalogue_tool_id)

    async def list_connected_for_team(
        self,
        organization_id: UUID,
        *,
        team_id: UUID,
        catalogue_tool_ids: set[UUID],
    ) -> list[Tool]:
        all_tools = await self.list_by_organization(organization_id, active=None)
        id_to_catalogue = connected_to_catalogue_map(all_tools)
        connected = [tool for tool in all_tools if not tool.catalogue_only]
        return find_connected_for_team(
            connected,
            team_id=team_id,
            catalogue_tool_ids=catalogue_tool_ids,
            id_to_catalogue=id_to_catalogue,
        )
