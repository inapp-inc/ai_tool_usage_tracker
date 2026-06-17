"""Tool data access."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Tool


class ToolRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active: bool | None = None,
    ) -> list[Tool]:
        stmt = select(Tool).where(Tool.organization_id == organization_id)
        if active is not None:
            stmt = stmt.where(Tool.active == active)
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
        api_token_ciphertext: str,
    ) -> Tool:
        tool = Tool(
            organization_id=organization_id,
            name=name.strip(),
            vendor=vendor,
            description=description.strip() if description else None,
            api_endpoint=api_endpoint,
            pricing_model=pricing_model,
            token_price=token_price,
            package_allowance=package_allowance,
            overage_price=overage_price,
            pricing_config=pricing_config,
            active=True,
            api_token_ciphertext=api_token_ciphertext,
            sync_status="inactive",
        )
        self._session.add(tool)
        await self._session.flush()
        return tool

    async def delete(self, tool: Tool) -> None:
        await self._session.delete(tool)
        await self._session.flush()
