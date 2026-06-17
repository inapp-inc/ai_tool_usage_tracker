"""Collector business logic — CRUD, pull execution, usage persistence."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.collector.adapters.base import ProviderValidationError
from app.collector.adapters.registry import get_adapter, validate_provider_api_key
from app.collector.schemas import (
    CollectorCreateRequest,
    CollectorResponse,
    CollectorRunResponse,
    CollectorUpdateRequest,
    UsageEventResponse,
    UsageSummaryResponse,
)
from app.core.token_crypto import decrypt_token, encrypt_token, mask_token
from app.models.admin import Team, Tool
from app.models.collector import CollectorConfig, CollectorRun, UsageEvent
from app.tools.catalogue import catalogue_tool_id_from_connected, team_id_from_connected


def _to_collector_response(config: CollectorConfig) -> CollectorResponse:
    plain = decrypt_token(config.api_token_ciphertext)
    return CollectorResponse(
        id=config.id,
        name=config.name,
        provider=config.provider,
        api_token_masked=mask_token(plain),
        pull_interval_minutes=config.pull_interval_minutes,
        active=config.active,
        last_run_at=config.last_run_at,
        last_success_at=config.last_success_at,
        last_error=config.last_error,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


class CollectorService:
    """Manage collector configs and execute token pulls."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_collectors(self) -> list[CollectorResponse]:
        result = await self._session.execute(
            select(CollectorConfig).order_by(CollectorConfig.created_at.desc())
        )
        return [_to_collector_response(row) for row in result.scalars().all()]

    async def get_collector(self, collector_id: UUID) -> CollectorResponse | None:
        config = await self._session.get(CollectorConfig, collector_id)
        if config is None:
            return None
        return _to_collector_response(config)

    async def create_collector(self, body: CollectorCreateRequest) -> CollectorResponse:
        try:
            await validate_provider_api_key(
                body.provider,
                body.api_token,
                pricing_config=body.pricing_config,
            )
        except ProviderValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        config = CollectorConfig(
            name=body.name,
            provider=body.provider,
            api_token_ciphertext=encrypt_token(body.api_token),
            pull_interval_minutes=body.pull_interval_minutes,
            active=body.active,
        )
        self._session.add(config)
        await self._session.commit()
        await self._session.refresh(config)
        return _to_collector_response(config)

    async def update_collector(
        self,
        collector_id: UUID,
        body: CollectorUpdateRequest,
    ) -> CollectorResponse | None:
        config = await self._session.get(CollectorConfig, collector_id)
        if config is None:
            return None

        if body.name is not None:
            config.name = body.name
        if body.api_token is not None:
            try:
                await validate_provider_api_key(
                    config.provider,
                    body.api_token,
                    pricing_config=body.pricing_config or {},
                )
            except ProviderValidationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc
            config.api_token_ciphertext = encrypt_token(body.api_token)
        if body.pull_interval_minutes is not None:
            config.pull_interval_minutes = body.pull_interval_minutes
        if body.active is not None:
            config.active = body.active

        await self._session.commit()
        await self._session.refresh(config)
        return _to_collector_response(config)

    async def delete_collector(self, collector_id: UUID) -> bool:
        config = await self._session.get(CollectorConfig, collector_id)
        if config is None:
            return False
        await self._session.delete(config)
        await self._session.commit()
        return True

    async def list_runs(self, collector_id: UUID) -> list[CollectorRunResponse]:
        result = await self._session.execute(
            select(CollectorRun)
            .where(CollectorRun.collector_id == collector_id)
            .order_by(CollectorRun.created_at.desc())
            .limit(50)
        )
        return [CollectorRunResponse.model_validate(row) for row in result.scalars().all()]

    async def run_collector(
        self,
        collector_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> CollectorRunResponse | None:
        config = await self._session.get(CollectorConfig, collector_id)
        if config is None:
            return None

        run = CollectorRun(
            collector_id=config.id,
            status="running",
            started_at=datetime.now(UTC),
        )
        self._session.add(run)
        config.last_run_at = datetime.now(UTC)
        await self._session.flush()

        try:
            records = await self._pull_usage(config, since=since, until=until)
            ingested = await self._persist_records(config, records)
            run.status = "completed"
            run.records_ingested = ingested
            run.completed_at = datetime.now(UTC)
            config.last_success_at = run.completed_at
            config.last_error = None
        except Exception as exc:  # noqa: BLE001 — store sanitized message on run row
            run.status = "failed"
            run.error_message = str(exc)[:500]
            run.completed_at = datetime.now(UTC)
            config.last_error = run.error_message

        await self._session.commit()
        await self._session.refresh(run)
        return CollectorRunResponse.model_validate(run)

    async def _pull_usage(
        self,
        config: CollectorConfig,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ):
        adapter = get_adapter(config.provider)
        token = decrypt_token(config.api_token_ciphertext)
        until = until or datetime.now(UTC)
        since = since or (until - timedelta(minutes=config.pull_interval_minutes))

        pricing_config: dict = {}
        if config.tool_id is not None:
            tool = await self._session.get(Tool, config.tool_id)
            if tool is not None and isinstance(tool.pricing_config, dict):
                pricing_config = tool.pricing_config

        try:
            return await adapter.fetch_usage(
                token,
                since=since,
                until=until,
                pricing_config=pricing_config,
            )
        except TypeError:
            return await adapter.fetch_usage(token, since=since, until=until)

    async def _persist_records(self, config: CollectorConfig, records) -> int:
        organization_id = None
        team_id = None
        tool_id = config.tool_id
        if tool_id is not None:
            tool = await self._session.get(Tool, tool_id)
            if tool is not None:
                organization_id = tool.organization_id
                team_id = await self._resolve_team_id_for_tool(tool)

        ingested = 0
        for record in records:
            stmt = (
                insert(UsageEvent)
                .values(
                    collector_id=config.id,
                    organization_id=organization_id,
                    team_id=team_id,
                    tool_id=tool_id,
                    provider=config.provider,
                    model=record.model,
                    occurred_at=record.occurred_at,
                    input_tokens=record.input_tokens,
                    output_tokens=record.output_tokens,
                    total_tokens=record.input_tokens + record.output_tokens,
                    estimated_cost=record.estimated_cost,
                    vendor_event_id=record.vendor_event_id,
                )
                .on_conflict_do_nothing(
                    index_elements=["provider", "vendor_event_id"],
                    index_where=UsageEvent.vendor_event_id.is_not(None),
                )
            )
            result = await self._session.execute(stmt)
            if result.rowcount:
                ingested += 1
        return ingested

    async def _resolve_team_id_for_tool(self, tool: Tool) -> UUID | None:
        team_id = team_id_from_connected(tool)
        if team_id is not None:
            return team_id
        catalogue_id = catalogue_tool_id_from_connected(tool)
        if catalogue_id is None:
            return None
        result = await self._session.execute(
            select(Team).where(Team.organization_id == tool.organization_id)
        )
        catalogue_id_str = str(catalogue_id)
        for team in result.scalars().all():
            raw_ids = team.tool_ids if isinstance(team.tool_ids, list) else []
            if catalogue_id_str in {str(value) for value in raw_ids}:
                return team.id
        return None

    async def list_usage_events(
        self,
        *,
        collector_id: UUID | None = None,
        limit: int = 100,
    ) -> list[UsageEventResponse]:
        query = select(UsageEvent).order_by(UsageEvent.occurred_at.desc()).limit(limit)
        if collector_id is not None:
            query = query.where(UsageEvent.collector_id == collector_id)
        result = await self._session.execute(query)
        return [UsageEventResponse.model_validate(row) for row in result.scalars().all()]

    async def usage_summary(
        self,
        *,
        collector_id: UUID | None = None,
    ) -> UsageSummaryResponse:
        query = select(
            func.coalesce(func.sum(UsageEvent.total_tokens), 0),
            func.coalesce(func.sum(UsageEvent.estimated_cost), Decimal("0")),
            func.count(UsageEvent.id),
            func.min(UsageEvent.occurred_at),
            func.max(UsageEvent.occurred_at),
        )
        if collector_id is not None:
            query = query.where(UsageEvent.collector_id == collector_id)

        result = await self._session.execute(query)
        total_tokens, total_cost, event_count, period_from, period_to = result.one()
        return UsageSummaryResponse(
            total_tokens=int(total_tokens),
            total_cost=Decimal(str(total_cost)),
            event_count=int(event_count),
            period_from=period_from,
            period_to=period_to,
        )

    async def list_active_collectors(self) -> list[CollectorConfig]:
        result = await self._session.execute(
            select(CollectorConfig).where(CollectorConfig.active.is_(True))
        )
        return list(result.scalars().all())
