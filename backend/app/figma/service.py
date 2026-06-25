"""Figma billing CSV analytics for Insights."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.figma.pricing import (
    figma_configured_subscription,
    figma_paid_credit_cost,
    figma_pricing_from_assignment,
)
from app.figma.schemas import (
    FigmaBillingCostTrendPoint,
    FigmaBillingCreditTotals,
    FigmaBillingInsightsResponse,
    FigmaBillingPeriodOption,
    FigmaBillingPeriodRow,
    FigmaBillingPeriodUser,
    FigmaBillingPeriodUsersResponse,
    FigmaBillingTopUser,
    FigmaInsight,
)
from app.models.admin import TeamTool, Tool
from app.models.figma import FigmaBillingImport, FigmaBillingImportUser
from app.models.ingestion import Upload
from app.teams.figma_billing_metrics import active_upload_filter, figma_import_overlaps_period
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import catalogue_tool_id_from_connected


class FigmaAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._team_tools = TeamToolRepository(session)

    async def get_billing_insights(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        from_date: date,
        to_date: date,
        billing_period_start: date | None = None,
        billing_period_end: date | None = None,
        billing_import_id: uuid.UUID | None = None,
    ) -> FigmaBillingInsightsResponse:
        assignment = await self._team_figma_assignment(team_id, tool_id=tool_id)
        pricing = figma_pricing_from_assignment(assignment)
        configured = self._configured_pricing(pricing, assignment)

        all_rows = await self._billing_import_rows(
            team_id,
            tool_id,
            from_date,
            to_date,
            apply_date_filter=False,
        )
        available_periods = [
            FigmaBillingPeriodOption(
                import_id=str(billing_import.id),
                usage_period_start=billing_import.usage_period_start,
                usage_period_end=billing_import.usage_period_end,
                upload_filename=upload.filename if upload else None,
            )
            for billing_import, upload in all_rows
        ]

        active_import_id = billing_import_id
        active_start = billing_period_start
        active_end = billing_period_end
        if active_import_id is not None:
            selected = next(
                (
                    (billing_import, upload)
                    for billing_import, upload in all_rows
                    if billing_import.id == active_import_id
                ),
                None,
            )
            if selected is not None:
                active_start = selected[0].usage_period_start
                active_end = selected[0].usage_period_end
        elif active_start is None or active_end is None:
            if available_periods:
                active_start = available_periods[0].usage_period_start
                active_end = available_periods[0].usage_period_end
                active_import_id = uuid.UUID(available_periods[0].import_id)

        if active_import_id is not None:
            rows = [
                (billing_import, upload)
                for billing_import, upload in all_rows
                if billing_import.id == active_import_id
            ]
        elif active_start is not None and active_end is not None:
            rows = [
                (billing_import, upload)
                for billing_import, upload in all_rows
                if billing_import.usage_period_start == active_start
                and billing_import.usage_period_end == active_end
            ]
        else:
            rows = []
        imports_outside_filter = False

        import_ids = [billing_import.id for billing_import, _upload in rows]
        users_by_import = await self._users_for_imports(import_ids)

        seat_cost = Decimal("0")
        paid_cost = Decimal("0")
        total_cost = Decimal("0")
        full_seat_count = 0
        view_seat_count = 0
        user_count = 0
        total_seat_credits = Decimal("0")
        total_paid_credits = Decimal("0")
        period_stubs: list[dict] = []

        for billing_import, upload in rows:
            period_paid_credits = Decimal("0")
            full_seat_count += billing_import.full_seat_count
            view_seat_count += billing_import.view_seat_count
            user_count += billing_import.user_count
            for user_row in users_by_import.get(billing_import.id, []):
                total_seat_credits += user_row.seat_credits_used
                total_paid_credits += user_row.paid_credits_used
                period_paid_credits += user_row.paid_credits_used

            period_stubs.append(
                {
                    "billing_import": billing_import,
                    "upload": upload,
                    "period_paid_credits": period_paid_credits,
                }
            )

        configured_seat_cost = None
        if pricing.full_seat_cost_usd is not None or pricing.view_seat_cost_usd is not None:
            sub = figma_configured_subscription(
                pricing,
                full_seat_count=full_seat_count,
                view_seat_count=view_seat_count,
            )
            if sub > 0:
                configured_seat_cost = sub

        usd_per_credit = pricing.credits_per_usd
        import_paid_cost = figma_paid_credit_cost(total_paid_credits, usd_per_credit)
        display_seat_cost = configured_seat_cost or Decimal("0")
        display_total = display_seat_cost + import_paid_cost

        periods: list[FigmaBillingPeriodRow] = []
        for stub in period_stubs:
            billing_import = stub["billing_import"]
            upload = stub["upload"]
            period_paid_credits = stub["period_paid_credits"]
            period_paid_cost = figma_paid_credit_cost(period_paid_credits, usd_per_credit)
            periods.append(
                FigmaBillingPeriodRow(
                    usage_period_start=billing_import.usage_period_start,
                    usage_period_end=billing_import.usage_period_end,
                    seat_cost=display_seat_cost,
                    paid_cost=period_paid_cost,
                    total_cost=display_seat_cost + period_paid_cost,
                    paid_credits_used=period_paid_credits,
                    full_seat_count=billing_import.full_seat_count,
                    view_seat_count=billing_import.view_seat_count,
                    user_count=billing_import.user_count,
                    upload_filename=upload.filename if upload else None,
                    imported_at=billing_import.imported_at,
                )
            )

        monthly_budget = assignment.monthly_budget if assignment else None
        alert_threshold_usd = assignment.alert_threshold_usd if assignment else None
        budget_remaining = None
        if monthly_budget is not None and display_total > 0:
            budget_remaining = monthly_budget - display_total
        budget_alert_triggered = bool(
            alert_threshold_usd is not None
            and display_total > 0
            and display_total >= alert_threshold_usd
        )

        trend_from = active_start or from_date
        trend_to = active_end or to_date
        if periods:
            period_starts = [row.usage_period_start for row in periods if row.usage_period_start]
            period_ends = [row.usage_period_end for row in periods if row.usage_period_end]
            if period_starts and period_ends:
                trend_from = min(period_starts)
                trend_to = max(period_ends)

        cost_trend = self._billing_cost_trend(periods, from_date=trend_from, to_date=trend_to)
        top_users = self._top_users(
            users_by_import,
            total_cost=display_total,
            usd_per_credit=usd_per_credit,
        )

        insights = self._billing_insights(
            has_import=bool(periods),
            has_config=(
                configured[2] is not None
                or configured_seat_cost is not None
                or pricing.configured_seat_count is not None
            ),
            total_cost=display_total,
            seat_cost=display_seat_cost,
            paid_cost=import_paid_cost,
            configured_seat_cost=configured_seat_cost,
            configured_seat_count=pricing.configured_seat_count,
            full_seat_count=full_seat_count,
            view_seat_count=view_seat_count,
            credits_per_usd=configured[2],
            budget_remaining=budget_remaining,
            alert_threshold_usd=alert_threshold_usd,
            budget_alert_triggered=budget_alert_triggered,
            imports_outside_filter=imports_outside_filter,
        )

        return FigmaBillingInsightsResponse(
            team_id=str(team_id),
            tool_id=str(tool_id),
            from_date=from_date,
            to_date=to_date,
            has_import=bool(periods),
            has_config=(
                configured[2] is not None
                or configured_seat_cost is not None
                or pricing.configured_seat_count is not None
            ),
            imports_outside_filter=imports_outside_filter,
            full_seat_cost_usd=configured[0],
            view_seat_cost_usd=configured[1],
            credits_per_usd=configured[2],
            configured_seat_cost=configured_seat_cost,
            seat_cost=display_seat_cost if periods or configured_seat_cost else None,
            paid_cost=import_paid_cost if periods else None,
            total_cost=display_total if periods or configured_seat_cost else None,
            monthly_budget=monthly_budget,
            alert_threshold_usd=alert_threshold_usd,
            budget_remaining=budget_remaining,
            budget_alert_triggered=budget_alert_triggered,
            full_seat_count=full_seat_count if full_seat_count else None,
            view_seat_count=view_seat_count if view_seat_count else None,
            user_count=user_count if user_count else None,
            credits=FigmaBillingCreditTotals(
                total_seat_credits_used=total_seat_credits,
                total_paid_credits_used=total_paid_credits,
            ),
            available_periods=available_periods,
            active_billing_period_start=active_start,
            active_billing_period_end=active_end,
            periods=periods,
            cost_trend=cost_trend,
            top_users=top_users,
            insights=insights,
        )

    async def get_billing_period_users(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        period_start: date | None,
        period_end: date | None,
    ) -> FigmaBillingPeriodUsersResponse:
        assignment = await self._team_figma_assignment(team_id, tool_id=tool_id)
        pricing = figma_pricing_from_assignment(assignment)
        usd_per_credit = pricing.credits_per_usd
        rows = await self._billing_import_rows(
            team_id,
            tool_id,
            period_start or date.min,
            period_end or date.max,
            apply_date_filter=False,
        )
        import_ids = [
            billing_import.id
            for billing_import, _upload in rows
            if billing_import.usage_period_start == period_start
            and billing_import.usage_period_end == period_end
        ]
        users_by_import = await self._users_for_imports(import_ids)
        users: list[FigmaBillingPeriodUser] = []
        total_paid = Decimal("0")
        for import_id in import_ids:
            for row in users_by_import.get(import_id, []):
                paid_cost = figma_paid_credit_cost(row.paid_credits_used, usd_per_credit)
                total_paid += paid_cost
                users.append(
                    FigmaBillingPeriodUser(
                        user_email=row.user_email,
                        user_name=row.user_name,
                        figma_user_id=row.figma_user_id,
                        seat_type=row.seat_type,
                        seat_credits_used=row.seat_credits_used,
                        paid_credits_used=row.paid_credits_used,
                        seat_cost_usd=Decimal("0"),
                        paid_cost_usd=paid_cost,
                        total_cost_usd=paid_cost,
                    )
                )
        users.sort(key=lambda row: row.total_cost_usd, reverse=True)
        return FigmaBillingPeriodUsersResponse(
            usage_period_start=period_start,
            usage_period_end=period_end,
            total_cost=total_paid,
            total_paid_cost=total_paid,
            total_seat_cost=Decimal("0"),
            users=users,
        )

    async def get_billing_day_users(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        on_date: date,
    ) -> FigmaBillingPeriodUsersResponse:
        assignment = await self._team_figma_assignment(team_id, tool_id=tool_id)
        pricing = figma_pricing_from_assignment(assignment)
        usd_per_credit = pricing.credits_per_usd
        rows = await self._billing_import_rows(
            team_id,
            tool_id,
            on_date,
            on_date,
            apply_date_filter=True,
        )
        import_ids = [billing_import.id for billing_import, _upload in rows]
        users_by_import = await self._users_for_imports(import_ids)
        users: list[FigmaBillingPeriodUser] = []
        total_paid = Decimal("0")

        def append_user(row: FigmaBillingImportUser) -> None:
            nonlocal total_paid
            paid_cost = figma_paid_credit_cost(row.paid_credits_used, usd_per_credit)
            total_paid += paid_cost
            users.append(
                FigmaBillingPeriodUser(
                    user_email=row.user_email,
                    user_name=row.user_name,
                    figma_user_id=row.figma_user_id,
                    seat_type=row.seat_type,
                    seat_credits_used=row.seat_credits_used,
                    paid_credits_used=row.paid_credits_used,
                    seat_cost_usd=Decimal("0"),
                    paid_cost_usd=paid_cost,
                    total_cost_usd=paid_cost,
                )
            )

        for import_id in import_ids:
            for row in users_by_import.get(import_id, []):
                activity_date = row.last_activity_at.date() if row.last_activity_at else None
                if activity_date is not None and activity_date != on_date:
                    continue
                append_user(row)
        if not users:
            for import_id in import_ids:
                for row in users_by_import.get(import_id, []):
                    append_user(row)
        users.sort(key=lambda row: row.total_cost_usd, reverse=True)
        return FigmaBillingPeriodUsersResponse(
            usage_period_start=on_date,
            usage_period_end=on_date,
            total_cost=total_paid,
            total_paid_cost=total_paid,
            total_seat_cost=Decimal("0"),
            users=users,
        )

    async def _team_figma_assignment(
        self,
        team_id: uuid.UUID,
        *,
        tool_id: uuid.UUID | None = None,
    ) -> TeamTool | None:
        if tool_id is not None:
            tool = await self._session.get(Tool, tool_id)
            if tool is not None:
                catalogue_id = catalogue_tool_id_from_connected(tool) or tool_id
                assignment = await self._team_tools.get_by_team_and_tool(team_id, catalogue_id)
                if assignment is not None:
                    return assignment
                if catalogue_id != tool_id:
                    return await self._team_tools.get_by_team_and_tool(team_id, tool_id)
        return None

    async def _billing_import_rows(
        self,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        from_date: date,
        to_date: date,
        *,
        apply_date_filter: bool,
    ) -> list[tuple[FigmaBillingImport, Upload | None]]:
        tool = await self._session.get(Tool, tool_id)
        catalogue_id = catalogue_tool_id_from_connected(tool) or tool_id if tool else tool_id

        stmt = (
            select(FigmaBillingImport, Upload)
            .outerjoin(Upload, FigmaBillingImport.upload_id == Upload.id)
            .where(
                FigmaBillingImport.team_id == team_id,
                FigmaBillingImport.tool_id.in_({catalogue_id, tool_id}),
                active_upload_filter(),
            )
            .order_by(FigmaBillingImport.usage_period_start.desc().nullslast())
        )
        if apply_date_filter:
            stmt = stmt.where(figma_import_overlaps_period(from_date, to_date))

        result = await self._session.execute(stmt)
        return list(result.all())

    async def _users_for_imports(
        self,
        import_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, list[FigmaBillingImportUser]]:
        if not import_ids:
            return {}
        result = await self._session.execute(
            select(FigmaBillingImportUser).where(
                FigmaBillingImportUser.import_id.in_(import_ids)
            )
        )
        grouped: dict[uuid.UUID, list[FigmaBillingImportUser]] = {}
        for row in result.scalars().all():
            grouped.setdefault(row.import_id, []).append(row)
        return grouped

    def _configured_pricing(
        self,
        pricing,
        assignment: TeamTool | None,
    ) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
        return (
            pricing.full_seat_cost_usd,
            pricing.view_seat_cost_usd,
            pricing.credits_per_usd,
        )

    def _billing_cost_trend(
        self,
        periods: list[FigmaBillingPeriodRow],
        *,
        from_date: date,
        to_date: date,
    ) -> list[FigmaBillingCostTrendPoint]:
        """Daily cumulative cost across the CSV usage period (ends at actual period total)."""
        daily_increment: dict[date, Decimal] = {}
        for period in periods:
            start = period.usage_period_start
            end = period.usage_period_end or period.usage_period_start
            if start is None:
                continue
            if end is None:
                end = start
            span = max((end - start).days + 1, 1)
            per_day = period.total_cost / Decimal(span)
            current = start
            while current <= end:
                if from_date <= current <= to_date:
                    daily_increment[current] = daily_increment.get(current, Decimal("0")) + per_day
                current += timedelta(days=1)

        points: list[FigmaBillingCostTrendPoint] = []
        cumulative = Decimal("0")
        current = from_date
        while current <= to_date:
            day_cost = daily_increment.get(current, Decimal("0"))
            cumulative += day_cost
            points.append(
                FigmaBillingCostTrendPoint(
                    label=current.strftime("%b %d, %Y"),
                    iso_date=current.isoformat(),
                    cost=cumulative,
                    daily_cost=day_cost,
                    usage_period_start=current,
                    usage_period_end=current,
                )
            )
            current += timedelta(days=1)
        return points

    def _top_users(
        self,
        users_by_import: dict[uuid.UUID, list[FigmaBillingImportUser]],
        *,
        total_cost: Decimal,
        usd_per_credit: Decimal | None,
    ) -> list[FigmaBillingTopUser]:
        aggregated: dict[str, FigmaBillingTopUser] = {}
        for rows in users_by_import.values():
            for row in rows:
                key = (row.user_email or row.figma_user_id or str(row.id)).lower()
                paid_cost = figma_paid_credit_cost(row.paid_credits_used, usd_per_credit)
                existing = aggregated.get(key)
                if existing is None:
                    aggregated[key] = FigmaBillingTopUser(
                        user_email=row.user_email,
                        user_name=row.user_name,
                        figma_user_id=row.figma_user_id,
                        seat_type=row.seat_type,
                        seat_credits_used=row.seat_credits_used,
                        paid_credits_used=row.paid_credits_used,
                        seat_cost_usd=Decimal("0"),
                        paid_cost_usd=paid_cost,
                        total_cost_usd=paid_cost,
                    )
                else:
                    existing.seat_credits_used += row.seat_credits_used
                    existing.paid_credits_used += row.paid_credits_used
                    existing.paid_cost_usd += paid_cost
                    existing.total_cost_usd += paid_cost

        top = sorted(aggregated.values(), key=lambda row: row.total_cost_usd, reverse=True)
        total = float(total_cost) if total_cost > 0 else 0.0
        for row in top:
            row.percent_of_total = (
                float(row.total_cost_usd) / total * 100 if total > 0 else 0.0
            )
        return top

    def _billing_insights(
        self,
        *,
        has_import: bool,
        has_config: bool,
        total_cost: Decimal,
        seat_cost: Decimal,
        paid_cost: Decimal,
        configured_seat_cost: Decimal | None,
        configured_seat_count: int | None,
        full_seat_count: int,
        view_seat_count: int,
        credits_per_usd: Decimal | None,
        budget_remaining: Decimal | None,
        alert_threshold_usd: Decimal | None,
        budget_alert_triggered: bool,
        imports_outside_filter: bool,
    ) -> list[FigmaInsight]:
        insights: list[FigmaInsight] = []
        if not has_config:
            insights.append(
                FigmaInsight(
                    severity="warning",
                    title="Figma pricing not configured",
                    message="Set paid seat cost, seat count, and USD per paid credit on the team before importing.",
                )
            )
        if not has_import:
            insights.append(
                FigmaInsight(
                    severity="info",
                    title="No billing imports",
                    message="Upload a Figma billing CSV under Uploads to populate cost insights.",
                )
            )
            return insights
        if imports_outside_filter:
            insights.append(
                FigmaInsight(
                    severity="warning",
                    title="Imports outside date filter",
                    message="Showing imported billing data outside the selected date range.",
                )
            )
        insights.append(
            FigmaInsight(
                severity="info",
                title="Imported billing total",
                message=(
                    f"Subscription: ${seat_cost:.2f} + additional cost: ${paid_cost:.2f} "
                    f"= ${total_cost:.2f} total."
                ),
            )
        )
        if configured_seat_cost is not None and configured_seat_cost > 0:
            if (
                configured_seat_count
                and full_seat_count + view_seat_count > 0
                and full_seat_count + view_seat_count != configured_seat_count
            ):
                insights.append(
                    FigmaInsight(
                        severity="info",
                        title="Seat count vs configured",
                        message=(
                            f"CSV lists {full_seat_count + view_seat_count} users vs "
                            f"{configured_seat_count} configured paid seats."
                        ),
                    )
                )
        if credits_per_usd is not None:
            insights.append(
                FigmaInsight(
                    severity="info",
                    title="Paid credits conversion",
                    message=(
                        f"Paid credits used × ${credits_per_usd} per credit "
                        f"= ${paid_cost:.2f} additional cost. Seat credits in CSV are "
                        f"included in the subscription package."
                    ),
                )
            )
        if budget_alert_triggered:
            insights.append(
                FigmaInsight(
                    severity="warning",
                    title="Budget alert",
                    message=f"Total cost reached alert threshold (${alert_threshold_usd:.2f}).",
                )
            )
        elif budget_remaining is not None:
            insights.append(
                FigmaInsight(
                    severity="info",
                    title="Budget remaining",
                    message=f"${budget_remaining:.2f} remaining against monthly budget.",
                )
            )
        return insights
