"""Persist GitHub Copilot sync data to copilot schema tables."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.copilot.productivity_parser import (
    CopilotOrgSnapshot,
    CopilotSeatRow,
    CopilotUserUsageRow,
    parse_org_metrics_row,
    parse_seat_row,
    parse_user_metrics_row,
)
from app.models.copilot import CopilotOrganization, CopilotSeat, CopilotUserUsage
from app.models.admin import Tool

logger = logging.getLogger(__name__)

DEFAULT_SEAT_PRICES: dict[str, Decimal] = {
    "business": Decimal("19"),
    "enterprise": Decimal("39"),
    "individual": Decimal("10"),
}


@dataclass
class CopilotSyncResult:
    user_rows: int
    seat_rows: int
    org_rows: int


class CopilotIngestService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sync_from_pull(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID | None,
        github_org_id: str,
        seat_price: Decimal,
        subscription_type: str | None,
        user_metric_rows: list[dict],
        org_metric_rows: list[dict],
        seat_payloads: list[dict],
        sync_until: datetime,
    ) -> CopilotSyncResult:
        org_row = await self._upsert_organization(
            team_id=team_id,
            tool_id=tool_id,
            github_org_id=github_org_id,
            subscription_type=subscription_type,
            seat_price=seat_price,
            assigned_seats=len(seat_payloads),
            user_metric_rows=user_metric_rows,
            org_metric_rows=org_metric_rows,
            sync_until=sync_until,
        )

        seat_count = await self._upsert_seats(
            org_row_id=org_row.id,
            seat_payloads=seat_payloads,
            seat_price=seat_price,
        )
        user_count = await self._upsert_user_usage(
            team_id=team_id,
            org_row_id=org_row.id,
            user_metric_rows=user_metric_rows,
            seat_price=seat_price,
            assigned_logins={parse_seat_row(s).user_login for s in seat_payloads if parse_seat_row(s)},
        )
        return CopilotSyncResult(user_rows=user_count, seat_rows=seat_count, org_rows=1)

    async def _upsert_organization(
        self,
        *,
        team_id: uuid.UUID,
        tool_id: uuid.UUID | None,
        github_org_id: str,
        subscription_type: str | None,
        seat_price: Decimal,
        assigned_seats: int,
        user_metric_rows: list[dict],
        org_metric_rows: list[dict],
        sync_until: datetime,
    ) -> CopilotOrganization:
        report_date = sync_until.astimezone(UTC).date()
        snapshot: CopilotOrgSnapshot | None = None
        for row in org_metric_rows:
            if isinstance(row, dict):
                snapshot = parse_org_metrics_row(row, github_org_id=github_org_id)
                break

        active_users = len(
            {
                parse_user_metrics_row(r).user_login
                for r in user_metric_rows
                if isinstance(r, dict) and parse_user_metrics_row(r)
            }
        )
        total_seats = assigned_seats
        if snapshot is not None:
            if snapshot.total_seats:
                total_seats = snapshot.total_seats
            if snapshot.active_users:
                active_users = snapshot.active_users
            if snapshot.report_date:
                report_date = snapshot.report_date

        monthly_cost = seat_price * Decimal(assigned_seats)
        values = {
            "id": uuid.uuid4(),
            "team_id": team_id,
            "tool_id": tool_id,
            "organization_name": snapshot.organization_name if snapshot else github_org_id,
            "organization_id": github_org_id,
            "subscription_type": subscription_type,
            "monthly_cost": monthly_cost,
            "total_seats": total_seats,
            "assigned_seats": assigned_seats,
            "active_users": active_users,
            "report_date": report_date,
        }
        stmt = insert(CopilotOrganization).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["team_id", "organization_id", "report_date"],
            set_={
                "tool_id": stmt.excluded.tool_id,
                "organization_name": stmt.excluded.organization_name,
                "subscription_type": stmt.excluded.subscription_type,
                "monthly_cost": stmt.excluded.monthly_cost,
                "total_seats": stmt.excluded.total_seats,
                "assigned_seats": stmt.excluded.assigned_seats,
                "active_users": stmt.excluded.active_users,
                "updated_at": datetime.now(UTC),
            },
        ).returning(CopilotOrganization)
        result = await self._session.execute(stmt)
        row = result.scalar_one()
        return row

    async def _upsert_seats(
        self,
        *,
        org_row_id: uuid.UUID,
        seat_payloads: list[dict],
        seat_price: Decimal,
    ) -> int:
        count = 0
        for seat in seat_payloads:
            parsed = parse_seat_row(seat)
            if parsed is None:
                continue
            values = {
                "id": uuid.uuid4(),
                "organization_id": org_row_id,
                "user_login": parsed.user_login,
                "user_email": parsed.user_email,
                "seat_status": parsed.seat_status,
                "assigned_at": parsed.assigned_at,
                "last_activity_at": parsed.last_activity_at,
                "monthly_cost": seat_price,
            }
            stmt = insert(CopilotSeat).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["organization_id", "user_login"],
                set_={
                    "user_email": stmt.excluded.user_email,
                    "seat_status": stmt.excluded.seat_status,
                    "assigned_at": stmt.excluded.assigned_at,
                    "last_activity_at": stmt.excluded.last_activity_at,
                    "monthly_cost": stmt.excluded.monthly_cost,
                    "updated_at": datetime.now(UTC),
                },
            )
            await self._session.execute(stmt)
            count += 1
        return count

    async def _upsert_user_usage(
        self,
        *,
        team_id: uuid.UUID,
        org_row_id: uuid.UUID,
        user_metric_rows: list[dict],
        seat_price: Decimal,
        assigned_logins: set[str],
    ) -> int:
        count = 0
        for row in user_metric_rows:
            if not isinstance(row, dict):
                continue
            parsed = parse_user_metrics_row(row)
            if parsed is None:
                continue
            cost = seat_price if parsed.user_login in assigned_logins else Decimal("0")
            values = {
                "id": uuid.uuid4(),
                "team_id": team_id,
                "organization_id": org_row_id,
                "report_date": parsed.report_date,
                "user_login": parsed.user_login,
                "user_email": parsed.user_email,
                "user_name": parsed.user_name,
                "feature": parsed.feature,
                "editor": parsed.editor,
                "language": parsed.language,
                "active_days": parsed.active_days,
                "chat_turns": parsed.chat_turns,
                "suggestions_count": parsed.suggestions_count,
                "acceptances_count": parsed.acceptances_count,
                "acceptance_rate": parsed.acceptance_rate,
                "lines_suggested": parsed.lines_suggested,
                "lines_accepted": parsed.lines_accepted,
                "estimated_cost": cost,
                "raw_payload": parsed.raw_payload,
            }
            stmt = insert(CopilotUserUsage).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "team_id",
                    "organization_id",
                    "user_login",
                    "report_date",
                    "feature",
                    "editor",
                    "language",
                ],
                set_={
                    "chat_turns": stmt.excluded.chat_turns,
                    "suggestions_count": stmt.excluded.suggestions_count,
                    "acceptances_count": stmt.excluded.acceptances_count,
                    "acceptance_rate": stmt.excluded.acceptance_rate,
                    "lines_suggested": stmt.excluded.lines_suggested,
                    "lines_accepted": stmt.excluded.lines_accepted,
                    "estimated_cost": stmt.excluded.estimated_cost,
                    "raw_payload": stmt.excluded.raw_payload,
                },
            )
            await self._session.execute(stmt)
            count += 1
        return count


async def resolve_copilot_seat_price(
    session: AsyncSession,
    *,
    tool: Tool | None,
    team_tool_assignment,
) -> Decimal:
    from app.teams.pricing_resolution import resolve_team_tool_pricing

    if tool is None:
        return DEFAULT_SEAT_PRICES["business"]

    resolved = resolve_team_tool_pricing(team_tool_assignment, tool)
    package_name = (resolved.pricing_config.get("plan_name") or "").lower()
    for key, price in DEFAULT_SEAT_PRICES.items():
        if key in package_name:
            return price

    monthly = resolved.pricing_config.get("cost_per_seat") or resolved.pricing_config.get("flat_monthly_cost")
    if monthly is not None:
        try:
            return Decimal(str(monthly))
        except Exception:  # noqa: BLE001
            pass

    if team_tool_assignment and team_tool_assignment.package_id:
        from app.models.admin import ToolPackage

        package = await session.get(ToolPackage, team_tool_assignment.package_id)
        if package and package.monthly_price is not None:
            return Decimal(str(package.monthly_price))

    billing = getattr(tool, "billing_type", None)
    if billing == "SEAT_BASED":
        return DEFAULT_SEAT_PRICES["business"]
    return DEFAULT_SEAT_PRICES["business"]
