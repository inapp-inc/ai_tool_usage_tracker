"""Tool business logic — CRUD and catalogue management."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.collector.adapters.base import ProviderValidationError
from app.collector.adapters.registry import fetch_provider_members, fetch_provider_snapshot, fetch_provider_usage
from app.integration.resolve import resolve_tool_polling_context
from app.collector.service import CollectorService
from app.core.token_crypto import decrypt_token, encrypt_token, mask_token
from app.models.admin import Provider, Tool, ToolPackage
from app.models.collector import CollectorConfig, UsageEvent
from app.tools.catalogue import catalogue_tool_id_from_connected
from app.settings.builtin_catalog import BUILTIN_CATALOGUE_SLUGS
from app.settings.parent_repository import ProviderParentRepository
from app.settings.repository import ProviderRepository
from app.tools.package_schemas import ToolPackageListResponse, ToolPackageResponse
from app.tools.pricing import (
    merge_pricing_config,
    normalize_pricing_config,
    organization_id_from_pricing,
    pricing_config_for_response,
    validate_pricing_model,
    vendor_requires_api_endpoint,
    vendor_requires_organization_id,
)
from app.tools.repository import ToolRepository
from app.tools.synced_members import store_synced_members
from app.tools.schemas import (
    PaginationMeta,
    ToolCreateRequest,
    ToolListResponse,
    ToolMemberResponse,
    ToolMembersListResponse,
    ToolResponse,
    ToolUpdateRequest,
)

SYNC_LOOKBACK_DAYS = 30

logger = logging.getLogger(__name__)


class ToolService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tools = ToolRepository(session)
        self._collectors = CollectorService(session)
        self._providers = ProviderRepository(session)
        self._provider_parents = ProviderParentRepository(session)

    async def list_tools(
        self,
        organization_id: UUID,
        *,
        active: bool | None = None,
        catalogue_only: bool | None = None,
    ) -> ToolListResponse:
        rows = await self._tools.list_by_organization(
            organization_id,
            active=active,
            catalogue_only=catalogue_only,
        )
        provider_order = await self._provider_sort_order()
        provider_map, parent_map = await self._catalogue_lookup_maps()
        rows.sort(
            key=lambda tool: (
                not tool.built_in,
                provider_order.get(tool.vendor, 999),
                (tool.name or "").lower(),
            )
        )
        return ToolListResponse(
            data=[
                self._to_response(row, provider_map=provider_map, parent_map=parent_map)
                for row in rows
            ],
            meta=PaginationMeta(has_more=False),
        )

    async def list_packages(self, tool_id: UUID, organization_id: UUID) -> ToolPackageListResponse:
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
        catalogue_id = catalogue_tool_id_from_connected(tool) or tool.id
        result = await self._session.execute(
            select(ToolPackage)
            .where(ToolPackage.tool_id == catalogue_id, ToolPackage.is_active.is_(True))
            .order_by(ToolPackage.package_name.asc())
        )
        rows = result.scalars().all()
        return ToolPackageListResponse(
            data=[ToolPackageResponse.model_validate(row) for row in rows],
            meta=PaginationMeta(has_more=False),
        )

    async def get_tool(self, organization_id: UUID, tool_id: UUID) -> ToolResponse:
        tool = await self._require_tool(organization_id, tool_id)
        provider_map, parent_map = await self._catalogue_lookup_maps()
        return self._to_response(tool, provider_map=provider_map, parent_map=parent_map)

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

        provider = await self._require_active_provider(body.vendor)
        if body.vendor in BUILTIN_CATALOGUE_SLUGS:
            existing_builtin = await self._tools.get_catalogue_by_vendor(
                organization_id,
                body.vendor,
            )
            if existing_builtin is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Built-in catalogue tool '{provider.label}' already exists. "
                        "Edit the existing entry or add a Custom Integration."
                    ),
                )

        pricing_config = normalize_pricing_config(
            body.pricing_model,
            body.pricing_config,
            package_allowance=body.package_allowance,
            overage_price=body.overage_price,
        )
        pricing_config.setdefault("provider_slug", body.vendor)

        await self._validate_vendor_api_endpoint(
            provider,
            body.api_endpoint,
            integration_config=body.integration_config,
            pricing_config=pricing_config,
        )
        if body.vendor == "custom":
            await self._validate_custom_parent_slug(pricing_config)
        self._validate_polling_config(body.vendor, body.api_endpoint, body.integration_config)

        tool = await self._tools.create(
            organization_id=organization_id,
            name=body.name,
            vendor=body.vendor,
            description=body.description,
            api_endpoint=body.api_endpoint,
            pricing_model=body.pricing_model,
            token_price=body.token_price,
            package_allowance=body.package_allowance,
            overage_price=body.overage_price,
            pricing_config=pricing_config,
            integration_config=body.integration_config or {},
            api_token_ciphertext=encrypt_token(""),
            catalogue_only=True,
        )

        await self._session.commit()
        await self._session.refresh(tool)
        provider_map, parent_map = await self._catalogue_lookup_maps()
        return self._to_response(tool, provider_map=provider_map, parent_map=parent_map)

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
            provider = await self._require_active_provider(body.vendor)
            tool.vendor = body.vendor
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.provider = body.vendor
        else:
            provider = await self._require_active_provider(tool.vendor)

        if "description" in updates:
            tool.description = body.description.strip() if body.description else None

        if "api_endpoint" in updates:
            tool.api_endpoint = body.api_endpoint

        if "integration_config" in updates and body.integration_config is not None:
            tool.integration_config = body.integration_config
            flag_modified(tool, "integration_config")

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

        effective_api_endpoint = (
            body.api_endpoint if "api_endpoint" in updates else tool.api_endpoint
        )
        effective_integration_config = (
            body.integration_config
            if "integration_config" in updates and body.integration_config is not None
            else (tool.integration_config if isinstance(tool.integration_config, dict) else {})
        )
        await self._validate_vendor_api_endpoint(
            provider,
            effective_api_endpoint,
            integration_config=effective_integration_config,
            pricing_config=tool.pricing_config if isinstance(tool.pricing_config, dict) else {},
        )
        if tool.vendor == "custom":
            await self._validate_custom_parent_slug(
                tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
            )
        self._validate_polling_config(
            provider.slug,
            effective_api_endpoint,
            effective_integration_config,
        )

        if "name" in updates and body.name is not None:
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.name = f"{tool.name} collector"

        await self._session.commit()
        await self._session.refresh(tool)
        provider_map, parent_map = await self._catalogue_lookup_maps()
        return self._to_response(tool, provider_map=provider_map, parent_map=parent_map)

    async def delete_tool(self, organization_id: UUID, tool_id: UUID) -> None:
        tool = await self._require_tool(organization_id, tool_id)
        if tool.built_in:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Built-in catalogue tools cannot be deleted.",
            )
        if not tool.catalogue_only:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Live connections are managed in Credentials, not the Tools catalogue.",
            )
        await self._tools.delete(tool)
        await self._session.commit()

    async def sync_tool(self, organization_id: UUID, tool_id: UUID) -> ToolResponse:
        tool = await self._require_tool(organization_id, tool_id)
        api_key = self._decrypt_api_key(tool)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No API key connected. Connect credentials before syncing.",
            )
        await self._apply_sync(tool, api_key)
        await self._session.commit()
        await self._session.refresh(tool)
        provider_map, parent_map = await self._catalogue_lookup_maps()
        return self._to_response(tool, provider_map=provider_map, parent_map=parent_map)

    async def list_tool_members(
        self,
        organization_id: UUID,
        tool_id: UUID,
    ) -> ToolMembersListResponse:
        tool = await self._require_tool(organization_id, tool_id)
        api_key = self._decrypt_api_key(tool)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No API key connected. Connect credentials before listing members.",
            )
        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        try:
            members = await fetch_provider_members(
                tool.vendor,
                api_key,
                pricing_config=pricing_config,
                api_endpoint=tool.api_endpoint,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to fetch members from provider: {str(exc)[:200]}",
            ) from exc

        store_synced_members(tool, members)
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
        pricing_config, api_endpoint, integration_config = await resolve_tool_polling_context(
            self._session,
            tool,
        )
        until = datetime.now(UTC)
        since = await self._usage_sync_since(tool, until)

        logger.info(
            "Tool sync started | tool_id=%s vendor=%s since=%s until=%s",
            tool.id,
            tool.vendor,
            since.isoformat(),
            until.isoformat(),
        )

        try:
            snapshot = await fetch_provider_snapshot(
                tool.vendor,
                api_key,
                package_allowance=tool.package_allowance,
                pricing_config=pricing_config,
                api_endpoint=api_endpoint,
                integration_config=integration_config,
                since=since,
                until=until,
            )

            members = await fetch_provider_members(
                tool.vendor,
                api_key,
                pricing_config=pricing_config,
                api_endpoint=api_endpoint,
            )
            store_synced_members(tool, members)

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

            logger.info(
                "Tool sync finished | tool_id=%s vendor=%s tokens=%s cost=%s members=%s collector_run_error=%s",
                tool.id,
                tool.vendor,
                tool.token_count,
                tool.cost_total,
                len(members),
                run_error,
            )

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
            logger.warning(
                "Tool sync validation failed | tool_id=%s vendor=%s error=%s",
                tool.id,
                tool.vendor,
                tool.last_sync_error,
            )
        except Exception as exc:  # noqa: BLE001
            tool.sync_status = "error"
            tool.last_sync_error = str(exc)[:500]
            tool.last_sync_at = datetime.now(UTC)
            logger.exception(
                "Tool sync failed | tool_id=%s vendor=%s",
                tool.id,
                tool.vendor,
            )

    async def _usage_sync_since(self, tool: Tool, until: datetime) -> datetime:
        """Pull only from last stored event (with overlap), capped by lookback window."""
        lookback_start = until - timedelta(days=SYNC_LOOKBACK_DAYS)
        tool_ids = {tool.id}
        catalogue_id = catalogue_tool_id_from_connected(tool)
        if catalogue_id is not None:
            tool_ids.add(catalogue_id)

        result = await self._session.execute(
            select(func.max(UsageEvent.occurred_at)).where(
                UsageEvent.provider == tool.vendor,
                UsageEvent.tool_id.in_(tool_ids),
            )
        )
        latest = result.scalar_one_or_none()
        if latest is None:
            return lookback_start

        overlap = timedelta(hours=1)
        incremental_since = latest - overlap
        if incremental_since.tzinfo is None:
            incremental_since = incremental_since.replace(tzinfo=UTC)
        return max(incremental_since, lookback_start)

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

    async def _require_active_provider(self, slug: str):
        provider = await self._providers.get_by_slug(slug)
        if provider is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown provider: {slug}",
            )
        if not provider.active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Provider '{slug}' is inactive.",
            )
        return provider

    async def _catalogue_lookup_maps(
        self,
    ) -> tuple[dict[str, Provider], dict[str, object]]:
        providers = await self._providers.list_providers()
        provider_map = {row.slug: row for row in providers}
        parents = await self._provider_parents.list_parents()
        parent_map = {row.slug: row for row in parents}
        return provider_map, parent_map

    async def _validate_custom_parent_slug(self, pricing_config: dict | None) -> None:
        parent_slug = (pricing_config or {}).get("parent_slug")
        if not parent_slug or not str(parent_slug).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provider (parent company) is required for custom tools.",
            )
        parent = await self._provider_parents.get_by_slug(str(parent_slug).strip())
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown provider: {parent_slug}",
            )

    async def _provider_sort_order(self) -> dict[str, int]:
        rows = await self._providers.list_providers()
        return {row.slug: row.sort_order for row in rows}

    @staticmethod
    def _validate_polling_config(
        vendor: str,
        api_endpoint: str | None,
        integration_config: dict | None,
    ) -> None:
        if vendor != "custom":
            return
        config = integration_config or {}
        usage = config.get("usage") if isinstance(config, dict) else None
        if not usage or not isinstance(usage, dict):
            return
        if not api_endpoint or not str(api_endpoint).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="api_endpoint is required when usage polling is enabled.",
            )

    @staticmethod
    async def _validate_vendor_api_endpoint(
        provider: Provider,
        api_endpoint: str | None,
        *,
        integration_config: dict | None = None,
        pricing_config: dict | None = None,
    ) -> None:
        config = integration_config or {}
        pricing = pricing_config or {}

        if vendor_requires_organization_id(provider.slug):
            if not organization_id_from_pricing(pricing):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="GitHub organization ID is required for Microsoft Copilot.",
                )
            return

        if provider.slug == "custom" and isinstance(config, dict) and config.get("usage"):
            if not api_endpoint or not str(api_endpoint).strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="api_endpoint is required when usage polling is enabled.",
                )
            return
        if vendor_requires_api_endpoint(
            provider.slug,
            built_in=provider.built_in,
            requires_api_endpoint=bool(provider.requires_api_endpoint),
        ) and not api_endpoint:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="api_endpoint is required for this provider.",
            )

    @staticmethod
    def _decrypt_api_key(tool: Tool) -> str:
        plain = decrypt_token(tool.api_token_ciphertext)
        return plain.strip()

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
    def _to_response(
        tool: Tool,
        *,
        provider_map: dict[str, Provider] | None = None,
        parent_map: dict[str, object] | None = None,
    ) -> ToolResponse:
        plain = ToolService._decrypt_api_key(tool)
        if plain:
            masked = mask_token(plain)
            if len(plain) > 4:
                masked = f"sk-...{plain[-4:]}"
        else:
            masked = ""
        sync_status = tool.sync_status
        if not tool.active:
            sync_status = "inactive"

        pricing_raw = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        parent_slug: str | None = None
        parent_label: str | None = None
        product_label: str | None = None

        if tool.vendor == "custom":
            product_label = tool.name
            raw_parent = pricing_raw.get("parent_slug")
            parent_slug = str(raw_parent).strip() if raw_parent else None
            if parent_slug and parent_map:
                parent_row = parent_map.get(parent_slug)
                if parent_row is not None:
                    parent_label = getattr(parent_row, "label", None)
        else:
            product = (provider_map or {}).get(tool.vendor)
            if product is not None:
                product_label = product.label
                parent_slug = product.parent_slug
                if product.parent is not None:
                    parent_label = product.parent.label
                elif parent_slug and parent_map:
                    parent_row = parent_map.get(parent_slug)
                    if parent_row is not None:
                        parent_label = getattr(parent_row, "label", None)

        return ToolResponse(
            id=tool.id,
            organization_id=tool.organization_id,
            name=tool.name,
            vendor=tool.vendor,
            billing_type=getattr(tool, "billing_type", None) or "TOKEN_BASED",
            description=tool.description,
            api_endpoint=tool.api_endpoint,
            integration_config=tool.integration_config if isinstance(tool.integration_config, dict) else {},
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
            built_in=bool(tool.built_in),
            parent_slug=parent_slug,
            parent_label=parent_label,
            product_label=product_label,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )
