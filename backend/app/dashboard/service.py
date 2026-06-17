"""Dashboard analytics over usage.usage_events."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.scope import DashboardScope
from app.dashboard.schemas import (
    ActiveAlertSummary,
    ActiveAlertsResponse,
    CostOverviewWidget,
    DailyBreakdownResponse,
    DailyBreakdownTeam,
    DailyBreakdownUser,
    MyUsageResponse,
    TokenUsageWidget,
    TopConsumerItem,
    TopConsumersResponse,
    TrendGranularityApi,
    TrendPoint,
    TrendsResponse,
    UsageByTeamItem,
    UsageByTeamResponse,
    UsageByToolItem,
    UsageByToolResponse,
)
from app.models.admin import Team, Tool
from app.models.auth import User
from app.models.collector import CollectorConfig, UsageEvent
from app.models.notifications import Threshold, ThresholdEvent
from app.teams.membership_repository import TeamMembershipRepository
from app.teams.repository import TeamRepository
from app.users.repository import UserAdminRepository


def _pct_delta(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100.0, 1)


def effective_token_total(input_tokens: int, output_tokens: int) -> int:
    """Combined token count from input + output (source of truth for dashboards)."""
    return input_tokens + output_tokens


_TOKEN_TOTAL_EXPR = UsageEvent.input_tokens + UsageEvent.output_tokens


def _sum_tokens():
    return func.coalesce(func.sum(_TOKEN_TOTAL_EXPR), 0)


def _entity_id_for_email(email: str) -> UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, email.strip().lower())


def _previous_period(from_dt: datetime, to_dt: datetime) -> tuple[datetime, datetime]:
    duration = to_dt - from_dt
    prev_to = from_dt - timedelta(microseconds=1)
    prev_from = prev_to - duration
    return prev_from, prev_to


@dataclass(frozen=True)
class TokenCostTotals:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: Decimal


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = TeamRepository(session)
        self._memberships = TeamMembershipRepository(session)
        self._users = UserAdminRepository(session)

    async def _org_team_ids(self, organization_id: UUID) -> list[UUID]:
        rows = await self._teams.list_by_organization(organization_id)
        return [row.id for row in rows]

    def _org_usage_predicate(self, organization_id: UUID, org_team_ids: list[UUID]):
        org_tools = select(Tool.id).where(Tool.organization_id == organization_id)
        org_collectors = (
            select(CollectorConfig.id)
            .join(Tool, CollectorConfig.tool_id == Tool.id)
            .where(Tool.organization_id == organization_id)
        )
        clauses = [UsageEvent.organization_id == organization_id]
        if org_team_ids:
            clauses.append(
                and_(
                    UsageEvent.organization_id.is_(None),
                    UsageEvent.team_id.in_(org_team_ids),
                )
            )
        clauses.append(
            and_(
                UsageEvent.organization_id.is_(None),
                UsageEvent.tool_id.in_(org_tools),
            )
        )
        clauses.append(
            and_(
                UsageEvent.organization_id.is_(None),
                UsageEvent.collector_id.in_(org_collectors),
            )
        )
        return or_(*clauses)

    def _scope_filters(
        self,
        scope: DashboardScope,
        org_team_ids: list[UUID],
        *,
        from_dt: datetime,
        to_dt: datetime,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> list:
        conditions = [
            self._org_usage_predicate(scope.organization_id, org_team_ids),
            UsageEvent.occurred_at >= from_dt,
            UsageEvent.occurred_at <= to_dt,
        ]
        if scope.user_id is not None:
            email_match = (
                func.lower(UsageEvent.user_email) == scope.user_email.lower()
                if scope.user_email
                else False
            )
            conditions.append(or_(UsageEvent.user_id == scope.user_id, email_match))
        elif scope.allowed_team_ids is not None:
            conditions.append(UsageEvent.team_id.in_(scope.allowed_team_ids))
        if team_id is not None and scope.user_id is None:
            conditions.append(UsageEvent.team_id == team_id)
        if tool_id is not None:
            conditions.append(UsageEvent.tool_id == tool_id)
        return conditions

    async def _aggregate_totals(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> TokenCostTotals:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=from_dt,
            to_dt=to_dt,
            team_id=team_id,
            tool_id=tool_id,
        )
        result = await self._session.execute(
            select(
                func.coalesce(func.sum(UsageEvent.input_tokens), 0),
                func.coalesce(func.sum(UsageEvent.output_tokens), 0),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            ).where(*filters)
        )
        row = result.one()
        input_tokens = int(row[0])
        output_tokens = int(row[1])
        return TokenCostTotals(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=effective_token_total(input_tokens, output_tokens),
            estimated_cost=Decimal(str(row[2])),
        )

    async def _last_updated_at(self, scope: DashboardScope) -> datetime:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = [self._org_usage_predicate(scope.organization_id, org_team_ids)]
        if scope.user_id is not None:
            email_match = (
                func.lower(UsageEvent.user_email) == scope.user_email.lower()
                if scope.user_email
                else False
            )
            filters.append(or_(UsageEvent.user_id == scope.user_id, email_match))
        elif scope.allowed_team_ids is not None:
            filters.append(UsageEvent.team_id.in_(scope.allowed_team_ids))

        result = await self._session.execute(
            select(func.max(UsageEvent.occurred_at)).where(*filters)
        )
        latest = result.scalar_one_or_none()
        return latest or datetime.now(UTC)

    async def get_tokens(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> TokenUsageWidget:
        totals = await self._aggregate_totals(
            scope, from_dt, to_dt, team_id=team_id, tool_id=tool_id
        )
        return TokenUsageWidget(
            input_tokens=totals.input_tokens,
            output_tokens=totals.output_tokens,
            total_tokens=totals.total_tokens,
            last_updated_at=await self._last_updated_at(scope),
        )

    async def get_cost(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> CostOverviewWidget:
        totals = await self._aggregate_totals(
            scope, from_dt, to_dt, team_id=team_id, tool_id=tool_id
        )
        allowance = await self._package_allowance(scope)
        consumed_pct = None
        if allowance > 0:
            consumed_pct = float(min((totals.estimated_cost / allowance) * 100, 999.9))
        overage = max(totals.estimated_cost - allowance, Decimal("0"))
        return CostOverviewWidget(
            actual_spend=totals.estimated_cost,
            package_allowance=allowance,
            allowance_consumed_pct=consumed_pct,
            overage_cost=overage,
            last_updated_at=await self._last_updated_at(scope),
        )

    async def _package_allowance(self, scope: DashboardScope) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(Tool.package_allowance), 0)).where(
                Tool.organization_id == scope.organization_id,
                Tool.active.is_(True),
            )
        )
        tokens = int(result.scalar_one())
        if tokens <= 0:
            return Decimal("0")
        result = await self._session.execute(
            select(func.coalesce(func.sum(Tool.token_price), 0)).where(
                Tool.organization_id == scope.organization_id,
                Tool.active.is_(True),
                Tool.package_allowance.is_not(None),
            )
        )
        avg_price = Decimal(str(result.scalar_one() or 0))
        return Decimal(tokens) * avg_price

    async def get_usage_by_tool(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        team_id: UUID | None = None,
    ) -> UsageByToolResponse:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=from_dt,
            to_dt=to_dt,
            team_id=team_id,
        )
        result = await self._session.execute(
            select(
                UsageEvent.tool_id,
                Tool.name,
                _sum_tokens(),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .outerjoin(Tool, Tool.id == UsageEvent.tool_id)
            .where(*filters, UsageEvent.tool_id.is_not(None))
            .group_by(UsageEvent.tool_id, Tool.name)
            .order_by(func.sum(_TOKEN_TOTAL_EXPR).desc())
        )
        rows = result.all()
        grand_total = sum(int(r[2]) for r in rows) or 1
        data = [
            UsageByToolItem(
                tool_id=tool_id,
                tool_name=tool_name or "Unknown tool",
                total_tokens=int(total_tokens),
                estimated_cost=Decimal(str(estimated_cost)),
                share_pct=round((int(total_tokens) / grand_total) * 100, 1),
            )
            for tool_id, tool_name, total_tokens, estimated_cost in rows
        ]
        return UsageByToolResponse(
            data=data,
            last_updated_at=await self._last_updated_at(scope),
        )

    async def get_usage_by_team(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        tool_id: UUID | None = None,
    ) -> UsageByTeamResponse:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=from_dt,
            to_dt=to_dt,
            tool_id=tool_id,
        )
        usage_result = await self._session.execute(
            select(
                UsageEvent.team_id,
                _sum_tokens(),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .where(*filters, UsageEvent.team_id.is_not(None))
            .group_by(UsageEvent.team_id)
        )
        usage_map = {
            team_id: (int(tokens), Decimal(str(cost)))
            for team_id, tokens, cost in usage_result.all()
        }

        if scope.allowed_team_ids is not None:
            team_rows = [
                team
                for team in await self._teams.list_by_organization(scope.organization_id)
                if team.id in scope.allowed_team_ids
            ]
        else:
            team_rows = await self._teams.list_by_organization(scope.organization_id)

        data: list[UsageByTeamItem] = []
        for team in team_rows:
            tokens, cost = usage_map.get(team.id, (0, Decimal("0")))
            data.append(
                UsageByTeamItem(
                    team_id=team.id,
                    team_name=team.name,
                    total_tokens=tokens,
                    estimated_cost=cost,
                )
            )
        data.sort(key=lambda row: row.total_tokens, reverse=True)
        return UsageByTeamResponse(
            data=data,
            last_updated_at=await self._last_updated_at(scope),
        )

    async def get_top_consumers(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        limit: int = 10,
        entity: str = "users",
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> TopConsumersResponse:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=from_dt,
            to_dt=to_dt,
            team_id=team_id,
            tool_id=tool_id,
        )

        if entity == "teams":
            result = await self._session.execute(
                select(
                    UsageEvent.team_id,
                    Team.name,
                    _sum_tokens(),
                    func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
                )
                .join(Team, Team.id == UsageEvent.team_id)
                .where(*filters, UsageEvent.team_id.is_not(None))
                .group_by(UsageEvent.team_id, Team.name)
                .order_by(func.sum(_TOKEN_TOTAL_EXPR).desc())
                .limit(limit)
            )
            teams = [
                TopConsumerItem(
                    entity_id=team_id,
                    entity_name=team_name,
                    total_tokens=int(total_tokens),
                    estimated_cost=Decimal(str(estimated_cost)),
                )
                for team_id, team_name, total_tokens, estimated_cost in result.all()
            ]
            return TopConsumersResponse(teams=teams)

        result = await self._session.execute(
            select(
                UsageEvent.user_id,
                UsageEvent.user_email,
                UsageEvent.team_id,
                _sum_tokens(),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
                func.count(UsageEvent.id),
            )
            .where(
                *filters,
                or_(UsageEvent.user_id.is_not(None), UsageEvent.user_email.is_not(None)),
            )
            .group_by(UsageEvent.user_id, UsageEvent.user_email, UsageEvent.team_id)
            .order_by(func.sum(_TOKEN_TOTAL_EXPR).desc())
            .limit(limit)
        )
        users: list[TopConsumerItem] = []
        for user_id, email, event_team_id, total_tokens, estimated_cost, request_count in result.all():
            entity_id = user_id or _entity_id_for_email(email or "")
            display_name = email or "Unknown user"
            user_email = email
            if user_id is not None:
                user_row = await self._users.get_by_id(user_id, scope.organization_id)
                if user_row is not None:
                    display_name = user_row.display_name or user_row.email
                    user_email = user_row.email
            team_name = None
            if event_team_id is not None:
                team_row = await self._teams.get_by_id(event_team_id, scope.organization_id)
                team_name = team_row.name if team_row else None
            users.append(
                TopConsumerItem(
                    entity_id=entity_id,
                    entity_name=display_name,
                    total_tokens=int(total_tokens),
                    estimated_cost=Decimal(str(estimated_cost)),
                    team_id=event_team_id,
                    team_name=team_name,
                    user_email=user_email,
                    request_count=int(request_count),
                )
            )
        return TopConsumersResponse(users=users)

    async def get_trends(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        granularity: TrendGranularityApi,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> TrendsResponse:
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=from_dt,
            to_dt=to_dt,
            team_id=team_id,
            tool_id=tool_id,
        )
        if granularity == "weekly":
            bucket = func.date_trunc("week", UsageEvent.occurred_at)
        elif granularity == "monthly":
            bucket = func.date_trunc("month", UsageEvent.occurred_at)
        else:
            bucket = cast(UsageEvent.occurred_at, Date)

        result = await self._session.execute(
            select(
                bucket,
                _sum_tokens(),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .where(*filters)
            .group_by(bucket)
            .order_by(bucket.asc())
        )
        data = [
            TrendPoint(
                period_start=period if isinstance(period, datetime) else datetime.combine(period, datetime.min.time(), tzinfo=UTC),
                total_tokens=int(total_tokens),
                estimated_cost=Decimal(str(estimated_cost)),
            )
            for period, total_tokens, estimated_cost in result.all()
        ]
        return TrendsResponse(granularity=granularity, data=data)

    async def get_alerts(
        self,
        scope: DashboardScope,
        *,
        team_id: UUID | None = None,
        limit: int = 10,
    ) -> ActiveAlertsResponse:
        conditions = [
            ThresholdEvent.organization_id == scope.organization_id,
            ThresholdEvent.acknowledged_at.is_(None),
        ]
        if team_id is not None:
            conditions.append(ThresholdEvent.team_id == team_id)
        elif scope.allowed_team_ids is not None:
            conditions.append(
                or_(
                    ThresholdEvent.team_id.in_(scope.allowed_team_ids),
                    ThresholdEvent.team_id.is_(None),
                )
            )

        result = await self._session.execute(
            select(ThresholdEvent, Threshold)
            .join(Threshold, Threshold.id == ThresholdEvent.threshold_id)
            .where(*conditions)
            .order_by(ThresholdEvent.triggered_at.desc())
            .limit(limit)
        )
        data: list[ActiveAlertSummary] = []
        for event, threshold in result.all():
            team_name = None
            tool_name = None
            if event.team_id is not None:
                team = await self._teams.get_by_id(event.team_id, scope.organization_id)
                team_name = team.name if team else None
            if threshold.tool_id is not None:
                tool_result = await self._session.execute(
                    select(Tool.name).where(Tool.id == threshold.tool_id)
                )
                tool_name = tool_result.scalar_one_or_none()
            current_value = await self._current_value_for_threshold(threshold, scope)
            data.append(
                ActiveAlertSummary(
                    alert_id=event.id,
                    severity=event.severity,  # type: ignore[arg-type]
                    threshold_type=threshold.threshold_type,
                    tool_name=tool_name,
                    team_name=team_name,
                    current_value=current_value,
                    limit_value=threshold.limit_value,
                    triggered_at=event.triggered_at,
                    title=threshold.name,
                )
            )
        return ActiveAlertsResponse(data=data)

    async def _current_value_for_threshold(
        self,
        threshold: Threshold,
        scope: DashboardScope,
    ) -> Decimal:
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        team_id = threshold.team_id
        tool_id = threshold.tool_id
        totals = await self._aggregate_totals(
            scope,
            month_start,
            now,
            team_id=team_id,
            tool_id=tool_id,
        )
        if threshold.threshold_type == "cost_amount":
            return totals.estimated_cost
        if threshold.threshold_type == "package_utilization_pct":
            allowance = await self._package_allowance(scope)
            if allowance <= 0:
                return Decimal("0")
            return (totals.estimated_cost / allowance) * Decimal("100")
        return Decimal(totals.total_tokens)

    async def get_my_usage(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
        *,
        user_id: UUID | None = None,
    ) -> MyUsageResponse:
        if user_id is not None and scope.user_id is None:
            target = await self._users.get_by_id(user_id, scope.organization_id)
            if target is None:
                return MyUsageResponse(total_tokens=0, estimated_cost=Decimal("0"), by_tool=[])
            personal_scope = DashboardScope(
                organization_id=scope.organization_id,
                allowed_team_ids=scope.allowed_team_ids,
                user_id=target.id,
                user_email=target.email,
            )
        else:
            personal_scope = scope

        totals = await self._aggregate_totals(personal_scope, from_dt, to_dt)
        by_tool = await self.get_usage_by_tool(personal_scope, from_dt, to_dt)
        return MyUsageResponse(
            total_tokens=totals.total_tokens,
            estimated_cost=totals.estimated_cost,
            by_tool=by_tool.data,
        )

    async def get_daily_breakdown(
        self,
        scope: DashboardScope,
        day: datetime,
        *,
        team_id: UUID | None = None,
        tool_id: UUID | None = None,
    ) -> DailyBreakdownResponse:
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters = self._scope_filters(
            scope,
            org_team_ids,
            from_dt=day_start,
            to_dt=day_end,
            team_id=team_id,
            tool_id=tool_id,
        )

        team_result = await self._session.execute(
            select(
                UsageEvent.team_id,
                Team.name,
                _sum_tokens(),
                func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
            )
            .outerjoin(Team, Team.id == UsageEvent.team_id)
            .where(*filters, UsageEvent.team_id.is_not(None))
            .group_by(UsageEvent.team_id, Team.name)
            .order_by(func.sum(_TOKEN_TOTAL_EXPR).desc())
        )
        team_rows = team_result.all()

        data: list[DailyBreakdownTeam] = []
        for event_team_id, team_name, team_tokens, team_cost in team_rows:
            user_filters = [
                *filters,
                UsageEvent.team_id == event_team_id,
            ]
            user_result = await self._session.execute(
                select(
                    UsageEvent.user_id,
                    UsageEvent.user_email,
                    _sum_tokens(),
                    func.coalesce(func.sum(UsageEvent.estimated_cost), 0),
                )
                .where(
                    *user_filters,
                    or_(UsageEvent.user_id.is_not(None), UsageEvent.user_email.is_not(None)),
                )
                .group_by(UsageEvent.user_id, UsageEvent.user_email)
                .order_by(func.sum(_TOKEN_TOTAL_EXPR).desc())
            )
            users: list[DailyBreakdownUser] = []
            for user_id, email, tokens, cost in user_result.all():
                display_name = email or "Unknown user"
                entity_id = user_id or _entity_id_for_email(email or "")
                if user_id is not None:
                    user_row = await self._users.get_by_id(user_id, scope.organization_id)
                    if user_row is not None:
                        display_name = user_row.display_name or user_row.email
                users.append(
                    DailyBreakdownUser(
                        user_id=entity_id,
                        user_name=display_name,
                        tokens=int(tokens),
                        cost=Decimal(str(cost)),
                    )
                )
            data.append(
                DailyBreakdownTeam(
                    team_id=event_team_id,
                    team_name=team_name or "Unknown team",
                    tokens=int(team_tokens),
                    cost=Decimal(str(team_cost)),
                    users=users,
                )
            )
        return DailyBreakdownResponse(data=data)

    async def compute_period_deltas(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
    ) -> dict[str, float]:
        """Token/cost/tool/team percent deltas vs previous period."""
        current = await self._aggregate_totals(scope, from_dt, to_dt)
        prev_from, prev_to = _previous_period(from_dt, to_dt)
        previous = await self._aggregate_totals(scope, prev_from, prev_to)

        org_team_ids = await self._org_team_ids(scope.organization_id)
        filters_current = self._scope_filters(
            scope, org_team_ids, from_dt=from_dt, to_dt=to_dt
        )
        filters_previous = self._scope_filters(
            scope, org_team_ids, from_dt=prev_from, to_dt=prev_to
        )

        async def distinct_count(column, filters) -> int:
            result = await self._session.execute(
                select(func.count(func.distinct(column))).where(*filters, column.is_not(None))
            )
            return int(result.scalar_one())

        active_tools_current = await distinct_count(UsageEvent.tool_id, filters_current)
        active_tools_previous = await distinct_count(UsageEvent.tool_id, filters_previous)
        active_teams_current = await distinct_count(UsageEvent.team_id, filters_current)
        active_teams_previous = await distinct_count(UsageEvent.team_id, filters_previous)

        return {
            "tokens_delta": _pct_delta(float(current.total_tokens), float(previous.total_tokens)),
            "cost_delta": _pct_delta(float(current.estimated_cost), float(previous.estimated_cost)),
            "tools_delta": _pct_delta(float(active_tools_current), float(active_tools_previous)),
            "teams_delta": _pct_delta(float(active_teams_current), float(active_teams_previous)),
        }

    async def team_usage_trends(
        self,
        scope: DashboardScope,
        from_dt: datetime,
        to_dt: datetime,
    ) -> dict[UUID, float]:
        """Per-team token delta vs previous period."""
        prev_from, prev_to = _previous_period(from_dt, to_dt)
        current_rows = (await self.get_usage_by_team(scope, from_dt, to_dt)).data
        previous_rows = (await self.get_usage_by_team(scope, prev_from, prev_to)).data
        previous_map = {row.team_id: row.total_tokens for row in previous_rows}
        return {
            row.team_id: _pct_delta(float(row.total_tokens), float(previous_map.get(row.team_id, 0)))
            for row in current_rows
        }

    async def member_counts_for_teams(
        self,
        organization_id: UUID,
        team_ids: list[UUID],
    ) -> dict[UUID, int]:
        counts: dict[UUID, int] = {}
        for team_id in team_ids:
            memberships = await self._memberships.list_active_for_team(team_id)
            counts[team_id] = len(memberships)
        return counts
