"""Copilot productivity analytics queries and insights."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.productivity_parser import top_editors_from_rows, top_languages_from_rows
from app.copilot.schemas import (
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
from app.models.copilot import CopilotOrganization, CopilotSeat, CopilotUserUsage


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
