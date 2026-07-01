"""Copilot productivity analytics queries and insights."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.billing_totals import (
    load_parsed_rows_for_uploads,
    prorated_row_amounts_for_day,
    totals_from_upload_ids,
)
from app.copilot.user_matching import build_team_copilot_user_lookup, match_copilot_user_login
from app.copilot.billing_import import (
    compute_copilot_billed_total,
    compute_copilot_cost_split,
    extract_row_amounts,
)
from app.copilot.schemas import (
    CopilotBillingCostTrendPoint,
    CopilotBillingInsightsResponse,
    CopilotBillingPeriodRow,
    CopilotBillingPeriodUser,
    CopilotBillingPeriodUsersResponse,
    CopilotBillingQuantityTotals,
    CopilotBillingSkuBreakdown,
    CopilotBillingTopUser,
    CopilotChartPoint,
    CopilotCostReportRow,
    CopilotInsight,
    CopilotInsightsResponse,
    CopilotOverviewResponse,
    CopilotProductivityReportRow,
    CopilotSeatReportRow,
    CopilotUserDetailResponse,
    CopilotUserListResponse,
    CopilotUserSummary,
)
from app.models.copilot import CopilotBillingImport, CopilotOrganization, CopilotSeat, CopilotUserUsage
from app.models.admin import TeamTool, Tool
from app.models.ingestion import ParsedRow, Upload
from app.teams.copilot_billing_metrics import active_upload_filter, copilot_import_overlaps_period
from app.tools.catalogue import catalogue_tool_id_from_connected


class _BillingPeriodTotals:
    __slots__ = ("monthly_cost_limit", "additional_cost", "total_cost")

    def __init__(
        self,
        *,
        monthly_cost_limit: Decimal,
        additional_cost: Decimal,
        total_cost: Decimal,
    ) -> None:
        self.monthly_cost_limit = monthly_cost_limit
        self.additional_cost = additional_cost
        self.total_cost = total_cost


class CopilotAnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_overview(
        self,
        *,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> CopilotOverviewResponse:
        org = await self._latest_org(team_id)
        seats = await self._seats_for_team(team_id)
        usage_rows = await self._usage_in_range(team_id, from_date, to_date)

        assigned = len(seats)
        total_seats = org.total_seats if org and org.total_seats else assigned
        active_logins = {row.user_login for row in usage_rows}
        active_users = len(active_logins)
        inactive_users = max(assigned - active_users, 0)
        monthly_cost = org.monthly_cost if org else sum((s.monthly_cost for s in seats), Decimal("0"))
        utilization = (assigned / total_seats * 100) if total_seats else 0.0

        billing_totals = await self._latest_billing_totals(team_id, from_date, to_date)
        monthly_cost_limit: Decimal | None = None
        additional_cost: Decimal | None = None
        budget_remaining: Decimal | None = None
        alert_threshold_usd: Decimal | None = None
        budget_alert_triggered = False
        data_source = "config"

        assignment = await self._team_copilot_assignment(team_id)
        if assignment is not None:
            alert_threshold_usd = assignment.alert_threshold_usd
            if assignment.monthly_budget is not None:
                budget_remaining = assignment.monthly_budget - monthly_cost

        if billing_totals is not None:
            data_source = "import"
            monthly_cost = billing_totals.total_cost
            monthly_cost_limit = billing_totals.monthly_cost_limit
            additional_cost = billing_totals.additional_cost
            if assignment and assignment.monthly_budget is not None:
                budget_remaining = assignment.monthly_budget - billing_totals.total_cost
            if (
                alert_threshold_usd is not None
                and billing_totals.total_cost >= alert_threshold_usd
            ):
                budget_alert_triggered = True

        suggestions = sum(row.suggestions_count for row in usage_rows)
        acceptances = sum(row.acceptances_count for row in usage_rows)
        avg_acceptance = (acceptances / suggestions * 100) if suggestions else None

        raw_payloads = [row.raw_payload for row in usage_rows if isinstance(row.raw_payload, dict)]
        trend = await self._active_users_trend(team_id, from_date, to_date)

        return CopilotOverviewResponse(
            team_id=str(team_id),
            from_date=from_date,
            to_date=to_date,
            total_seats=total_seats,
            assigned_seats=assigned,
            active_users=active_users,
            inactive_users=inactive_users,
            monthly_cost=monthly_cost,
            seat_utilization_pct=round(utilization, 1),
            average_acceptance_rate=round(avg_acceptance, 1) if avg_acceptance is not None else None,
            monthly_cost_limit=monthly_cost_limit,
            additional_cost=additional_cost,
            budget_remaining=budget_remaining,
            alert_threshold_usd=alert_threshold_usd,
            budget_alert_triggered=budget_alert_triggered,
            data_source=data_source,
            seat_utilization=[
                CopilotChartPoint(label="Assigned", value=float(assigned)),
                CopilotChartPoint(label="Unused", value=float(max(total_seats - assigned, 0))),
                CopilotChartPoint(label="Available", value=float(max(total_seats - assigned, 0))),
            ],
            active_users_trend=trend,
            suggestions_vs_acceptances=[
                CopilotChartPoint(label="Suggestions", value=float(suggestions)),
                CopilotChartPoint(label="Accepted", value=float(acceptances)),
            ],
            top_languages=[
                CopilotChartPoint(label=name, value=float(count))
                for name, count in top_languages_from_rows(raw_payloads)
            ],
            ide_distribution=[
                CopilotChartPoint(label=name, value=float(count))
                for name, count in top_editors_from_rows(raw_payloads)
            ],
        )

    async def get_billing_insights(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> CopilotBillingInsightsResponse:
        assignment = await self._team_copilot_assignment(team_id, tool_id=tool_id)
        rows = await self._billing_import_rows(
            team_id,
            tool_id,
            from_date,
            to_date,
            apply_date_filter=True,
        )
        imports_outside_filter = False
        if not rows:
            rows = await self._billing_import_rows(
                team_id,
                tool_id,
                from_date,
                to_date,
                apply_date_filter=False,
            )
            imports_outside_filter = bool(rows)
        configured = self._configured_copilot_pricing(assignment)
        configured_subscription = configured[2] or Decimal("0")

        upload_ids = [
            billing_import.upload_id
            for billing_import, _upload in rows
            if billing_import.upload_id is not None
        ]
        parsed_totals = await totals_from_upload_ids(self._session, upload_ids)

        subscription, additional_cost, total_cost = compute_copilot_cost_split(
            parsed_totals.net_total,
            configured_subscription if configured_subscription > 0 else None,
            credits_gross=parsed_totals.credits_gross,
        )
        credits_cost = parsed_totals.credits_gross
        if total_cost == 0 and rows:
            total_cost = sum(
                (billing_import.total_cost for billing_import, _upload in rows),
                Decimal("0"),
            )
        seat_count = 0
        periods: list[CopilotBillingPeriodRow] = []

        for billing_import, upload in rows:
            raw_summary = billing_import.raw_summary if isinstance(billing_import.raw_summary, dict) else {}
            row_credits = Decimal(str(raw_summary.get("credits_cost") or 0))
            row_additional = billing_import.additional_cost
            if row_additional <= 0 and row_credits > 0:
                row_additional = row_credits
            if billing_import.seat_count:
                seat_count = max(seat_count, billing_import.seat_count)
            period_subscription = (
                configured_subscription
                if billing_import.sku == "copilot_for_business"
                else Decimal("0")
            )
            period_total = compute_copilot_billed_total(
                monthly_cost_limit=period_subscription,
                additional_cost=row_additional,
                credits_cost=Decimal("0") if row_additional > 0 else row_credits,
            )
            periods.append(
                CopilotBillingPeriodRow(
                    billing_period_start=billing_import.billing_period_start,
                    billing_period_end=billing_import.billing_period_end,
                    sku=billing_import.sku,
                    monthly_cost_limit=period_subscription,
                    additional_cost=row_additional,
                    credits_cost=row_credits,
                    total_cost=period_total,
                    seat_count=billing_import.seat_count,
                    upload_filename=upload.filename if upload else None,
                    imported_at=billing_import.imported_at,
                )
            )

        monthly_cost_limit = subscription if subscription > 0 else None

        monthly_budget = assignment.monthly_budget if assignment else None
        alert_threshold_usd = assignment.alert_threshold_usd if assignment else None
        budget_remaining = None
        if monthly_budget is not None and total_cost > 0:
            budget_remaining = monthly_budget - total_cost
        budget_alert_triggered = bool(
            alert_threshold_usd is not None and total_cost > 0 and total_cost >= alert_threshold_usd
        )

        insights = self._billing_insights(
            total_cost=total_cost,
            monthly_cost_limit=subscription,
            additional_cost=additional_cost,
            credits_cost=credits_cost,
            seat_count=seat_count,
            budget_remaining=budget_remaining,
            alert_threshold_usd=alert_threshold_usd,
            budget_alert_triggered=budget_alert_triggered,
            periods=periods,
            configured_monthly_cost=configured[2],
            pricing_model=configured[3],
            imports_outside_filter=imports_outside_filter,
        )

        trend_from = from_date
        trend_to = to_date
        if parsed_totals.gross_by_day:
            data_start = min(parsed_totals.gross_by_day)
            data_end = max(parsed_totals.gross_by_day)
            trend_from = max(from_date, data_start)
            trend_to = min(to_date, data_end)
        elif periods:
            period_starts = [
                row.billing_period_start for row in periods if row.billing_period_start
            ]
            period_ends = [row.billing_period_end for row in periods if row.billing_period_end]
            if period_starts and period_ends:
                trend_from = max(from_date, min(period_starts))
                trend_to = min(to_date, max(period_ends))

        cost_trend = self._billing_daily_cost_trend(
            parsed_totals.gross_by_day,
            from_date=trend_from,
            to_date=trend_to,
        )
        organization_id = rows[0][0].organization_id if rows else None
        user_lookup = (
            await build_team_copilot_user_lookup(
                self._session,
                organization_id=organization_id,
                team_id=team_id,
            )
            if organization_id is not None
            else {}
        )
        top_users = await self._billing_top_users(rows, user_lookup=user_lookup)
        sku_breakdown = self._billing_sku_breakdown(periods)

        return CopilotBillingInsightsResponse(
            team_id=str(team_id),
            tool_id=str(tool_id),
            from_date=from_date,
            to_date=to_date,
            has_import=bool(periods),
            has_config=configured[2] is not None,
            pricing_model=configured[3],
            cost_per_seat=configured[0],
            team_size=configured[1],
            configured_monthly_cost=configured[2],
            monthly_cost_limit=monthly_cost_limit,
            additional_cost=additional_cost if periods else None,
            credits_cost=credits_cost if periods else None,
            total_cost=total_cost if periods else None,
            monthly_budget=monthly_budget,
            alert_threshold_usd=alert_threshold_usd,
            budget_remaining=budget_remaining,
            budget_alert_triggered=budget_alert_triggered,
            seat_count=seat_count if seat_count else None,
            quantities=CopilotBillingQuantityTotals(
                total_quantity=parsed_totals.quantities.total_quantity,
                ai_credits_quantity=parsed_totals.quantities.ai_credits_quantity,
                user_months_quantity=parsed_totals.quantities.user_months_quantity,
            ),
            periods=periods,
            cost_trend=cost_trend,
            top_users=top_users,
            sku_breakdown=sku_breakdown,
            insights=insights,
            imports_outside_filter=imports_outside_filter,
        )

    async def get_billing_period_users(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        period_start: date | None,
        period_end: date | None,
    ) -> CopilotBillingPeriodUsersResponse:
        rows = await self._billing_import_rows(
            team_id,
            tool_id,
            period_start or date.min,
            period_end or date.max,
            apply_date_filter=False,
        )
        upload_ids = [
            billing_import.upload_id
            for billing_import, _upload in rows
            if billing_import.upload_id is not None
            and billing_import.billing_period_start == period_start
            and billing_import.billing_period_end == period_end
        ]
        users = await self._billing_users_from_parsed(
            upload_ids,
            period_start=period_start,
            period_end=period_end,
            allow_missing_row_period=True,
            user_lookup=await build_team_copilot_user_lookup(
                self._session,
                organization_id=rows[0][0].organization_id,
                team_id=team_id,
            )
            if rows
            else {},
            linked_only=False,
        )
        total_gross = sum((user.gross_cost for user in users), Decimal("0"))
        total_net = sum((user.net_cost for user in users), Decimal("0"))
        return CopilotBillingPeriodUsersResponse(
            billing_period_start=period_start,
            billing_period_end=period_end,
            total_gross=total_gross,
            total_net=total_net,
            users=users,
        )

    async def get_billing_day_users(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        on_date: date,
    ) -> CopilotBillingPeriodUsersResponse:
        rows = await self._billing_import_rows(
            team_id,
            tool_id,
            on_date,
            on_date,
            apply_date_filter=False,
        )
        upload_ids = [
            billing_import.upload_id
            for billing_import, _upload in rows
            if billing_import.upload_id is not None
            and self._billing_import_covers_date(billing_import, on_date)
        ]
        users = await self._billing_users_for_day(
            upload_ids,
            on_date=on_date,
            user_lookup=await build_team_copilot_user_lookup(
                self._session,
                organization_id=rows[0][0].organization_id,
                team_id=team_id,
            )
            if rows
            else {},
        )
        total_gross = sum((user.gross_cost for user in users), Decimal("0"))
        total_net = sum((user.net_cost for user in users), Decimal("0"))
        return CopilotBillingPeriodUsersResponse(
            billing_period_start=on_date,
            billing_period_end=on_date,
            total_gross=total_gross,
            total_net=total_net,
            users=users,
        )

    async def list_users(
        self,
        *,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> CopilotUserListResponse:
        usage_rows = await self._usage_in_range(team_id, from_date, to_date)
        seats_by_login = await self._seat_map(team_id)
        grouped: dict[str, CopilotUserSummary] = {}

        for row in usage_rows:
            existing = grouped.get(row.user_login)
            if existing is None:
                grouped[row.user_login] = CopilotUserSummary(
                    user_login=row.user_login,
                    user_email=row.user_email,
                    active_days=1,
                    chat_turns=row.chat_turns,
                    suggestions_count=row.suggestions_count,
                    acceptances_count=row.acceptances_count,
                    acceptance_rate=float(row.acceptance_rate) if row.acceptance_rate else None,
                    estimated_cost=row.estimated_cost,
                    last_activity_at=seats_by_login.get(row.user_login),
                )
            else:
                existing.active_days += 1
                existing.chat_turns += row.chat_turns
                existing.suggestions_count += row.suggestions_count
                existing.acceptances_count += row.acceptances_count
                if existing.suggestions_count:
                    existing.acceptance_rate = round(
                        existing.acceptances_count / existing.suggestions_count * 100, 1
                    )

        return CopilotUserListResponse(
            team_id=str(team_id),
            from_date=from_date,
            to_date=to_date,
            users=sorted(grouped.values(), key=lambda u: u.suggestions_count, reverse=True),
        )

    async def get_user_detail(
        self,
        *,
        team_id: uuid.UUID,
        user_login: str,
        from_date: date,
        to_date: date,
    ) -> CopilotUserDetailResponse | None:
        users = await self.list_users(team_id=team_id, from_date=from_date, to_date=to_date)
        summary = next((u for u in users.users if u.user_login.lower() == user_login.lower()), None)
        if summary is None:
            return None

        result = await self._session.execute(
            select(CopilotUserUsage)
            .where(
                CopilotUserUsage.team_id == team_id,
                CopilotUserUsage.user_login == summary.user_login,
                CopilotUserUsage.report_date >= from_date,
                CopilotUserUsage.report_date <= to_date,
            )
            .order_by(CopilotUserUsage.report_date.asc())
        )
        rows = list(result.scalars().all())
        raw_payloads = [row.raw_payload for row in rows if isinstance(row.raw_payload, dict)]

        daily = [
            CopilotChartPoint(
                label=row.report_date.isoformat(),
                value=float(row.suggestions_count + row.chat_turns),
            )
            for row in rows
        ]
        return CopilotUserDetailResponse(
            team_id=str(team_id),
            from_date=from_date,
            to_date=to_date,
            **summary.model_dump(),
            daily_usage=daily,
            language_distribution=[
                CopilotChartPoint(label=name, value=float(count))
                for name, count in top_languages_from_rows(raw_payloads)
            ],
            ide_usage=[
                CopilotChartPoint(label=name, value=float(count))
                for name, count in top_editors_from_rows(raw_payloads)
            ],
        )

    async def get_insights(
        self,
        *,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> CopilotInsightsResponse:
        overview = await self.get_overview(team_id=team_id, from_date=from_date, to_date=to_date)
        users = await self.list_users(team_id=team_id, from_date=from_date, to_date=to_date)
        insights: list[CopilotInsight] = []

        if overview.assigned_seats:
            adoption_pct = round(overview.active_users / overview.assigned_seats * 100)
            insights.append(
                CopilotInsight(
                    kind="adoption",
                    title="Adoption",
                    message=f"{adoption_pct}% of assigned users actively used Copilot in the selected period.",
                )
            )

        if overview.inactive_users:
            seat_price = (
                overview.monthly_cost / Decimal(overview.assigned_seats)
                if overview.assigned_seats
                else Decimal("19")
            )
            savings = seat_price * Decimal(overview.inactive_users)
            insights.append(
                CopilotInsight(
                    kind="license_waste",
                    title="License waste",
                    severity="warning",
                    message=(
                        f"{overview.inactive_users} licenses assigned but inactive in period. "
                        f"Potential monthly saving: ${savings:.0f}."
                    ),
                )
            )

        if users.users:
            total_activity = sum(u.suggestions_count + u.chat_turns for u in users.users)
            top = users.users[: min(10, len(users.users))]
            top_activity = sum(u.suggestions_count + u.chat_turns for u in top)
            if total_activity:
                share = round(top_activity / total_activity * 100)
                insights.append(
                    CopilotInsight(
                        kind="power_users",
                        title="Power users",
                        message=f"Top {len(top)} users generated {share}% of all Copilot activity.",
                    )
                )

        if overview.average_acceptance_rate is not None and overview.average_acceptance_rate < 20:
            insights.append(
                CopilotInsight(
                    kind="low_adoption",
                    title="Low acceptance rate",
                    severity="warning",
                    message=f"Organization acceptance rate is {overview.average_acceptance_rate:.0f}% (below 20%).",
                )
            )

        if overview.ide_distribution:
            top_ide = overview.ide_distribution[0]
            total = sum(point.value for point in overview.ide_distribution) or 1
            pct = round(top_ide.value / total * 100)
            insights.append(
                CopilotInsight(
                    kind="ide",
                    title="IDE usage",
                    message=f"{top_ide.label} represents {pct}% of total Copilot usage.",
                )
            )

        if overview.top_languages:
            top_lang = overview.top_languages[0]
            total = sum(point.value for point in overview.top_languages) or 1
            pct = round(top_lang.value / total * 100)
            insights.append(
                CopilotInsight(
                    kind="language",
                    title="Language usage",
                    message=f"{top_lang.label} accounts for {pct}% of generated suggestions.",
                )
            )

        return CopilotInsightsResponse(team_id=str(team_id), insights=insights)

    async def seat_report(self, *, team_id: uuid.UUID) -> list[CopilotSeatReportRow]:
        org = await self._latest_org(team_id)
        if org is None:
            return []
        result = await self._session.execute(
            select(CopilotSeat).where(CopilotSeat.organization_id == org.id).order_by(CopilotSeat.user_login)
        )
        return [
            CopilotSeatReportRow(
                user_login=seat.user_login,
                user_email=seat.user_email,
                assigned_at=seat.assigned_at.isoformat() if seat.assigned_at else None,
                last_activity_at=seat.last_activity_at.isoformat() if seat.last_activity_at else None,
                seat_status=seat.seat_status,
                monthly_cost=seat.monthly_cost,
            )
            for seat in result.scalars().all()
        ]

    async def productivity_report(
        self,
        *,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> list[CopilotProductivityReportRow]:
        users = await self.list_users(team_id=team_id, from_date=from_date, to_date=to_date)
        return [
            CopilotProductivityReportRow(
                user_login=user.user_login,
                language="all",
                editor="all",
                suggestions_count=user.suggestions_count,
                acceptances_count=user.acceptances_count,
                acceptance_rate=user.acceptance_rate,
                chat_turns=user.chat_turns,
            )
            for user in users.users
        ]

    async def cost_report(self, *, team_id: uuid.UUID) -> list[CopilotCostReportRow]:
        org = await self._latest_org(team_id)
        package = org.subscription_type if org else None
        seats = await self._seats_for_team(team_id)
        cutoff = datetime.now(UTC) - timedelta(days=30)
        rows: list[CopilotCostReportRow] = []
        for seat in seats:
            active = seat.last_activity_at and seat.last_activity_at >= cutoff
            rows.append(
                CopilotCostReportRow(
                    user_login=seat.user_login,
                    package=package,
                    estimated_monthly_cost=seat.monthly_cost,
                    activity_status="active" if active else "inactive",
                )
            )
        return rows

    async def _latest_org(self, team_id: uuid.UUID) -> CopilotOrganization | None:
        result = await self._session.execute(
            select(CopilotOrganization)
            .where(CopilotOrganization.team_id == team_id)
            .order_by(CopilotOrganization.report_date.desc().nullslast(), CopilotOrganization.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _latest_billing_totals(
        self,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> _BillingPeriodTotals | None:
        result = await self._session.execute(
            select(CopilotBillingImport)
            .where(CopilotBillingImport.team_id == team_id)
            .order_by(CopilotBillingImport.imported_at.desc())
        )
        rows = list(result.scalars().all())
        if not rows:
            return None

        in_range = [
            row
            for row in rows
            if row.billing_period_start is not None
            and row.billing_period_end is not None
            and row.billing_period_start >= from_date
            and row.billing_period_end <= to_date
        ]
        anchor = in_range[0] if in_range else rows[0]
        period_rows = [
            row
            for row in rows
            if row.billing_period_start == anchor.billing_period_start
            and row.billing_period_end == anchor.billing_period_end
        ]
        return _BillingPeriodTotals(
            monthly_cost_limit=sum((row.monthly_cost_limit for row in period_rows), Decimal("0")),
            additional_cost=sum((row.additional_cost for row in period_rows), Decimal("0")),
            total_cost=compute_copilot_billed_total(
                monthly_cost_limit=sum((row.monthly_cost_limit for row in period_rows), Decimal("0")),
                additional_cost=sum((row.additional_cost for row in period_rows), Decimal("0")),
                credits_cost=sum(
                    (
                        Decimal(str((row.raw_summary or {}).get("credits_cost") or 0))
                        for row in period_rows
                    ),
                    Decimal("0"),
                ),
            ),
        )

    async def _latest_billing_import(
        self,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> CopilotBillingImport | None:
        result = await self._session.execute(
            select(CopilotBillingImport)
            .where(
                CopilotBillingImport.team_id == team_id,
                CopilotBillingImport.billing_period_start >= from_date,
                CopilotBillingImport.billing_period_end <= to_date,
            )
            .order_by(CopilotBillingImport.imported_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        result = await self._session.execute(
            select(CopilotBillingImport)
            .where(CopilotBillingImport.team_id == team_id)
            .order_by(CopilotBillingImport.imported_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _resolve_catalogue_tool_id(self, tool_id: uuid.UUID) -> uuid.UUID:
        tool = await self._session.get(Tool, tool_id)
        if tool is None:
            return tool_id
        return catalogue_tool_id_from_connected(tool) or tool_id

    async def _copilot_tool_ids_for_query(self, tool_id: uuid.UUID) -> list[uuid.UUID]:
        catalogue_id = await self._resolve_catalogue_tool_id(tool_id)
        if catalogue_id == tool_id:
            return [tool_id]
        return [tool_id, catalogue_id]

    async def _team_copilot_assignment(
        self,
        team_id: uuid.UUID,
        tool_id: uuid.UUID | None = None,
    ) -> TeamTool | None:
        result = await self._session.execute(
            select(TeamTool, Tool)
            .join(Tool, TeamTool.tool_id == Tool.id)
            .where(TeamTool.team_id == team_id, Tool.vendor == "copilot")
        )
        rows = list(result.all())
        if tool_id is not None:
            catalogue_id = await self._resolve_catalogue_tool_id(tool_id)
            allowed = {tool_id, catalogue_id}
            for assignment, _tool in rows:
                if assignment.tool_id in allowed:
                    return assignment
            return None
        return rows[0][0] if rows else None

    async def _billing_import_rows(
        self,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        from_date: date,
        to_date: date,
        *,
        apply_date_filter: bool = True,
    ) -> list[tuple[CopilotBillingImport, Upload | None]]:
        tool_ids = await self._copilot_tool_ids_for_query(tool_id)
        stmt = (
            select(CopilotBillingImport, Upload)
            .outerjoin(Upload, CopilotBillingImport.upload_id == Upload.id)
            .where(
                CopilotBillingImport.team_id == team_id,
                CopilotBillingImport.tool_id.in_(tool_ids),
                active_upload_filter(),
            )
            .order_by(
                CopilotBillingImport.billing_period_start.desc().nullslast(),
                CopilotBillingImport.imported_at.desc(),
                CopilotBillingImport.sku.asc(),
            )
        )
        if apply_date_filter:
            stmt = stmt.where(copilot_import_overlaps_period(from_date, to_date))

        filtered: list[tuple[CopilotBillingImport, Upload | None]] = []
        for billing_import, upload in (await self._session.execute(stmt)).all():
            filtered.append((billing_import, upload))
        return filtered

    @staticmethod
    def _sku_label(sku: str) -> str:
        labels = {
            "copilot_for_business": "Copilot Business",
            "copilot_ai_credit": "AI Credits",
        }
        return labels.get(sku, sku.replace("_", " ").title())

    @staticmethod
    def _billing_import_covers_date(billing_import: CopilotBillingImport, on_date: date) -> bool:
        start = billing_import.billing_period_start
        end = billing_import.billing_period_end
        if start is not None and end is not None:
            return start <= on_date <= end
        if start is not None:
            return start <= on_date
        if end is not None:
            return on_date <= end
        return True

    @staticmethod
    def _daily_chart_label(day: date) -> str:
        return f"{day.strftime('%b')} {day.day}"

    @staticmethod
    def _billing_daily_cost_trend(
        gross_by_day: dict[date, Decimal],
        *,
        from_date: date,
        to_date: date,
    ) -> list[CopilotBillingCostTrendPoint]:
        trend: list[CopilotBillingCostTrendPoint] = []
        current = from_date
        while current <= to_date:
            cost = gross_by_day.get(current, Decimal("0"))
            trend.append(
                CopilotBillingCostTrendPoint(
                    label=CopilotAnalyticsService._daily_chart_label(current),
                    iso_date=current.isoformat(),
                    cost=cost,
                    billing_period_start=current,
                    billing_period_end=current,
                )
            )
            current += timedelta(days=1)
        return trend

    @staticmethod
    def _billing_cost_trend_from_periods(
        periods: list[CopilotBillingPeriodRow],
    ) -> list[CopilotBillingCostTrendPoint]:
        totals_by_period: dict[tuple[date | None, date | None], Decimal] = {}
        for row in periods:
            key = (row.billing_period_start, row.billing_period_end)
            totals_by_period[key] = totals_by_period.get(key, Decimal("0")) + row.total_cost
        return CopilotAnalyticsService._billing_cost_trend(totals_by_period)

    @staticmethod
    def _billing_cost_trend(
        gross_by_period: dict[tuple[date | None, date | None], Decimal],
    ) -> list[CopilotBillingCostTrendPoint]:
        trend: list[CopilotBillingCostTrendPoint] = []
        for (period_start, period_end), cost in sorted(
            gross_by_period.items(),
            key=lambda item: item[0][0] or date.min,
        ):
            anchor = period_end or period_start
            if anchor is None:
                label = "Import"
                iso = date.today().isoformat()
            else:
                label = anchor.strftime("%b %Y")
                if period_start and period_end and period_start != period_end:
                    label = f"{period_start.strftime('%b %d')} – {period_end.strftime('%b %d, %Y')}"
                iso = anchor.isoformat()
            trend.append(
                CopilotBillingCostTrendPoint(
                    label=label,
                    iso_date=iso,
                    cost=cost,
                    billing_period_start=period_start,
                    billing_period_end=period_end,
                ),
            )
        return trend

    @staticmethod
    def _parsed_amounts(
        mapped: dict,
        raw: dict | None = None,
    ) -> tuple[Decimal, Decimal, str, str]:
        net, gross = extract_row_amounts(mapped, raw)
        unit_type = str(mapped.get("unit_type") or "").strip().lower().replace("_", "-")
        login = str(mapped.get("user_login") or "").strip()
        return net, gross, unit_type, login

    @staticmethod
    def _parsed_period_matches(
        mapped: dict,
        *,
        period_start: date | None,
        period_end: date | None,
        allow_missing_row_period: bool = False,
    ) -> bool:
        if period_start is None and period_end is None:
            return True

        def _as_date(value: object) -> date | None:
            if value is None or value == "":
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                return None

        row_start = _as_date(mapped.get("billing_period_start"))
        row_end = _as_date(mapped.get("billing_period_end"))
        if row_start is None and row_end is None:
            return allow_missing_row_period
        return row_start == period_start and row_end == period_end

    async def _user_display_names(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
        if not user_ids:
            return {}
        from app.models.auth import User

        result = await self._session.execute(select(User).where(User.id.in_(user_ids)))
        names: dict[uuid.UUID, str] = {}
        for user in result.scalars():
            if user.display_name and user.display_name.strip():
                names[user.id] = user.display_name.strip()
            else:
                names[user.id] = user.email
        return names

    async def _billing_users_from_parsed(
        self,
        upload_ids: list[uuid.UUID],
        *,
        period_start: date | None = None,
        period_end: date | None = None,
        linked_only: bool = False,
        allow_missing_row_period: bool = False,
        user_lookup: dict[str, uuid.UUID] | None = None,
    ) -> list[CopilotBillingPeriodUser]:
        if not upload_ids:
            return []

        lookup = user_lookup or {}
        result = await self._session.execute(
            select(ParsedRow).where(ParsedRow.upload_id.in_(upload_ids))
        )
        parsed_rows = list(result.scalars())
        resolved_ids: set[uuid.UUID] = set()
        for parsed in parsed_rows:
            mapped = parsed.mapped_payload if isinstance(parsed.mapped_payload, dict) else {}
            login = str(mapped.get("user_login") or parsed.user_email or "").strip()
            resolved = parsed.matched_user_id or match_copilot_user_login(login, lookup)
            if resolved is not None:
                resolved_ids.add(resolved)
        display_names = await self._user_display_names(resolved_ids)

        by_user: dict[str, dict[str, object]] = {}
        for parsed in parsed_rows:
            mapped = parsed.mapped_payload if isinstance(parsed.mapped_payload, dict) else {}
            raw = parsed.raw_payload if isinstance(parsed.raw_payload, dict) else {}
            if not self._parsed_period_matches(
                mapped,
                period_start=period_start,
                period_end=period_end,
                allow_missing_row_period=allow_missing_row_period,
            ):
                continue
            login = str(mapped.get("user_login") or parsed.user_email or "").strip()
            resolved_user_id = parsed.matched_user_id or match_copilot_user_login(login, lookup)
            if linked_only and resolved_user_id is None:
                continue
            if not login and resolved_user_id is None:
                continue
            bucket_key = str(resolved_user_id) if resolved_user_id is not None else login.lower()
            net, gross, _unit_type, _ = self._parsed_amounts(mapped, raw)
            qty = int(mapped.get("quantity") or 0)
            bucket = by_user.setdefault(
                bucket_key,
                {
                    "user_id": str(resolved_user_id) if resolved_user_id is not None else "",
                    "user_login": login or "Unknown user",
                    "display_name": display_names.get(resolved_user_id) if resolved_user_id else login,
                    "gross_cost": Decimal("0"),
                    "net_cost": Decimal("0"),
                    "quantity": 0,
                },
            )
            bucket["gross_cost"] = Decimal(str(bucket["gross_cost"])) + gross
            bucket["net_cost"] = Decimal(str(bucket["net_cost"])) + net
            bucket["quantity"] = int(bucket["quantity"]) + qty
            if login:
                bucket["user_login"] = login
            if resolved_user_id is not None:
                bucket["user_id"] = str(resolved_user_id)
                bucket["display_name"] = display_names.get(resolved_user_id) or login

        users = [
            CopilotBillingPeriodUser(
                user_id=str(data["user_id"]),
                user_login=str(data["user_login"]),
                display_name=str(data["display_name"]) if data.get("display_name") else None,
                gross_cost=Decimal(str(data["gross_cost"])),
                net_cost=Decimal(str(data["net_cost"])),
                quantity=int(data["quantity"]),
            )
            for data in by_user.values()
            if Decimal(str(data["gross_cost"])) > 0 or Decimal(str(data["net_cost"])) > 0
        ]
        return sorted(users, key=lambda row: row.gross_cost, reverse=True)

    async def _billing_users_for_day(
        self,
        upload_ids: list[uuid.UUID],
        *,
        on_date: date,
        user_lookup: dict[str, uuid.UUID] | None = None,
    ) -> list[CopilotBillingPeriodUser]:
        if not upload_ids:
            return []

        lookup = user_lookup or {}
        parsed_rows = await load_parsed_rows_for_uploads(self._session, upload_ids)
        resolved_ids: set[uuid.UUID] = set()
        for mapped, _raw, _fallback_start, _fallback_end in parsed_rows:
            login = str(mapped.get("user_login") or "").strip()
            resolved = match_copilot_user_login(login, lookup)
            if resolved is not None:
                resolved_ids.add(resolved)
        display_names = await self._user_display_names(resolved_ids)

        by_user: dict[str, dict[str, object]] = {}
        for mapped, raw, fallback_start, fallback_end in parsed_rows:
            net, gross, qty = prorated_row_amounts_for_day(
                mapped,
                raw,
                on_date,
                fallback_start=fallback_start,
                fallback_end=fallback_end,
            )
            if gross <= 0 and net <= 0:
                continue

            login = str(mapped.get("user_login") or "").strip()
            resolved_user_id = match_copilot_user_login(login, lookup)
            if not login and resolved_user_id is None:
                continue

            bucket_key = str(resolved_user_id) if resolved_user_id is not None else login.lower()
            bucket = by_user.setdefault(
                bucket_key,
                {
                    "user_id": str(resolved_user_id) if resolved_user_id is not None else "",
                    "user_login": login or "Unknown user",
                    "display_name": display_names.get(resolved_user_id) if resolved_user_id else login,
                    "gross_cost": Decimal("0"),
                    "net_cost": Decimal("0"),
                    "quantity": 0,
                },
            )
            bucket["gross_cost"] = Decimal(str(bucket["gross_cost"])) + gross
            bucket["net_cost"] = Decimal(str(bucket["net_cost"])) + net
            bucket["quantity"] = int(bucket["quantity"]) + qty
            if login:
                bucket["user_login"] = login
            if resolved_user_id is not None:
                bucket["user_id"] = str(resolved_user_id)
                bucket["display_name"] = display_names.get(resolved_user_id) or login

        users = [
            CopilotBillingPeriodUser(
                user_id=str(data["user_id"]),
                user_login=str(data["user_login"]),
                display_name=str(data["display_name"]) if data.get("display_name") else None,
                gross_cost=Decimal(str(data["gross_cost"])),
                net_cost=Decimal(str(data["net_cost"])),
                quantity=int(data["quantity"]),
            )
            for data in by_user.values()
            if Decimal(str(data["gross_cost"])) > 0 or Decimal(str(data["net_cost"])) > 0
        ]
        return sorted(users, key=lambda row: row.gross_cost, reverse=True)

    @staticmethod
    def _billing_sku_breakdown(
        periods: list[CopilotBillingPeriodRow],
    ) -> list[CopilotBillingSkuBreakdown]:
        totals: dict[str, Decimal] = {}
        for row in periods:
            totals[row.sku] = totals.get(row.sku, Decimal("0")) + row.total_cost
        return [
            CopilotBillingSkuBreakdown(
                sku=sku,
                label=CopilotAnalyticsService._sku_label(sku),
                cost=cost,
            )
            for sku, cost in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]

    async def _billing_top_users(
        self,
        billing_rows: list[tuple[CopilotBillingImport, Upload | None]],
        *,
        user_lookup: dict[str, uuid.UUID] | None = None,
    ) -> list[CopilotBillingTopUser]:
        upload_ids = [
            billing_import.upload_id
            for billing_import, _upload in billing_rows
            if billing_import.upload_id is not None
        ]
        period_users = await self._billing_users_from_parsed(
            upload_ids,
            linked_only=False,
            user_lookup=user_lookup,
        )
        return [
            CopilotBillingTopUser(
                user_login=user.user_login,
                user_id=user.user_id,
                display_name=user.display_name,
                cost=user.gross_cost,
                net_cost=user.net_cost,
                quantity=user.quantity,
            )
            for user in period_users[:10]
        ]

    @staticmethod
    def _configured_copilot_pricing(
        assignment: TeamTool | None,
    ) -> tuple[Decimal | None, int | None, Decimal | None, str | None]:
        if assignment is None:
            return None, None, None, None
        config = assignment.pricing_config if isinstance(assignment.pricing_config, dict) else {}
        model = str(config.get("model") or "per_seat")
        team_size = assignment.seat_count
        if team_size is None and config.get("seat_count") is not None:
            team_size = int(config["seat_count"])
        if not team_size:
            return None, team_size, None, model

        if model == "per_team":
            cost_per_team = config.get("cost_per_team") or config.get("flat_monthly_cost")
            if cost_per_team is None and assignment.cost_per_seat is not None:
                cost_per_team = assignment.cost_per_seat
            if cost_per_team is None:
                return None, team_size, None, model
            unit = Decimal(str(cost_per_team))
            return unit, team_size, unit * Decimal(team_size), model

        cost_per_seat = assignment.cost_per_seat
        if cost_per_seat is None and config.get("cost_per_seat") is not None:
            cost_per_seat = Decimal(str(config["cost_per_seat"]))
        if cost_per_seat is None:
            return None, team_size, None, model
        return cost_per_seat, team_size, cost_per_seat * Decimal(team_size), model

    @staticmethod
    def _billing_insights(
        *,
        total_cost: Decimal,
        monthly_cost_limit: Decimal,
        additional_cost: Decimal,
        credits_cost: Decimal,
        seat_count: int,
        budget_remaining: Decimal | None,
        alert_threshold_usd: Decimal | None,
        budget_alert_triggered: bool,
        periods: list[CopilotBillingPeriodRow],
        configured_monthly_cost: Decimal | None = None,
        pricing_model: str | None = None,
        imports_outside_filter: bool = False,
    ) -> list[CopilotInsight]:
        if not periods and configured_monthly_cost is None:
            return [
                CopilotInsight(
                    kind="no_data",
                    title="No Copilot pricing configured",
                    message=(
                        "Configure Copilot package, pricing model, unit cost, and team size on the team, "
                        "then import billing CSV for actual totals."
                    ),
                    severity="info",
                )
            ]

        insights: list[CopilotInsight] = []
        if imports_outside_filter:
            insights.append(
                CopilotInsight(
                    kind="period_mismatch",
                    title="Imported data outside selected period",
                    message=(
                        "Billing imports exist for this team but fall outside the selected date range. "
                        "Showing the latest imported periods — widen the period filter to match."
                    ),
                    severity="info",
                )
            )
        if configured_monthly_cost is not None:
            formula = (
                "cost per team × team members"
                if pricing_model == "per_team"
                else "cost per seat × team size"
            )
            insights.append(
                CopilotInsight(
                    kind="configured_cost",
                    title="Configured subscription total",
                    message=(
                        f"Expected monthly cost from team setup is "
                        f"${configured_monthly_cost:.2f} USD ({formula})."
                    ),
                    severity="info",
                )
            )
        if not periods:
            insights.append(
                CopilotInsight(
                    kind="no_import",
                    title="No billing CSV imported",
                    message="Upload a Copilot billing CSV to see actual invoice totals in this period.",
                    severity="info",
                )
            )
            return insights

        insights.append(
            CopilotInsight(
                kind="billing_total",
                title="Imported billing total",
                message=(
                    f"Total billed cost is ${total_cost:.2f} USD "
                    f"(subscription limit + additional spend)."
                ),
                severity="info",
            )
        )
        if (
            configured_monthly_cost is not None
            and total_cost > 0
            and configured_monthly_cost != total_cost
        ):
            delta = total_cost - configured_monthly_cost
            insights.append(
                CopilotInsight(
                    kind="variance",
                    title="Configured vs imported",
                    message=(
                        f"Imported total differs from configured subscription by "
                        f"${abs(delta):.2f} USD ({'over' if delta > 0 else 'under'})."
                    ),
                    severity="warning" if delta > 0 else "info",
                )
            )
        if monthly_cost_limit > 0:
            insights.append(
                CopilotInsight(
                    kind="monthly_limit",
                    title="Configured subscription limit",
                    message=(
                        f"Team subscription total from setup is "
                        f"${monthly_cost_limit:.2f} USD per billing period."
                    ),
                    severity="info",
                )
            )
        if additional_cost > 0:
            insights.append(
                CopilotInsight(
                    kind="additional_cost",
                    title="Additional spend",
                    message=(
                        f"Imported net spend beyond the subscription limit is "
                        f"${additional_cost:.2f} USD."
                    ),
                    severity="info",
                )
            )
        if credits_cost > 0:
            insights.append(
                CopilotInsight(
                    kind="credits_cost",
                    title="AI credits usage",
                    message=f"Imported gross amount for AI credits is ${credits_cost:.2f} USD.",
                    severity="info",
                )
            )
        if seat_count > 0:
            insights.append(
                CopilotInsight(
                    kind="seat_count",
                    title="Seats billed",
                    message=f"Latest import includes {seat_count} billed seat-months.",
                    severity="info",
                )
            )
        if budget_alert_triggered and alert_threshold_usd is not None:
            insights.append(
                CopilotInsight(
                    kind="budget_alert",
                    title="Cost alert triggered",
                    message=(
                        f"Imported spend (${total_cost:.2f}) reached your "
                        f"${alert_threshold_usd:.2f} USD alert threshold."
                    ),
                    severity="warning",
                )
            )
        elif budget_remaining is not None:
            insights.append(
                CopilotInsight(
                    kind="budget_remaining",
                    title="Budget remaining",
                    message=f"${budget_remaining:.2f} USD remains against the team monthly budget.",
                    severity="success" if budget_remaining >= 0 else "warning",
                )
            )
        return insights

    async def _seats_for_team(self, team_id: uuid.UUID) -> list[CopilotSeat]:
        org = await self._latest_org(team_id)
        if org is None:
            return []
        result = await self._session.execute(
            select(CopilotSeat).where(CopilotSeat.organization_id == org.id)
        )
        return list(result.scalars().all())

    async def _usage_in_range(
        self,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> list[CopilotUserUsage]:
        result = await self._session.execute(
            select(CopilotUserUsage).where(
                CopilotUserUsage.team_id == team_id,
                CopilotUserUsage.report_date >= from_date,
                CopilotUserUsage.report_date <= to_date,
            )
        )
        return list(result.scalars().all())

    async def _seat_map(self, team_id: uuid.UUID) -> dict[str, str | None]:
        seats = await self._seats_for_team(team_id)
        return {
            seat.user_login: seat.last_activity_at.isoformat() if seat.last_activity_at else None
            for seat in seats
        }

    async def _active_users_trend(
        self,
        team_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> list[CopilotChartPoint]:
        result = await self._session.execute(
            select(CopilotUserUsage.report_date, func.count(func.distinct(CopilotUserUsage.user_login)))
            .where(
                CopilotUserUsage.team_id == team_id,
                CopilotUserUsage.report_date >= from_date,
                CopilotUserUsage.report_date <= to_date,
            )
            .group_by(CopilotUserUsage.report_date)
            .order_by(CopilotUserUsage.report_date.asc())
        )
        return [
            CopilotChartPoint(label=row[0].isoformat(), value=float(row[1]))
            for row in result.all()
        ]
