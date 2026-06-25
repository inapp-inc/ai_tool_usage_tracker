"""Persist Copilot billing CSV aggregates and evaluate team cost alerts."""

from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.copilot.billing_import import (
    CopilotBillingAggregate,
    CopilotBillingRow,
    extract_row_amounts,
    summarize_aggregates,
)
from app.copilot.billing_period import normalize_billing_period, period_from_aggregates, report_period_bounds, resolve_billing_period
from app.models.admin import Team, TeamTool, Tool, ToolPackage
from app.models.copilot import CopilotBillingImport, CopilotOrganization
from app.models.ingestion import ParsedRow, Upload
from app.notifications.repository import NotificationRepository
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import catalogue_tool_id_from_connected

logger = logging.getLogger(__name__)


class CopilotBillingImportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._team_tools = TeamToolRepository(session)

    async def delete_by_upload_id(self, upload_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(CopilotBillingImport).where(CopilotBillingImport.upload_id == upload_id)
        )

    async def backfill_null_periods(
        self,
        upload_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> None:
        result = await self._session.execute(
            select(CopilotBillingImport).where(CopilotBillingImport.upload_id == upload_id)
        )
        for row in result.scalars():
            if row.billing_period_start is None:
                row.billing_period_start = period_start
            if row.billing_period_end is None:
                row.billing_period_end = period_end

    async def find_period_conflicts(
        self,
        upload: Upload,
        *,
        organization_id: uuid.UUID,
        aggregates: list[CopilotBillingAggregate],
    ) -> list[dict[str, str]]:
        tool = await self._session.get(Tool, upload.tool_id) if upload.tool_id else None
        if tool is None or upload.team_id is None or upload.tool_id is None:
            return []
        catalogue_id = catalogue_tool_id_from_connected(tool) or upload.tool_id
        conflicts: list[dict[str, str]] = []
        seen: set[tuple[date | None, date | None]] = set()
        for aggregate in aggregates:
            period_start, period_end = resolve_billing_period(
                aggregate.billing_period_start,
                aggregate.billing_period_end,
            )
            period_key = (period_start, period_end)
            if period_key in seen or period_start is None or period_end is None:
                continue
            seen.add(period_key)
            existing = await self._existing_active_import(
                organization_id=organization_id,
                team_id=upload.team_id,
                tool_id=catalogue_id,
                period_start=period_start,
                period_end=period_end,
                exclude_upload_id=upload.id,
            )
            if existing is not None:
                conflicts.append(
                    {
                        "billing_period_start": period_start.isoformat(),
                        "billing_period_end": period_end.isoformat(),
                        "existing_filename": existing.get("filename") or "existing upload",
                        "existing_upload_id": existing.get("upload_id") or "",
                    }
                )
        return conflicts

    async def assert_no_period_conflicts(
        self,
        upload: Upload,
        *,
        organization_id: uuid.UUID,
        aggregates: list[CopilotBillingAggregate],
    ) -> None:
        conflicts = await self.find_period_conflicts(
            upload,
            organization_id=organization_id,
            aggregates=aggregates,
        )
        if not conflicts:
            return
        first = conflicts[0]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Billing period {first['billing_period_start']} to "
                f"{first['billing_period_end']} is already imported "
                f"({first['existing_filename']}). Delete that upload before importing again."
            ),
        )

    async def commit_from_upload(
        self,
        upload: Upload,
        *,
        organization_id: uuid.UUID,
        aggregates: list[CopilotBillingAggregate],
    ) -> int:
        if upload.team_id is None or upload.tool_id is None:
            raise ValueError("Copilot billing import requires team_id and tool_id on the upload.")

        tool = await self._session.get(Tool, upload.tool_id)
        if tool is None or tool.vendor != "copilot":
            raise ValueError("Upload tool must be GitHub Copilot.")

        catalogue_id = catalogue_tool_id_from_connected(tool) or upload.tool_id
        assignment = await self._team_tools.get_by_team_and_tool(upload.team_id, catalogue_id)
        if assignment is None and catalogue_id != upload.tool_id:
            assignment = await self._team_tools.get_by_team_and_tool(upload.team_id, upload.tool_id)
        package_id = assignment.package_id if assignment else None

        period_start, period_end = period_from_aggregates(
            aggregates,
            fallback_anchor=date.today(),
        )

        from app.copilot.billing_import import apply_configured_subscription
        from app.copilot.service import CopilotAnalyticsService

        _, _, configured_subscription, _ = CopilotAnalyticsService._configured_copilot_pricing(
            assignment
        )
        apply_configured_subscription(aggregates, configured_subscription)

        ingested = 0
        total_for_alert = Decimal("0")
        for aggregate in aggregates:
            row_start, row_end = resolve_billing_period(
                aggregate.billing_period_start,
                aggregate.billing_period_end,
                report_start=period_start,
                report_end=period_end,
            )
            row = CopilotBillingImport(
                organization_id=organization_id,
                team_id=upload.team_id,
                tool_id=catalogue_id,
                upload_id=upload.id,
                package_id=package_id,
                billing_period_start=row_start or period_start,
                billing_period_end=row_end or period_end,
                sku=aggregate.sku,
                monthly_cost_limit=aggregate.monthly_cost_limit,
                additional_cost=aggregate.additional_cost,
                total_cost=aggregate.total_cost,
                seat_count=aggregate.seat_count,
                raw_summary={
                    "credits_cost": str(aggregate.credits_cost),
                    "gross_total": str(aggregate.total_cost),
                    "row_count": aggregate.row_count,
                },
            )
            self._session.add(row)
            ingested += 1
            total_for_alert += aggregate.total_cost

        await self._sync_copilot_organization(
            upload.team_id,
            tool_id=catalogue_id,
            aggregates=aggregates,
            assignment=assignment,
        )
        if assignment is not None and total_for_alert > 0:
            from app.notifications.import_cost_alert import evaluate_import_cost_alert

            await evaluate_import_cost_alert(self._session, assignment)
        return ingested

    async def _sync_copilot_organization(
        self,
        team_id: uuid.UUID,
        *,
        tool_id: uuid.UUID,
        aggregates: list[CopilotBillingAggregate],
        assignment: TeamTool | None,
    ) -> None:
        total_cost = sum((row.total_cost for row in aggregates), Decimal("0"))
        seat_count = max((row.seat_count or 0 for row in aggregates), default=0)
        subscription_type = None
        if assignment and assignment.package_id:
            package = await self._session.get(ToolPackage, assignment.package_id)
            subscription_type = package.package_name if package else None

        org_key = f"csv-import-{team_id}"
        result = await self._session.execute(
            select(CopilotOrganization).where(
                CopilotOrganization.team_id == team_id,
                CopilotOrganization.organization_id == org_key,
            )
        )
        org = result.scalar_one_or_none()
        if org is None:
            org = CopilotOrganization(
                team_id=team_id,
                tool_id=tool_id,
                organization_id=org_key,
                organization_name="CSV Import",
                subscription_type=subscription_type,
                monthly_cost=total_cost,
                total_seats=seat_count or (assignment.seat_count if assignment else 0),
                assigned_seats=seat_count or (assignment.seat_count if assignment else 0),
            )
            self._session.add(org)
        else:
            org.tool_id = tool_id
            org.subscription_type = subscription_type
            org.monthly_cost = total_cost
            if seat_count:
                org.total_seats = seat_count
                org.assigned_seats = seat_count

    async def _evaluate_cost_alert(
        self,
        *,
        organization_id: uuid.UUID,
        team_id: uuid.UUID,
        assignment: TeamTool,
        total_cost: Decimal,
        aggregates: list[CopilotBillingAggregate],
    ) -> None:
        threshold = assignment.alert_threshold_usd
        if threshold is None or threshold <= 0:
            return
        if total_cost < threshold:
            return

        team = await self._session.get(Team, team_id)
        package_name = assignment.plan_name or "Copilot"
        if assignment.package_id:
            package = await self._session.get(ToolPackage, assignment.package_id)
            if package:
                package_name = package.package_name

        period_label = ""
        if aggregates and aggregates[0].billing_period_start:
            period_label = aggregates[0].billing_period_start.isoformat()

        title = f"Copilot cost alert: {team.name if team else team_id}"
        body = (
            f"{package_name} spend is ${total_cost:.2f} "
            f"(threshold ${threshold:.2f})"
            + (f" for period starting {period_label}." if period_label else ".")
        )
        payload = {
            "team_id": str(team_id),
            "tool_id": str(assignment.tool_id),
            "total_cost": str(total_cost),
            "alert_threshold_usd": str(threshold),
            "package_name": package_name,
            "deep_link": f"/insights?team_id={team_id}&tool_id={assignment.tool_id}",
        }

        repo = NotificationRepository(self._session)
        from app.users.repository import UserAdminRepository

        users = await UserAdminRepository(self._session).list_by_organization(organization_id)
        admin_users = [user for user in users if user.role in {"super_admin", "team_admin"}]
        recipient_ids = {user.id for user in admin_users if user.role == "super_admin"}
        for user in admin_users:
            if user.role == "team_admin":
                from app.teams.membership_repository import TeamMembershipRepository

                memberships = await TeamMembershipRepository(self._session).list_active_for_team(team_id)
                if any(row.user_id == user.id for row in memberships):
                    recipient_ids.add(user.id)

        for user_id in recipient_ids:
            await repo.create(
                organization_id=organization_id,
                user_id=user_id,
                notification_type="copilot_cost_alert",
                severity="warning",
                title=title,
                body=body,
                payload=payload,
            )

        logger.info(
            "Copilot cost alert | team_id=%s total=%s threshold=%s recipients=%s",
            team_id,
            total_cost,
            threshold,
            len(recipient_ids),
        )

    async def _existing_active_import(
        self,
        *,
        organization_id: uuid.UUID,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        period_start: date,
        period_end: date,
        exclude_upload_id: uuid.UUID | None = None,
    ) -> dict[str, str] | None:
        result = await self._session.execute(
            select(CopilotBillingImport, Upload)
            .outerjoin(Upload, CopilotBillingImport.upload_id == Upload.id)
            .where(
                CopilotBillingImport.organization_id == organization_id,
                CopilotBillingImport.team_id == team_id,
                CopilotBillingImport.tool_id == tool_id,
                CopilotBillingImport.billing_period_start == period_start,
                CopilotBillingImport.billing_period_end == period_end,
            )
            .limit(1)
        )
        row = result.first()
        if row is None:
            return None
        billing_import, upload = row
        if upload is not None:
            if upload.deleted_at is not None:
                return None
            if exclude_upload_id is not None and upload.id == exclude_upload_id:
                return None
            return {
                "upload_id": str(upload.id),
                "filename": upload.filename,
            }
        if exclude_upload_id is not None and billing_import.upload_id == exclude_upload_id:
            return None
        return {
            "upload_id": str(billing_import.upload_id) if billing_import.upload_id else "",
            "filename": "existing import",
        }


