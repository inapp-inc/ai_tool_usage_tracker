"""Tool business logic — CRUD, API key validation, sync."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.collector.adapters.base import ProviderValidationError
from app.collector.adapters.registry import fetch_provider_members, fetch_provider_snapshot, validate_provider_api_key
from app.collector.service import CollectorService
from app.core.token_crypto import decrypt_token, encrypt_token, mask_token
from app.models.admin import Tool
from app.models.collector import CollectorConfig
from app.tools.pricing import (
    merge_pricing_config,
    normalize_pricing_config,
    pricing_config_for_response,
    validate_pricing_model,
)
from app.tools.repository import ToolRepository
from app.tools.schemas import (
    PaginationMeta,
    ToolCreateRequest,
    ToolListResponse,
    ToolMemberResponse,
    ToolMembersListResponse,
    ToolResponse,
    ToolUpdateRequest,
)

DEFAULT_PULL_INTERVAL_MINUTES = 60
SYNC_LOOKBACK_DAYS = 30


class ToolService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tools = ToolRepository(session)
        self._collectors = CollectorService(session)

    async def list_tools(
        self,
        organization_id: UUID,
        *,
        active: bool | None = None,
    ) -> ToolListResponse:
        rows = await self._tools.list_by_organization(organization_id, active=active)
        return ToolListResponse(
            data=[self._to_response(row) for row in rows],
            meta=PaginationMeta(has_more=False),
        )

    async def get_tool(self, organization_id: UUID, tool_id: UUID) -> ToolResponse:
        tool = await self._require_tool(organization_id, tool_id)
        return self._to_response(tool)

    async def create_tool(
        self,
        organization_id: UUID,
        body: ToolCreateRequest,
    ) -> ToolResponse:
        validate_pricing_model(body.pricing_model)
        self._validate_package_pricing(body.pricing_model, body.package_allowance, body.overage_price)

        existing = await self._tools.get_by_name(organization_id, body.name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A tool with this name already exists in the organization.",
            )

        pricing_config = normalize_pricing_config(
            body.pricing_model,
            body.pricing_config,
            package_allowance=body.package_allowance,
            overage_price=body.overage_price,
        )
        pricing_config.setdefault("provider_slug", body.vendor)

        try:
            await validate_provider_api_key(
                body.vendor,
                body.api_key,
                pricing_config=pricing_config,
            )
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        tool = await self._tools.create(
            organization_id=organization_id,
            name=body.name,
            vendor=body.vendor,
            description=body.description,
            pricing_model=body.pricing_model,
            token_price=body.token_price,
            package_allowance=body.package_allowance,
            overage_price=body.overage_price,
            pricing_config=pricing_config,
            api_token_ciphertext=encrypt_token(body.api_key),
        )

        collector = CollectorConfig(
            name=f"{tool.name} collector",
            provider=tool.vendor,
            api_token_ciphertext=tool.api_token_ciphertext,
            pull_interval_minutes=DEFAULT_PULL_INTERVAL_MINUTES,
            active=tool.active,
            tool_id=tool.id,
        )
        self._session.add(collector)
        await self._session.commit()
        await self._session.refresh(tool)

        await self._apply_sync(tool, body.api_key)
        await self._session.commit()
        await self._session.refresh(tool)
        return self._to_response(tool)

    async def update_tool(
        self,
        organization_id: UUID,
        tool_id: UUID,
        body: ToolUpdateRequest,
    ) -> ToolResponse:
        tool = await self._require_tool(organization_id, tool_id)
        updates = body.model_fields_set

        if "name" in updates and body.name is not None:
            if body.name.strip().lower() != tool.name.lower():
                duplicate = await self._tools.get_by_name(organization_id, body.name)
                if duplicate is not None and duplicate.id != tool.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="A tool with this name already exists in the organization.",
                    )
            tool.name = body.name.strip()

        if "vendor" in updates and body.vendor is not None:
            tool.vendor = body.vendor

        if "description" in updates:
            tool.description = body.description.strip() if body.description else None

        if "pricing_model" in updates and body.pricing_model is not None:
            validate_pricing_model(body.pricing_model)
            tool.pricing_model = body.pricing_model

        if "token_price" in updates and body.token_price is not None:
            tool.token_price = body.token_price

        if "package_allowance" in updates:
            tool.package_allowance = body.package_allowance

        if "overage_price" in updates:
            tool.overage_price = body.overage_price

        if "pricing_config" in updates and body.pricing_config is not None:
            tool.pricing_config = merge_pricing_config(tool.pricing_config, body.pricing_config)
            flag_modified(tool, "pricing_config")

        if any(
            field in updates
            for field in ("pricing_model", "package_allowance", "overage_price", "pricing_config")
        ):
            tool.pricing_config = normalize_pricing_config(
                tool.pricing_model,
                tool.pricing_config if isinstance(tool.pricing_config, dict) else {},
                package_allowance=tool.package_allowance,
                overage_price=tool.overage_price,
            )
            if tool.package_allowance is None and tool.pricing_config.get("included_tokens") is not None:
                try:
                    tool.package_allowance = int(tool.pricing_config["included_tokens"])
                except (TypeError, ValueError):
                    pass
            if tool.overage_price is None and tool.pricing_config.get("overage_rate") is not None:
                try:
                    tool.overage_price = Decimal(str(tool.pricing_config["overage_rate"]))
                except Exception:  # noqa: BLE001
                    pass
            flag_modified(tool, "pricing_config")

        if "active" in updates and body.active is not None:
            tool.active = body.active
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.active = body.active

        pricing_model = tool.pricing_model
        self._validate_package_pricing(
            pricing_model,
            tool.package_allowance,
            tool.overage_price,
        )

        api_key = body.api_key if "api_key" in updates and body.api_key else None
        if api_key:
            try:
                await validate_provider_api_key(
                    tool.vendor,
                    api_key,
                    pricing_config=tool.pricing_config,
                )
            except ProviderValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            tool.api_token_ciphertext = encrypt_token(api_key)
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.api_token_ciphertext = tool.api_token_ciphertext
                if "vendor" in updates and body.vendor is not None:
                    collector.provider = body.vendor

        if "name" in updates and body.name is not None:
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.name = f"{tool.name} collector"

        await self._session.commit()
        await self._session.refresh(tool)
        return self._to_response(tool)

    async def delete_tool(self, organization_id: UUID, tool_id: UUID) -> None:
        tool = await self._require_tool(organization_id, tool_id)
        await self._tools.delete(tool)
        await self._session.commit()

    async def sync_tool(self, organization_id: UUID, tool_id: UUID) -> ToolResponse:
        tool = await self._require_tool(organization_id, tool_id)
        api_key = decrypt_token(tool.api_token_ciphertext)
        await self._apply_sync(tool, api_key)
        await self._session.commit()
        await self._session.refresh(tool)
        return self._to_response(tool)

    async def list_tool_members(
        self,
        organization_id: UUID,
        tool_id: UUID,
    ) -> ToolMembersListResponse:
        tool = await self._require_tool(organization_id, tool_id)
        api_key = decrypt_token(tool.api_token_ciphertext)
        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        try:
            members = await fetch_provider_members(
                tool.vendor,
                api_key,
                pricing_config=pricing_config,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to fetch members from provider: {str(exc)[:200]}",
            ) from exc

        tool.member_count = len(members)
        await self._session.commit()

        return ToolMembersListResponse(
            data=[
                ToolMemberResponse(email=member.email, name=member.name)
                for member in members
            ],
            member_count=len(members),
        )

    async def _apply_sync(self, tool: Tool, api_key: str) -> None:
        collector = await self._get_collector(tool.id)
        run_error: str | None = None
        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        until = datetime.now(UTC)
        since = until - timedelta(days=SYNC_LOOKBACK_DAYS)

        try:
            snapshot = await fetch_provider_snapshot(
                tool.vendor,
                api_key,
                package_allowance=tool.package_allowance,
                pricing_config=pricing_config,
            )

            members = await fetch_provider_members(
                tool.vendor,
                api_key,
                pricing_config=pricing_config,
            )
            tool.member_count = len(members)

            if collector is not None:
                run = await self._collectors.run_collector(
                    collector.id,
                    since=since,
                    until=until,
                )
                await self._session.refresh(tool)
                if run is not None and run.status == "failed":
                    run_error = run.error_message

            tool.token_count = snapshot.tokens_used
            tool.cost_total = snapshot.total_cost
            tool.balance_tokens = snapshot.balance_tokens
            tool.last_sync_at = datetime.now(UTC)
            tool.last_sync_error = run_error

            if not tool.active:
                tool.sync_status = "inactive"
            elif run_error:
                tool.sync_status = "error"
            else:
                tool.sync_status = snapshot.sync_status

            if snapshot.input_cost_per_1k is not None or snapshot.output_cost_per_1k is not None:
                config = dict(tool.pricing_config)
                if snapshot.input_cost_per_1k is not None:
                    config["input_cost_per_1k"] = float(snapshot.input_cost_per_1k)
                if snapshot.output_cost_per_1k is not None:
                    config["output_cost_per_1k"] = float(snapshot.output_cost_per_1k)
                tool.pricing_config = config
                flag_modified(tool, "pricing_config")
        except ProviderValidationError as exc:
            tool.sync_status = "error"
            tool.last_sync_error = str(exc)[:500]
            tool.last_sync_at = datetime.now(UTC)
        except Exception as exc:  # noqa: BLE001
            tool.sync_status = "error"
            tool.last_sync_error = str(exc)[:500]
            tool.last_sync_at = datetime.now(UTC)

    async def _get_collector(self, tool_id: UUID) -> CollectorConfig | None:
        result = await self._session.execute(
            select(CollectorConfig).where(CollectorConfig.tool_id == tool_id)
        )
        return result.scalar_one_or_none()

    async def _require_tool(self, organization_id: UUID, tool_id: UUID) -> Tool:
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found.",
            )
        return tool

    @staticmethod
    def _validate_package_pricing(
        pricing_model: str,
        package_allowance: int | None,
        overage_price: Decimal | None,
    ) -> None:
        if pricing_model != "package_with_overage":
            return
        if package_allowance is None or overage_price is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="package_allowance and overage_price are required for package_with_overage.",
            )

    @staticmethod
    def _to_response(tool: Tool) -> ToolResponse:
        plain = decrypt_token(tool.api_token_ciphertext)
        masked = mask_token(plain)
        if len(plain) > 4:
            masked = f"sk-...{plain[-4:]}"
        sync_status = tool.sync_status
        if not tool.active:
            sync_status = "inactive"
        return ToolResponse(
            id=tool.id,
            organization_id=tool.organization_id,
            name=tool.name,
            vendor=tool.vendor,
            description=tool.description,
            pricing_model=tool.pricing_model,
            token_price=tool.token_price,
            package_allowance=tool.package_allowance,
            overage_price=tool.overage_price,
            pricing_config=pricing_config_for_response(
                tool.pricing_model,
                tool.pricing_config if isinstance(tool.pricing_config, dict) else {},
                package_allowance=tool.package_allowance,
                overage_price=tool.overage_price,
            ),
            active=tool.active,
            api_token_masked=masked,
            token_count=int(tool.token_count),
            cost_total=tool.cost_total,
            balance_tokens=tool.balance_tokens,
            member_count=int(tool.member_count),
            sync_status=sync_status,  # type: ignore[arg-type]
            last_sync_at=tool.last_sync_at,
            last_sync_error=tool.last_sync_error,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )
