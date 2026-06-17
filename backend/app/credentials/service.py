"""Credentials business logic — one credential per connected AI tool."""

from datetime import UTC, datetime
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
from app.teams.repository import TeamRepository
from app.tools.repository import ToolRepository


class CredentialService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._tools = ToolRepository(session)
        self._teams = TeamRepository(session)

    async def list_credentials(self, organization_id: UUID) -> CredentialListResponse:
        tools = await self._tools.list_by_organization(organization_id, active=None)
        teams = await self._teams.list_by_organization(organization_id, active=None)
        team_map = self._build_tool_team_map(teams)
        data = [self._to_response(tool, team_map.get(tool.id)) for tool in tools]
        return CredentialListResponse(
            data=data,
            meta=PaginationMeta(has_more=False),
        )

    async def validate_credential(
        self,
        organization_id: UUID,
        body: CredentialValidateRequest,
    ) -> CredentialValidateResponse:
        tool = await self._require_tool(organization_id, body.tool_id)
        try:
            await self._validate_secret_for_tool(tool, body.secret_value)
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        return CredentialValidateResponse(
            valid=True,
            provider=tool.vendor,
            message="API key verified.",
        )

    async def create_credential(
        self,
        organization_id: UUID,
        body: CredentialCreateRequest,
    ) -> CredentialCreateResponseBody:
        tool = await self._require_tool(organization_id, body.tool_id)
        team = await self._require_team(organization_id, body.team_id)

        try:
            await self._validate_secret_for_tool(tool, body.secret_value)
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        tool.credential_label = body.label.strip()
        tool.description = body.description.strip() or None
        tool.credential_environment = body.environment
        tool.credential_expires_at = body.expires_at
        tool.rotation_reminder_days = body.rotation_reminder_days
        tool.api_token_ciphertext = encrypt_token(body.secret_value)
        tool.last_rotated_at = datetime.now(UTC)
        tool.active = True

        await self._ensure_tool_on_team(team, tool.id)
        await self._ensure_collector(tool)
        await self._sync_collector_token(tool)
        await self._session.commit()
        await self._session.refresh(tool)

        team_map = {tool.id: team}
        return CredentialCreateResponseBody(
            credential=self._to_response(tool, team_map.get(tool.id)),
            plain_secret=body.secret_value,
        )

    async def update_credential(
        self,
        organization_id: UUID,
        credential_id: UUID,
        body: CredentialUpdateRequest,
    ) -> CredentialResponse:
        tool = await self._require_tool(organization_id, credential_id)
        updates = body.model_fields_set

        if "label" in updates and body.label is not None:
            tool.credential_label = body.label.strip()

        if "description" in updates:
            tool.description = body.description.strip() if body.description else None

        if "environment" in updates and body.environment is not None:
            tool.credential_environment = body.environment

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
            await self._ensure_collector(tool)
            await self._sync_collector_token(tool)

        primary_team: Team | None = None
        if "team_id" in updates and body.team_id is not None:
            primary_team = await self._require_team(organization_id, body.team_id)
            await self._ensure_tool_on_team(primary_team, tool.id)

        await self._session.commit()
        await self._session.refresh(tool)

        if primary_team is None:
            teams = await self._teams.list_by_organization(organization_id, active=None)
            team_map = self._build_tool_team_map(teams)
            primary_team = team_map.get(tool.id)

        return self._to_response(tool, primary_team)

    async def revoke_credential(self, organization_id: UUID, credential_id: UUID) -> None:
        tool = await self._require_tool(organization_id, credential_id)
        tool.active = False
        collector = await self._get_collector(tool.id)
        if collector is not None:
            collector.active = False
        await self._session.commit()

    async def reveal_secret(self, organization_id: UUID, credential_id: UUID) -> str:
        tool = await self._require_tool(organization_id, credential_id)
        return decrypt_token(tool.api_token_ciphertext)

    async def _validate_secret_for_tool(self, tool: Tool, secret_value: str) -> None:
        pricing_config = tool.pricing_config if isinstance(tool.pricing_config, dict) else {}
        await validate_provider_api_key(
            tool.vendor,
            secret_value,
            pricing_config=pricing_config,
            api_endpoint=tool.api_endpoint,
        )

    async def _require_tool(self, organization_id: UUID, tool_id: UUID) -> Tool:
        tool = await self._tools.get_by_id(tool_id, organization_id)
        if tool is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found.",
            )
        return tool

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

    async def _ensure_collector(self, tool: Tool) -> CollectorConfig:
        collector = await self._get_collector(tool.id)
        if collector is not None:
            return collector
        collector = CollectorConfig(
            name=f"{tool.name} collector",
            provider=tool.vendor,
            api_token_ciphertext=tool.api_token_ciphertext,
            pull_interval_minutes=60,
            active=tool.active,
            tool_id=tool.id,
        )
        self._session.add(collector)
        await self._session.flush()
        return collector

    async def _get_collector(self, tool_id: UUID) -> CollectorConfig | None:
        result = await self._session.execute(
            select(CollectorConfig).where(CollectorConfig.tool_id == tool_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _build_tool_team_map(teams: list[Team]) -> dict[UUID, Team]:
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

    @staticmethod
    def _mask_secret(tool: Tool) -> str:
        plain = decrypt_token(tool.api_token_ciphertext)
        if len(plain) > 4:
            return f"sk-...{plain[-4:]}"
        return mask_token(plain)

    @classmethod
    def _to_response(cls, tool: Tool, team: Team | None) -> CredentialResponse:
        environment = tool.credential_environment
        if environment not in ("production", "sandbox"):
            environment = "production"

        return CredentialResponse(
            id=tool.id,
            label=(tool.credential_label or tool.name).strip(),
            description=(tool.description or "").strip(),
            tool_id=tool.id,
            tool_name=tool.name,
            team_id=team.id if team else None,
            team_name=team.name if team else None,
            environment=environment,  # type: ignore[arg-type]
            masked_secret=cls._mask_secret(tool),
            status="active" if tool.active else "inactive",
            rotation_reminder_days=int(tool.rotation_reminder_days)
            if tool.rotation_reminder_days is not None
            else None,
            expires_at=tool.credential_expires_at,
            last_used_at=tool.last_sync_at,
            created_at=tool.created_at,
            created_by_name=None,
        )
