"""Credentials business logic — live provider connections (separate from tool catalogue)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.collector.adapters.base import ProviderValidationError
from app.collector.adapters.registry import validate_provider_api_key
from app.core.token_crypto import decrypt_token, encrypt_token, mask_token
from app.credentials.schemas import (
    CredentialCreateRequest,
    CredentialCreateResponseBody,
    CredentialListResponse,
    CredentialResponse,
    CredentialUpdateRequest,
    CredentialValidateRequest,
    CredentialValidateResponse,
    PaginationMeta,
)
from app.models.admin import Team, Tool
from app.models.collector import CollectorConfig
from app.settings.repository import ProviderRepository
from app.teams.repository import TeamRepository
from app.tools.pricing import normalize_pricing_config, vendor_requires_api_endpoint
from app.tools.catalogue import catalogue_tool_id_from_connected, team_id_from_connected
from app.tools.repository import ToolRepository


class CredentialService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tools = ToolRepository(session)
        self._teams = TeamRepository(session)
        self._providers = ProviderRepository(session)

    async def list_credentials(self, organization_id: UUID) -> CredentialListResponse:
        tools = await self._tools.list_by_organization(
            organization_id,
            active=None,
            catalogue_only=False,
        )
        teams = await self._teams.list_by_organization(organization_id, active=None)
        teams_by_id = {team.id: team for team in teams}
        team_map = self._build_catalogue_team_map(teams)
        collectors = await self._collectors_by_tool([tool.id for tool in tools])
        data = [
            self._to_response(
                tool,
                self._resolve_team_for_connected_tool(tool, teams_by_id, team_map),
                collectors.get(tool.id),
            )
            for tool in tools
        ]
        return CredentialListResponse(
            data=data,
            meta=PaginationMeta(has_more=False),
        )

    async def validate_credential(
        self,
        organization_id: UUID,
        body: CredentialValidateRequest,
    ) -> CredentialValidateResponse:
        catalogue_tool = await self._require_catalogue_tool(
            organization_id,
            body.tool_id,
        )
        await self._validate_catalogue_tool_for_connect(catalogue_tool)

        try:
            await self._validate_secret_for_tool(catalogue_tool, body.secret_value)
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        return CredentialValidateResponse(
            valid=True,
            provider=catalogue_tool.vendor,
            message="API key verified.",
        )

    async def create_credential(
        self,
        organization_id: UUID,
        body: CredentialCreateRequest,
    ) -> CredentialCreateResponseBody:
        catalogue_tool = await self._require_catalogue_tool(
            organization_id,
            body.tool_id,
        )
        team = await self._require_team(organization_id, body.team_id)
        await self._validate_catalogue_tool_for_connect(catalogue_tool)

        try:
            await self._validate_secret_for_tool(catalogue_tool, body.secret_value)
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        existing = await self._tools.get_by_name(organization_id, body.label)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A connection with this name already exists.",
            )

        source_config = (
            dict(catalogue_tool.pricing_config)
            if isinstance(catalogue_tool.pricing_config, dict)
            else {}
        )
        pricing_config = normalize_pricing_config(
            catalogue_tool.pricing_model,
            source_config,
            package_allowance=catalogue_tool.package_allowance,
            overage_price=catalogue_tool.overage_price,
        )
        pricing_config["catalogue_tool_id"] = str(catalogue_tool.id)
        pricing_config["catalogue_tool_name"] = catalogue_tool.name
        pricing_config["team_id"] = str(team.id)
        pricing_config.setdefault("provider_slug", catalogue_tool.vendor)

        tool = await self._tools.create(
            organization_id=organization_id,
            name=body.label.strip(),
            vendor=catalogue_tool.vendor,
            description=body.description.strip() or catalogue_tool.description,
            api_endpoint=catalogue_tool.api_endpoint,
            pricing_model=catalogue_tool.pricing_model,
            token_price=catalogue_tool.token_price,
            package_allowance=catalogue_tool.package_allowance,
            overage_price=catalogue_tool.overage_price,
            pricing_config=pricing_config,
            api_token_ciphertext=encrypt_token(body.secret_value),
            catalogue_only=False,
        )
        tool.credential_label = body.label.strip()
        tool.credential_expires_at = body.expires_at
        tool.rotation_reminder_days = body.rotation_reminder_days
        tool.last_rotated_at = datetime.now(UTC)
        tool.active = True

        await self._ensure_tool_on_team(team, catalogue_tool.id)
        await self._ensure_collector(tool, pull_interval_minutes=body.pull_interval_minutes)
        await self._sync_collector_token(tool)
        await self._session.commit()
        await self._session.refresh(tool)

        collector = await self._get_collector(tool.id)
        team_map = {tool.id: team}
        return CredentialCreateResponseBody(
            credential=self._to_response(tool, team_map.get(tool.id), collector),
            plain_secret=body.secret_value,
        )

    async def update_credential(
        self,
        organization_id: UUID,
        credential_id: UUID,
        body: CredentialUpdateRequest,
    ) -> CredentialResponse:
        tool = await self._require_connected_tool(organization_id, credential_id)
        updates = body.model_fields_set

        if "label" in updates and body.label is not None:
            tool.credential_label = body.label.strip()
            tool.name = body.label.strip()

        if "description" in updates:
            tool.description = body.description.strip() if body.description else None

        if "expires_at" in updates:
            tool.credential_expires_at = body.expires_at

        if "rotation_reminder_days" in updates:
            tool.rotation_reminder_days = body.rotation_reminder_days

        if "active" in updates and body.active is not None:
            tool.active = body.active
            collector = await self._get_collector(tool.id)
            if collector is not None:
                collector.active = body.active

        if "secret_value" in updates and body.secret_value:
            try:
                await self._validate_secret_for_tool(tool, body.secret_value)
            except ProviderValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(exc),
                ) from exc
            tool.api_token_ciphertext = encrypt_token(body.secret_value)
            tool.last_rotated_at = datetime.now(UTC)
            existing = await self._get_collector(tool.id)
            interval = existing.pull_interval_minutes if existing else 60
            await self._ensure_collector(tool, pull_interval_minutes=interval)
            await self._sync_collector_token(tool)

        if "pull_interval_minutes" in updates and body.pull_interval_minutes is not None:
            await self._ensure_collector(
                tool,
                pull_interval_minutes=body.pull_interval_minutes,
            )

        primary_team: Team | None = None
        if "team_id" in updates and body.team_id is not None:
            primary_team = await self._require_team(organization_id, body.team_id)
            catalogue_id = catalogue_tool_id_from_connected(tool)
            await self._ensure_tool_on_team(primary_team, catalogue_id or tool.id)
            config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
            config = dict(config)
            config["team_id"] = str(primary_team.id)
            tool.pricing_config = config

        await self._session.commit()
        await self._session.refresh(tool)

        if primary_team is None:
            teams = await self._teams.list_by_organization(organization_id, active=None)
            teams_by_id = {row.id: row for row in teams}
            team_map = self._build_catalogue_team_map(teams)
            primary_team = self._resolve_team_for_connected_tool(tool, teams_by_id, team_map)

        collector = await self._get_collector(tool.id)
        return self._to_response(tool, primary_team, collector)

    async def revoke_credential(self, organization_id: UUID, credential_id: UUID) -> None:
        tool = await self._require_connected_tool(organization_id, credential_id)
        tool.active = False
        collector = await self._get_collector(tool.id)
        if collector is not None:
            collector.active = False
        await self._session.commit()

    async def reveal_secret(self, organization_id: UUID, credential_id: UUID) -> str:
        tool = await self._require_connected_tool(organization_id, credential_id)
        return decrypt_token(tool.api_token_ciphertext)

    async def _validate_secret_for_tool(self, tool: Tool, secret_value: str) -> None:
        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        await validate_provider_api_key(
            tool.vendor,
            secret_value,
            pricing_config=pricing_config,
            api_endpoint=tool.api_endpoint,
        )

    async def _require_connected_tool(self, organization_id: UUID, credential_id: UUID) -> Tool:
        tool = await self._tools.get_by_id(credential_id, organization_id)
        if tool is None or tool.catalogue_only:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found.",
            )
        return tool

    async def _require_catalogue_tool(
        self,
        organization_id: UUID,
        tool_id: UUID,
    ) -> Tool:
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None or not tool.catalogue_only:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found in catalogue.",
            )
        if not tool.active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected tool is inactive.",
            )
        return tool

    async def _validate_catalogue_tool_for_connect(self, catalogue_tool: Tool) -> None:
        provider = await self._require_active_provider(catalogue_tool.vendor)
        await self._validate_vendor_api_endpoint(
            catalogue_tool.vendor,
            catalogue_tool.api_endpoint,
            built_in=provider.built_in,
        )

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

    @staticmethod
    async def _validate_vendor_api_endpoint(
        vendor: str,
        api_endpoint: str | None,
        *,
        built_in: bool,
    ) -> None:
        if vendor_requires_api_endpoint(vendor, built_in=built_in) and not api_endpoint:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="api_endpoint is required for this provider.",
            )

    async def _require_team(self, organization_id: UUID, team_id: UUID) -> Team:
        team = await self._teams.get_by_id(team_id, organization_id)
        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found.",
            )
        return team

    async def _ensure_tool_on_team(self, team: Team, tool_id: UUID) -> None:
        tool_id_str = str(tool_id)
        tool_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
        if tool_id_str in tool_ids:
            return
        team.tool_ids = [*tool_ids, tool_id_str]
        flag_modified(team, "tool_ids")

    async def _sync_collector_token(self, tool: Tool) -> None:
        collector = await self._get_collector(tool.id)
        if collector is not None:
            collector.api_token_ciphertext = tool.api_token_ciphertext
            collector.active = tool.active

    async def _ensure_collector(
        self,
        tool: Tool,
        *,
        pull_interval_minutes: int = 60,
    ) -> CollectorConfig:
        collector = await self._get_collector(tool.id)
        if collector is not None:
            collector.pull_interval_minutes = pull_interval_minutes
            return collector
        collector = CollectorConfig(
            name=f"{tool.name} collector",
            provider=tool.vendor,
            api_token_ciphertext=tool.api_token_ciphertext,
            pull_interval_minutes=pull_interval_minutes,
            active=tool.active,
            tool_id=tool.id,
        )
        self._session.add(collector)
        await self._session.flush()
        return collector

    async def _collectors_by_tool(
        self,
        tool_ids: list[UUID],
    ) -> dict[UUID, CollectorConfig]:
        if not tool_ids:
            return {}
        result = await self._session.execute(
            select(CollectorConfig).where(CollectorConfig.tool_id.in_(tool_ids))
        )
        return {row.tool_id: row for row in result.scalars().all() if row.tool_id is not None}

    async def _get_collector(self, tool_id: UUID) -> CollectorConfig | None:
        result = await self._session.execute(
            select(CollectorConfig).where(CollectorConfig.tool_id == tool_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _build_catalogue_team_map(teams: list[Team]) -> dict[UUID, Team]:
        """Map catalogue tool ids assigned on teams to their team."""
        mapping: dict[UUID, Team] = {}
        for team in teams:
            tool_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
            for raw_tool_id in tool_ids:
                try:
                    tool_uuid = UUID(str(raw_tool_id))
                except ValueError:
                    continue
                mapping.setdefault(tool_uuid, team)
        return mapping

    @classmethod
    def _resolve_team_for_connected_tool(
        cls,
        tool: Tool,
        teams_by_id: dict[UUID, Team],
        catalogue_team_map: dict[UUID, Team],
    ) -> Team | None:
        assigned_team_id = team_id_from_connected(tool)
        if assigned_team_id is not None:
            return teams_by_id.get(assigned_team_id)
        catalogue_id, _ = cls._catalogue_refs(tool)
        if catalogue_id is not None:
            return catalogue_team_map.get(catalogue_id)
        return None

    @staticmethod
    def _build_tool_team_map(teams: list[Team]) -> dict[UUID, Team]:
        return CredentialService._build_catalogue_team_map(teams)

    @staticmethod
    def _mask_secret(tool: Tool) -> str:
        plain = decrypt_token(tool.api_token_ciphertext)
        if len(plain) > 4:
            return f"sk-...{plain[-4:]}"
        return mask_token(plain)

    @classmethod
    def _catalogue_refs(cls, tool: Tool) -> tuple[UUID | None, str | None]:
        config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        raw_id = config.get("catalogue_tool_id")
        raw_name = config.get("catalogue_tool_name")
        catalogue_id: UUID | None = None
        if raw_id:
            try:
                catalogue_id = UUID(str(raw_id))
            except ValueError:
                catalogue_id = None
        catalogue_name = str(raw_name).strip() if raw_name else None
        return catalogue_id, catalogue_name

    @classmethod
    def _to_response(
        cls,
        tool: Tool,
        team: Team | None,
        collector: CollectorConfig | None = None,
    ) -> CredentialResponse:
        catalogue_tool_id, catalogue_tool_name = cls._catalogue_refs(tool)
        return CredentialResponse(
            id=tool.id,
            label=(tool.credential_label or tool.name).strip(),
            description=(tool.description or "").strip(),
            vendor=tool.vendor,
            catalogue_tool_id=catalogue_tool_id,
            catalogue_tool_name=catalogue_tool_name,
            tool_id=tool.id,
            tool_name=catalogue_tool_name or tool.name,
            team_id=team.id if team else None,
            team_name=team.name if team else None,
            api_endpoint=tool.api_endpoint,
            masked_secret=cls._mask_secret(tool),
            status="active" if tool.active else "inactive",
            pull_interval_minutes=collector.pull_interval_minutes if collector else 60,
            rotation_reminder_days=int(tool.rotation_reminder_days)
            if tool.rotation_reminder_days is not None
            else None,
            expires_at=tool.credential_expires_at,
            last_used_at=tool.last_sync_at,
            created_at=tool.created_at,
            created_by_name=None,
        )
