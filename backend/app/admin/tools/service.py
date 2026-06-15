"""AI tool management business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.tools.repository import ToolRepository
from app.admin.tools.schemas import (
    PaginationMeta,
    ToolCreateRequest,
    ToolCsvColumnMapping,
    ToolCsvDailyUsageRow,
    ToolCsvImportPreview,
    ToolCsvImportResponse,
    ToolCsvInspectResponse,
    ToolListResponse,
    ToolResponse,
    ToolSyncResponse,
    ToolUpdateRequest,
)
from app.admin.tools.csv_importer import (
    CsvColumnMapping,
    CsvImportParseError,
    inspect_tool_usage_csv,
    parse_tool_usage_csv,
)
from app.admin.providers.repository import ProviderRepository
from app.admin.providers.validator import validate_provider_token
from app.admin.providers.usage_fetcher import fetch_provider_usage
from app.admin.credentials.repository import CredentialRepository
from app.auth.service import AuthenticatedUser
from app.config import get_settings
from app.core.encryption import decrypt_secret
from app.core.pagination import CursorError
from app.dashboard.service import DashboardService
from app.models.admin import Tool


class ToolConflictError(Exception):
    """Tool name already exists in organization."""


class ToolNotFoundError(Exception):
    """Tool not found."""


class ToolSyncError(Exception):
    """Tool sync/validation failed."""


class ToolCsvImportError(Exception):
    """Tool CSV import failed."""


class ToolService:
    """Tool CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tools = ToolRepository(session)
        self._providers = ProviderRepository(session)
        self._credentials = CredentialRepository(session)
        self._settings = get_settings()

    async def list_tools(
        self,
        user: AuthenticatedUser,
        *,
        active: bool | None = None,
        limit: int = 50,
        cursor: str | None = None,
    ) -> ToolListResponse:
        rows, next_cursor = await self._tools.list_tools(
            user.organization_id,
            active=active,
            limit=limit,
            cursor=cursor,
        )
        return ToolListResponse(
            data=[ToolResponse.model_validate(row) for row in rows],
            meta=PaginationMeta(
                limit=limit,
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            ),
        )

    async def get_tool(
        self, user: AuthenticatedUser, tool_id: uuid.UUID
    ) -> ToolResponse:
        tool = await self._tools.get_by_id(user.organization_id, tool_id)
        if tool is None:
            raise ToolNotFoundError
        return ToolResponse.model_validate(tool)

    async def create_tool(
        self, user: AuthenticatedUser, body: ToolCreateRequest
    ) -> ToolResponse:
        tool = Tool(
            organization_id=user.organization_id,
            name=body.name.strip(),
            vendor=body.vendor.strip(),
            pricing_model=body.pricing_model,
            token_price=body.token_price,
            package_allowance=body.package_allowance,
            overage_price=body.overage_price,
            pricing_config=body.pricing_config,
        )
        try:
            await self._tools.add(tool)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ToolConflictError from exc
        await self._session.refresh(tool)
        return ToolResponse.model_validate(tool)

    async def update_tool(
        self,
        user: AuthenticatedUser,
        tool_id: uuid.UUID,
        body: ToolUpdateRequest,
    ) -> ToolResponse:
        tool = await self._tools.get_by_id(user.organization_id, tool_id)
        if tool is None:
            raise ToolNotFoundError

        updates = body.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            updates["name"] = updates["name"].strip()
        if "vendor" in updates and updates["vendor"] is not None:
            updates["vendor"] = updates["vendor"].strip()
        if "pricing_config" in updates and updates["pricing_config"] is not None:
            merged = {**(tool.pricing_config or {}), **updates["pricing_config"]}
            if updates["pricing_config"].get("force_sync_metrics"):
                merged = DashboardService.apply_sync_metrics(merged)
            updates["pricing_config"] = merged

        pricing_model = updates.get("pricing_model", tool.pricing_model)
        package_allowance = updates.get("package_allowance", tool.package_allowance)
        overage_price = updates.get("overage_price", tool.overage_price)
        if pricing_model == "package_with_overage":
            if package_allowance is None or overage_price is None:
                raise ValueError(
                    "package_allowance and overage_price are required for "
                    "package_with_overage pricing"
                )

        for field, value in updates.items():
            setattr(tool, field, value)
        tool.updated_at = datetime.now(UTC)

        try:
            await self._tools.save(tool)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ToolConflictError from exc
        await self._session.refresh(tool)
        return ToolResponse.model_validate(tool)

    async def sync_tool(
        self, user: AuthenticatedUser, tool_id: uuid.UUID
    ) -> ToolSyncResponse:
        tool = await self._tools.get_by_id(user.organization_id, tool_id)
        if tool is None:
            raise ToolNotFoundError

        config = dict(tool.pricing_config or {})
        if config.get("ingestion_source") == "csv":
            raise ToolSyncError(
                "This tool is updated via CSV import. Re-import a CSV file to refresh usage."
            )

        provider_slug = config.get("provider") or tool.vendor
        provider = await self._providers.get_by_slug(
            user.organization_id, str(provider_slug)
        )
        if provider is None:
            raise ToolSyncError("Provider configuration not found for this tool.")

        credential = await self._credentials.get_primary_for_tool(
            user.organization_id, tool.id
        )
        if credential is None:
            raise ToolSyncError("No stored API credential found for this tool.")

        api_key = decrypt_secret(
            credential.secret_ciphertext,
            self._settings.credential_encryption_key,
        )
        validation = await validate_provider_token(
            provider_slug=provider.slug,
            api_key=api_key,
            usage_api_url=provider.usage_api_url,
        )

        config["last_validation_at"] = datetime.now(UTC).isoformat()
        config["last_validation_message"] = validation.message

        if not validation.valid:
            config["connection_valid"] = False
            config["status"] = "error"
            tool.pricing_config = config
            tool.updated_at = datetime.now(UTC)
            await self._tools.save(tool)
            await self._session.commit()
            await self._session.refresh(tool)
            raise ToolSyncError(validation.message)

        schedule = str(config.get("collection_schedule") or "daily")
        usage = await fetch_provider_usage(
            provider_slug=provider.slug,
            api_key=api_key,
            usage_api_url=provider.usage_api_url,
            collection_schedule=schedule,
            token_price=tool.token_price,
            overage_price=tool.overage_price,
            pricing_config=config,
        )

        if not usage.success:
            config["connection_valid"] = True
            config["status"] = "active"
            config["last_validation_message"] = usage.message
            tool.pricing_config = config
            tool.updated_at = datetime.now(UTC)
            await self._tools.save(tool)
            await self._session.commit()
            await self._session.refresh(tool)
            raise ToolSyncError(usage.message)

        config["connection_valid"] = True
        config["status"] = "active"
        config["last_validation_message"] = usage.message
        config = DashboardService.apply_usage_snapshot(
            config,
            token_count=usage.token_count,
            cost_total=usage.cost_total,
            daily_usage=usage.daily_usage,
        )
        tool.pricing_config = config
        tool.updated_at = datetime.now(UTC)
        await self._tools.save(tool)
        await self._session.commit()
        await self._session.refresh(tool)

        return ToolSyncResponse(
            valid=True,
            message=usage.message,
            tool=ToolResponse.model_validate(tool),
        )

    @staticmethod
    def _mapping_from_schema(
        mapping: ToolCsvColumnMapping | None,
    ) -> CsvColumnMapping | None:
        if mapping is None or not mapping.token_column:
            return None
        return CsvColumnMapping(
            token_column=mapping.token_column,
            cost_column=mapping.cost_column,
            date_column=mapping.date_column,
            date_from_column=mapping.date_from_column,
            date_to_column=mapping.date_to_column,
        )

    @staticmethod
    def _preview_from_csv(
        file_name: str,
        content: bytes,
        mapping: ToolCsvColumnMapping | None = None,
    ) -> ToolCsvImportPreview:
        parsed = parse_tool_usage_csv(
            content,
            mapping=ToolService._mapping_from_schema(mapping),
        )
        return ToolCsvImportPreview(
            file_name=file_name,
            row_count=parsed.row_count,
            token_count=parsed.token_count,
            cost_total=parsed.cost_total,
            date_from=parsed.date_from,
            date_to=parsed.date_to,
            daily_usage=[
                ToolCsvDailyUsageRow(
                    date=row["date"],
                    tokens=int(row["tokens"]),
                    cost=float(row["cost"]),
                )
                for row in parsed.daily_usage
            ],
        )

    async def inspect_csv_import(
        self, user: AuthenticatedUser, *, content: bytes
    ) -> ToolCsvInspectResponse:
        try:
            inspected = inspect_tool_usage_csv(content)
        except CsvImportParseError as exc:
            raise ToolCsvImportError(str(exc)) from exc

        suggested = inspected.suggested_mapping
        return ToolCsvInspectResponse(
            headers=inspected.headers,
            row_count=inspected.row_count,
            format_hint=inspected.format_hint,
            suggested_mapping=ToolCsvColumnMapping(
                token_column=suggested.token_column,
                cost_column=suggested.cost_column,
                date_column=suggested.date_column,
                date_from_column=suggested.date_from_column,
                date_to_column=suggested.date_to_column,
            ),
        )

    async def preview_csv_import(
        self,
        user: AuthenticatedUser,
        *,
        file_name: str,
        content: bytes,
        mapping: ToolCsvColumnMapping | None = None,
    ) -> ToolCsvImportPreview:
        try:
            return self._preview_from_csv(file_name, content, mapping)
        except CsvImportParseError as exc:
            raise ToolCsvImportError(str(exc)) from exc

    async def import_csv(
        self,
        user: AuthenticatedUser,
        *,
        file_name: str,
        content: bytes,
        name: str,
        provider: str,
        mode: str,
        tool_id: uuid.UUID | None,
        replace_existing: bool,
        mapping: ToolCsvColumnMapping | None = None,
    ) -> ToolCsvImportResponse:
        try:
            preview = self._preview_from_csv(file_name, content, mapping)
        except CsvImportParseError as exc:
            raise ToolCsvImportError(str(exc)) from exc

        provider_row = await self._providers.get_by_slug(
            user.organization_id, provider.strip()
        )
        if provider_row is None:
            raise ToolCsvImportError("Selected provider was not found.")

        daily_usage = [
            {"date": row.date, "tokens": row.tokens, "cost": row.cost}
            for row in preview.daily_usage
        ]

        if mode == "update":
            if tool_id is None:
                raise ToolCsvImportError("Select a tool to update.")
            tool = await self._tools.get_by_id(user.organization_id, tool_id)
            if tool is None:
                raise ToolNotFoundError

            config = dict(tool.pricing_config or {})
            config["provider"] = provider.strip()
            config["ingestion_source"] = "csv"
            config["last_csv_import_at"] = datetime.now(UTC).isoformat()
            config["last_csv_file_name"] = file_name
            config["usage_date_from"] = preview.date_from
            config["usage_date_to"] = preview.date_to
            config["connection_valid"] = True
            config["status"] = "active"

            if replace_existing:
                config = DashboardService.apply_usage_snapshot(
                    config,
                    token_count=preview.token_count,
                    cost_total=preview.cost_total,
                    daily_usage=daily_usage,
                )
            else:
                config = DashboardService.merge_usage_snapshot(
                    config,
                    token_count=preview.token_count,
                    cost_total=preview.cost_total,
                    daily_usage=daily_usage,
                )

            tool.name = name.strip()
            tool.vendor = provider.strip()
            tool.pricing_config = config
            tool.active = True
            tool.updated_at = datetime.now(UTC)
            await self._tools.save(tool)
            await self._session.commit()
            await self._session.refresh(tool)

            action = "replaced" if replace_existing else "merged into"
            message = (
                f"CSV usage {action} {tool.name}: "
                f"{preview.token_count:,} tokens, ${preview.cost_total:,.2f} "
                f"({preview.date_from} to {preview.date_to})."
            )
            return ToolCsvImportResponse(
                message=message,
                tool=ToolResponse.model_validate(tool),
                preview=preview,
            )

        existing = await self._tools.get_by_name(user.organization_id, name.strip())
        if existing is not None:
            raise ToolConflictError

        config = {
            "provider": provider.strip(),
            "description": f"Imported from {file_name}",
            "collection_schedule": "daily",
            "ingestion_source": "csv",
            "api_key_masked": "csv-import",
            "connection_valid": True,
            "status": "active",
            "ui_pricing": {
                "model": "per_token",
                "inputCostPer1K": 0,
                "outputCostPer1K": 0,
                "costPerSeat": None,
                "seatCount": None,
                "flatMonthlyCost": None,
                "planName": None,
                "includedTokens": None,
                "overageRate": None,
            },
            "last_csv_import_at": datetime.now(UTC).isoformat(),
            "last_csv_file_name": file_name,
            "usage_date_from": preview.date_from,
            "usage_date_to": preview.date_to,
        }
        config = DashboardService.apply_usage_snapshot(
            config,
            token_count=preview.token_count,
            cost_total=preview.cost_total,
            daily_usage=daily_usage,
        )

        tool = Tool(
            organization_id=user.organization_id,
            name=name.strip(),
            vendor=provider.strip(),
            pricing_model="flat_token",
            token_price=0,
            package_allowance=None,
            overage_price=None,
            pricing_config=config,
            active=True,
        )
        try:
            await self._tools.add(tool)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ToolConflictError from exc
        await self._session.refresh(tool)

        message = (
            f"Created {tool.name} from CSV: "
            f"{preview.token_count:,} tokens, ${preview.cost_total:,.2f} "
            f"({preview.date_from} to {preview.date_to})."
        )
        return ToolCsvImportResponse(
            message=message,
            tool=ToolResponse.model_validate(tool),
            preview=preview,
        )