def copilot_rows_from_parsed(parsed_rows: list[ParsedRow]) -> list[CopilotBillingRow]:
    from datetime import date

    rows: list[CopilotBillingRow] = []
    for parsed in parsed_rows:
        if parsed.error_reason:
            continue
        mapped = parsed.mapped_payload if isinstance(parsed.mapped_payload, dict) else {}

        def _as_date(value: object) -> date | None:
            if value is None or value == "":
                return None
            if isinstance(value, date):
                return value
            text = str(value).strip()
            if not text:
                return None
            try:
                return date.fromisoformat(text[:10])
            except ValueError:
                return None

        unit_type = str(mapped.get("unit_type") or "").strip().lower().replace("_", "-")
        raw = parsed.raw_payload if isinstance(parsed.raw_payload, dict) else {}
        net_amount, gross_amount = extract_row_amounts(mapped, raw)
        usage_date = _as_date(mapped.get("usage_date"))
        raw_start = _as_date(mapped.get("billing_period_start"))
        raw_end = _as_date(mapped.get("billing_period_end"))
        rows.append(
            CopilotBillingRow(
                row_number=parsed.row_number,
                sku=str(mapped.get("sku") or "").strip().lower(),
                unit_type=unit_type,
                monthly_amount=Decimal(str(mapped.get("monthly_amount") or 0)),
                net_amount=net_amount,
                gross_amount=gross_amount,
                quantity=int(mapped.get("quantity") or 0),
                billing_period_start=raw_start,
                billing_period_end=raw_end,
                usage_date=usage_date,
                user_login=mapped.get("user_login"),
                raw_payload=parsed.raw_payload if isinstance(parsed.raw_payload, dict) else {},
            )
        )
    if rows:
        report_start, report_end = report_period_bounds(
            usage_dates=[row.usage_date for row in rows if row.usage_date],
            period_starts=[row.billing_period_start for row in rows if row.billing_period_start],
            period_ends=[row.billing_period_end for row in rows if row.billing_period_end],
        )
        for row in rows:
            row.billing_period_start, row.billing_period_end = resolve_billing_period(
                row.billing_period_start,
                row.billing_period_end,
                report_start=report_start,
                report_end=report_end,
            )
    return rows


def preview_summary_from_rows(rows: list[CopilotBillingRow]) -> dict[str, object]:
    from app.copilot.billing_import import aggregate_copilot_billing

    return summarize_aggregates(aggregate_copilot_billing(rows))
