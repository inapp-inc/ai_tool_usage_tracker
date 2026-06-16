"""Threshold / alert business logic."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.notifications import Threshold, ThresholdEvent
from app.teams.repository import TeamRepository
from app.thresholds.repository import ThresholdEventRepository, ThresholdRepository
from app.thresholds.schemas import (
    PaginationMeta,
    ThresholdCreateRequest,
    ThresholdEventListResponse,
    ThresholdEventResponse,
    ThresholdListResponse,
    ThresholdResponse,
    ThresholdUpdateRequest,
)


class ThresholdService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._thresholds = ThresholdRepository(session)
        self._events = ThresholdEventRepository(session)
        self._teams = TeamRepository(session)

    async def list_thresholds(self, organization_id: UUID) -> ThresholdListResponse:
        rows = await self._thresholds.list_by_organization(organization_id)
        stats = await self._events.stats_for_thresholds(
            organization_id,
            [row.id for row in rows],
        )
        team_names = await self._team_name_map(organization_id, rows)
        data = [
            self._to_threshold_response(
                row,
                team_names.get(row.team_id) if row.team_id else None,
                stats.get(row.id, (0, None)),
            )
            for row in rows
        ]
        return ThresholdListResponse(data=data, meta=PaginationMeta(has_more=False))

    async def create_threshold(
        self,
        organization_id: UUID,
        body: ThresholdCreateRequest,
    ) -> ThresholdResponse:
        await self._validate_scope_refs(organization_id, body.scope, body.team_id, body.tool_id)
        self._validate_limit(body.threshold_type, body.limit_value)

        row = await self._thresholds.create(
            organization_id=organization_id,
            name=body.name.strip(),
            threshold_type=body.threshold_type,
            scope=body.scope,
            tool_id=body.tool_id,
            team_id=body.team_id,
            user_id=body.user_id,
            limit_value=body.limit_value,
            severity=body.severity,
            notify_email=body.notify_email,
            notify_in_app=body.notify_in_app,
            webhook_url=body.webhook_url.strip() if body.webhook_url else None,
            email_recipients=body.email_recipients,
            active=body.active,
        )
        await self._session.commit()
        await self._session.refresh(row)
        team_name = await self._resolve_team_name(organization_id, row.team_id)
        return self._to_threshold_response(row, team_name, (0, None))

    async def update_threshold(
        self,
        organization_id: UUID,
        threshold_id: UUID,
        body: ThresholdUpdateRequest,
    ) -> ThresholdResponse:
        row = await self._require_threshold(organization_id, threshold_id)
        updates = body.model_fields_set

        if "name" in updates and body.name is not None:
            row.name = body.name.strip()

        if "threshold_type" in updates and body.threshold_type is not None:
            row.threshold_type = body.threshold_type

        if "scope" in updates and body.scope is not None:
            row.scope = body.scope

        if "tool_id" in updates:
            row.tool_id = body.tool_id

        if "team_id" in updates:
            row.team_id = body.team_id

        if "user_id" in updates:
            row.user_id = body.user_id

        if "limit_value" in updates and body.limit_value is not None:
            row.limit_value = body.limit_value

        if "severity" in updates and body.severity is not None:
            row.severity = body.severity

        if "notify_email" in updates and body.notify_email is not None:
            row.notify_email = body.notify_email

        if "notify_in_app" in updates and body.notify_in_app is not None:
            row.notify_in_app = body.notify_in_app

        if "webhook_url" in updates:
            row.webhook_url = body.webhook_url.strip() if body.webhook_url else None

        if "email_recipients" in updates and body.email_recipients is not None:
            row.email_recipients = body.email_recipients

        if "active" in updates and body.active is not None:
            row.active = body.active

        scope = row.scope
        await self._validate_scope_refs(organization_id, scope, row.team_id, row.tool_id)
        self._validate_limit(row.threshold_type, row.limit_value)

        await self._session.commit()
        await self._session.refresh(row)
        stats = await self._events.stats_for_thresholds(organization_id, [row.id])
        team_name = await self._resolve_team_name(organization_id, row.team_id)
        return self._to_threshold_response(row, team_name, stats.get(row.id, (0, None)))

    async def delete_threshold(self, organization_id: UUID, threshold_id: UUID) -> None:
        row = await self._require_threshold(organization_id, threshold_id)
        await self._thresholds.delete(row)
        await self._session.commit()

    async def list_events(self, organization_id: UUID) -> ThresholdEventListResponse:
        events = await self._events.list_by_organization(organization_id)
        if not events:
            return ThresholdEventListResponse(data=[], meta=PaginationMeta(has_more=False))

        threshold_ids = {event.threshold_id for event in events}
        thresholds = await self._thresholds.list_by_organization(organization_id)
        threshold_map = {row.id: row for row in thresholds if row.id in threshold_ids}
        team_names = await self._team_name_map(
            organization_id,
            [row for row in thresholds if row.id in threshold_ids],
        )

        user_names = await self._acknowledger_names(events)
        data: list[ThresholdEventResponse] = []
        for event in events:
            threshold = threshold_map.get(event.threshold_id)
            if threshold is None:
                continue
            team_name = None
            if event.team_id:
                team_name = team_names.get(event.team_id)
            elif threshold.team_id:
                team_name = team_names.get(threshold.team_id)
            data.append(
                ThresholdEventResponse(
                    id=event.id,
                    rule_id=threshold.id,
                    rule_name=threshold.name,
                    severity=event.severity,  # type: ignore[arg-type]
                    message=event.message,
                    team_name=team_name,
                    triggered_at=event.triggered_at,
                    acknowledged_at=event.acknowledged_at,
                    acknowledged_by=user_names.get(event.acknowledged_by),
                )
            )
        return ThresholdEventListResponse(data=data, meta=PaginationMeta(has_more=False))

    async def acknowledge_event(
        self,
        organization_id: UUID,
        event_id: UUID,
        user: User,
    ) -> ThresholdEventResponse:
        event = await self._events.get_by_id(event_id, organization_id)
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert event not found.",
            )
        if event.acknowledged_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Alert event already acknowledged.",
            )

        event.acknowledged_at = datetime.now(UTC)
        event.acknowledged_by = user.id
        await self._session.commit()
        await self._session.refresh(event)

        threshold = await self._require_threshold(organization_id, event.threshold_id)
        team_name = await self._resolve_team_name(organization_id, event.team_id or threshold.team_id)
        display_name = user.display_name.strip() if user.display_name else user.email
        return ThresholdEventResponse(
            id=event.id,
            rule_id=threshold.id,
            rule_name=threshold.name,
            severity=event.severity,  # type: ignore[arg-type]
            message=event.message,
            team_name=team_name,
            triggered_at=event.triggered_at,
            acknowledged_at=event.acknowledged_at,
            acknowledged_by=display_name,
        )

    async def _require_threshold(self, organization_id: UUID, threshold_id: UUID) -> Threshold:
        row = await self._thresholds.get_by_id(threshold_id, organization_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Threshold not found.",
            )
        return row

    async def _validate_scope_refs(
        self,
        organization_id: UUID,
        scope: str,
        team_id: UUID | None,
        tool_id: UUID | None,
    ) -> None:
        if scope == "organization":
            return
        if scope in ("team", "user") and team_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="team_id is required for team and user scoped thresholds.",
            )
        if scope == "team" and team_id is not None:
            team = await self._teams.get_by_id(team_id, organization_id)
            if team is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Team not found.",
                )
        if scope == "tool" and tool_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tool_id is required for tool scoped thresholds.",
            )

    @staticmethod
    def _validate_limit(threshold_type: str, limit_value: Decimal) -> None:
        if threshold_type == "package_utilization_pct" and (
            limit_value < 0 or limit_value > 100
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Budget utilization must be between 0 and 100.",
            )

    async def _team_name_map(
        self,
        organization_id: UUID,
        rows: list[Threshold],
    ) -> dict[UUID, str]:
        team_ids = {row.team_id for row in rows if row.team_id is not None}
        if not team_ids:
            return {}
        teams = await self._teams.list_by_organization(organization_id, active=None)
        return {team.id: team.name for team in teams if team.id in team_ids}

    async def _resolve_team_name(
        self,
        organization_id: UUID,
        team_id: UUID | None,
    ) -> str | None:
        if team_id is None:
            return None
        team = await self._teams.get_by_id(team_id, organization_id)
        return team.name if team else None

    async def _acknowledger_names(
        self,
        events: list[ThresholdEvent],
    ) -> dict[UUID | None, str | None]:
        from sqlalchemy import select

        from app.models.auth import User as AuthUser

        user_ids = {event.acknowledged_by for event in events if event.acknowledged_by}
        if not user_ids:
            return {}
        result = await self._session.execute(
            select(AuthUser).where(AuthUser.id.in_(user_ids))
        )
        users = list(result.scalars().all())
        return {
            user.id: (user.display_name.strip() if user.display_name else user.email)
            for user in users
        }

    @staticmethod
    def _to_threshold_response(
        row: Threshold,
        team_name: str | None,
        stats: tuple[int, object],
    ) -> ThresholdResponse:
        trigger_count, last_triggered = stats
        recipients = row.email_recipients if isinstance(row.email_recipients, list) else []
        return ThresholdResponse(
            id=row.id,
            name=row.name,
            threshold_type=row.threshold_type,  # type: ignore[arg-type]
            scope=row.scope,  # type: ignore[arg-type]
            tool_id=row.tool_id,
            team_id=row.team_id,
            user_id=row.user_id,
            team_name=team_name,
            limit_value=row.limit_value,
            severity=row.severity,  # type: ignore[arg-type]
            active=row.active,
            notify_email=row.notify_email,
            notify_in_app=row.notify_in_app,
            webhook_url=row.webhook_url,
            email_recipients=[str(email) for email in recipients],
            trigger_count=trigger_count,
            last_triggered_at=last_triggered,  # type: ignore[arg-type]
            created_at=row.created_at,
        )
