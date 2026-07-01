"""Persist Figma billing CSV imports."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.figma.billing_import import FigmaBillingAggregate, FigmaBillingRow, aggregate_figma_billing_rows
from app.figma.pricing import calculate_figma_row_costs, figma_pricing_from_assignment
from app.models.admin import TeamTool, Tool
from app.models.figma import FigmaBillingImport, FigmaBillingImportUser
from app.models.ingestion import ParsedRow, Upload
from app.teams.team_tool_repository import TeamToolRepository
from app.tools.catalogue import catalogue_tool_id_from_connected


class FigmaBillingImportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._team_tools = TeamToolRepository(session)

    async def delete_by_upload_id(self, upload_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(FigmaBillingImport.id).where(FigmaBillingImport.upload_id == upload_id)
        )
        import_ids = [row[0] for row in result.all()]
        if import_ids:
            await self._session.execute(
                delete(FigmaBillingImportUser).where(
                    FigmaBillingImportUser.import_id.in_(import_ids)
                )
            )
            await self._session.execute(
                delete(FigmaBillingImport).where(FigmaBillingImport.id.in_(import_ids))
            )

    async def find_period_conflicts(
        self,
        upload: Upload,
        *,
        organization_id: uuid.UUID,
        aggregates: list[FigmaBillingAggregate],
    ) -> list[dict[str, str]]:
        if upload.team_id is None or upload.tool_id is None:
            return []
        tool = await self._session.get(Tool, upload.tool_id)
        if tool is None:
            return []
        catalogue_id = catalogue_tool_id_from_connected(tool) or upload.tool_id
        conflicts: list[dict[str, str]] = []
        seen: set[tuple[date | None, date | None]] = set()
        for aggregate in aggregates:
            period_key = (aggregate.usage_period_start, aggregate.usage_period_end)
            if period_key in seen or period_key[0] is None or period_key[1] is None:
                continue
            seen.add(period_key)
            existing = await self._existing_active_import(
                organization_id=organization_id,
                team_id=upload.team_id,
                tool_id=catalogue_id,
                period_start=period_key[0],
                period_end=period_key[1],
                exclude_upload_id=upload.id,
            )
            if existing is not None:
                conflicts.append(
                    {
                        "usage_period_start": period_key[0].isoformat(),
                        "usage_period_end": period_key[1].isoformat(),
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
        aggregates: list[FigmaBillingAggregate],
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
                f"Usage period {first['usage_period_start']} to "
                f"{first['usage_period_end']} is already imported "
                f"({first['existing_filename']}). Delete that upload before importing again."
            ),
        )

    async def commit_from_upload(
        self,
        upload: Upload,
        *,
        organization_id: uuid.UUID,
        billing_rows: list[FigmaBillingRow],
        row_indexes: list[int],
        matched_user_ids: dict[int, uuid.UUID | None],
    ) -> int:
        if upload.team_id is None or upload.tool_id is None:
            raise ValueError("Figma billing import requires team_id and tool_id on the upload.")

        tool = await self._session.get(Tool, upload.tool_id)
        if tool is None or tool.vendor != "figma":
            raise ValueError("Upload tool must be Figma.")

        catalogue_id = catalogue_tool_id_from_connected(tool) or upload.tool_id
        assignment = await self._team_tools.get_by_team_and_tool(upload.team_id, catalogue_id)
        if assignment is None and catalogue_id != upload.tool_id:
            assignment = await self._team_tools.get_by_team_and_tool(upload.team_id, upload.tool_id)
        package_id = assignment.package_id if assignment else None
        pricing = figma_pricing_from_assignment(assignment)

        valid_rows: list[FigmaBillingRow] = []
        valid_indexes: list[int] = []
        for index in row_indexes:
            if index < 0 or index >= len(billing_rows):
                continue
            row = billing_rows[index]
            if row.error_reason is not None:
                continue
            valid_rows.append(row)
            valid_indexes.append(index)

        from app.figma.billing_import import apply_subscription_usage_periods

        apply_subscription_usage_periods(
            valid_rows,
            assignment.subscription_start if assignment else None,
        )

        row_costs: list[tuple[Decimal, Decimal, Decimal]] = []
        grouped_rows: dict[
            tuple[date | None, date | None],
            list[tuple[FigmaBillingRow, tuple[Decimal, Decimal, Decimal], uuid.UUID | None]],
        ] = {}
        for row, index in zip(valid_rows, valid_indexes, strict=True):
            seat_cost, paid_cost, total = calculate_figma_row_costs(
                seat_type=row.seat_type,
                seat_credits_used=row.seat_credits_used,
                paid_credits_used=row.paid_credits_used,
                pricing=pricing,
            )
            costs = (seat_cost, paid_cost, total)
            row_costs.append(costs)
            key = (row.usage_period_start, row.usage_period_end)
            matched = matched_user_ids.get(index)
            grouped_rows.setdefault(key, []).append((row, costs, matched))

        aggregates = aggregate_figma_billing_rows(valid_rows, row_costs=row_costs)

        ingested = 0
        for aggregate in aggregates:
            period_key = (aggregate.usage_period_start, aggregate.usage_period_end)
            import_row = FigmaBillingImport(
                organization_id=organization_id,
                team_id=upload.team_id,
                tool_id=catalogue_id,
                upload_id=upload.id,
                package_id=package_id,
                usage_period_start=aggregate.usage_period_start,
                usage_period_end=aggregate.usage_period_end,
                total_seat_cost=aggregate.total_seat_cost,
                total_paid_cost=aggregate.total_paid_cost,
                total_cost=aggregate.total_cost,
                full_seat_count=aggregate.full_seat_count,
                view_seat_count=aggregate.view_seat_count,
                user_count=aggregate.user_count,
                raw_summary={
                    "row_count": aggregate.row_count,
                    "credits_per_usd": str(pricing.credits_per_usd)
                    if pricing.credits_per_usd is not None
                    else None,
                },
            )
            self._session.add(import_row)
            await self._session.flush()

            for row, costs, matched_user_id in grouped_rows.get(period_key, []):
                seat_cost, paid_cost, total = costs
                self._session.add(
                    FigmaBillingImportUser(
                        import_id=import_row.id,
                        figma_user_id=row.figma_user_id,
                        user_email=row.user_email,
                        user_name=row.user_name,
                        seat_type=row.seat_type,
                        seat_credits_used=row.seat_credits_used,
                        paid_credits_used=row.paid_credits_used,
                        seat_cost_usd=seat_cost,
                        paid_cost_usd=paid_cost,
                        total_cost_usd=total,
                        last_activity_at=row.last_activity,
                        matched_user_id=matched_user_id,
                        raw_payload=row.raw_payload,
                    )
                )
            ingested += 1

        if assignment is not None and aggregates:
            from app.notifications.import_cost_alert import evaluate_import_cost_alert

            await evaluate_import_cost_alert(self._session, assignment)
        return ingested

    async def _existing_active_import(
        self,
        *,
        organization_id: uuid.UUID,
        team_id: uuid.UUID,
        tool_id: uuid.UUID,
        period_start: date,
        period_end: date,
        exclude_upload_id: uuid.UUID,
    ) -> dict[str, str] | None:
        from app.models.ingestion import Upload as UploadModel

        stmt = (
            select(FigmaBillingImport, UploadModel.filename)
            .outerjoin(UploadModel, FigmaBillingImport.upload_id == UploadModel.id)
            .where(
                FigmaBillingImport.organization_id == organization_id,
                FigmaBillingImport.team_id == team_id,
                FigmaBillingImport.tool_id == tool_id,
                FigmaBillingImport.usage_period_start == period_start,
                FigmaBillingImport.usage_period_end == period_end,
                FigmaBillingImport.upload_id != exclude_upload_id,
            )
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        billing_import, filename = row
        return {
            "upload_id": str(billing_import.upload_id) if billing_import.upload_id else "",
            "filename": filename or "",
        }


def figma_rows_from_parsed(parsed_rows: list[ParsedRow]) -> list[FigmaBillingRow]:
    from datetime import datetime

    rows: list[FigmaBillingRow] = []
    for parsed in parsed_rows:
        mapped = parsed.mapped_payload if isinstance(parsed.mapped_payload, dict) else {}

        def _as_date(value: object) -> date | None:
            if value is None or value == "":
                return None
            if isinstance(value, date):
                return value
            try:
                return date.fromisoformat(str(value)[:10])
            except ValueError:
                return None

        def _as_datetime(value: object) -> datetime | None:
            if value is None or value == "":
                return None
            text = str(value).strip()
            try:
                return datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                parsed_date = _as_date(text)
                return datetime.combine(parsed_date, datetime.min.time()) if parsed_date else None

        seat_type = str(mapped.get("seat_type") or "full").strip().lower()
        if seat_type in {"view", "viewer", "collab", "collaborator"}:
            seat_type = "view"
        else:
            seat_type = "full"

        rows.append(
            FigmaBillingRow(
                row_number=parsed.row_number,
                figma_user_id=mapped.get("figma_user_id") or mapped.get("user_id"),
                user_email=mapped.get("user_email"),
                user_name=mapped.get("user_name"),
                seat_type=seat_type,
                seat_credits_used=Decimal(str(mapped.get("seat_credits_used") or 0)),
                paid_credits_used=Decimal(str(mapped.get("paid_credits_used") or 0)),
                last_activity=_as_datetime(mapped.get("last_activity")),
                usage_period_start=_as_date(mapped.get("usage_period_start")),
                usage_period_end=_as_date(mapped.get("usage_period_end")),
                raw_payload=parsed.raw_payload if isinstance(parsed.raw_payload, dict) else {},
            )
        )

    from app.copilot.billing_period import report_period_bounds, resolve_billing_period

    valid = [row for row in rows if row.usage_period_start or row.usage_period_end]
    report_start, report_end = report_period_bounds(
        period_starts=[row.usage_period_start for row in valid if row.usage_period_start],
        period_ends=[row.usage_period_end for row in valid if row.usage_period_end],
    )
    for row in rows:
        row.usage_period_start, row.usage_period_end = resolve_billing_period(
            row.usage_period_start,
            row.usage_period_end,
            report_start=report_start,
            report_end=report_end,
        )
    return rows
