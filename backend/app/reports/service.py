"""Report generation from dashboard analytics."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dashboard.scope import resolve_dashboard_scope
from app.dashboard.service import DashboardService
from app.models.auth import User
from app.models.reporting import ReportJob, ReportSubscription
from app.reports.repository import ReportRepository, SubscriptionRepository
from app.reports.schemas import (
    ReportGenerateRequest,
    ReportJobResponse,
    ReportListResponse,
    SubscriptionCreateRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
)
from app.users.repository import UserAdminRepository

FE_TYPE_TO_API = {
    "usage_summary": "tool_usage_summary",
    "cost_breakdown": "cost",
    "team_comparison": "team_usage",
    "user_activity": "user_usage",
    "budget_variance": "team_usage",
}

API_TYPE_FROM_FE = {value: key for key, value in FE_TYPE_TO_API.items()}


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._reports = ReportRepository(session)
        self._subscriptions = SubscriptionRepository(session)
        self._users = UserAdminRepository(session)
        self._dashboard = DashboardService(session)

    async def list_reports(self, user: User) -> ReportListResponse:
        rows = await self._reports.list_by_organization(user.organization_id)
        data: list[ReportJobResponse] = []
        for row in rows:
            creator = await self._users.get_by_id(row.created_by, user.organization_id)
            sub_count = await self._reports.subscription_count(row.id)
            data.append(self._to_response(row, creator.display_name if creator else None, sub_count))
        return ReportListResponse(data=data)

    async def generate_report(self, user: User, body: ReportGenerateRequest) -> ReportJobResponse:
        if body.format not in {"csv", "json"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only csv and json formats are supported currently.",
            )

        name = (body.name or f"{body.report_type} report").strip()[:100]
        team_ids = [str(team_id) for team_id in body.team_ids]
        if body.team_id and str(body.team_id) not in team_ids:
            team_ids.append(str(body.team_id))

        job = ReportJob(
            organization_id=user.organization_id,
            created_by=user.id,
            name=name,
            report_type=body.report_type,
            format=body.format,
            schedule=body.schedule,
            status="processing",
            period_from=body.from_dt,
            period_to=body.to_dt,
            team_ids=team_ids,
        )
        await self._reports.create(job)

        try:
            content = await self._build_artifact(user, body)
            job.artifact_content = content
            job.file_size_bytes = len(content.encode("utf-8"))
            job.status = "completed"
            job.completed_at = datetime.now(UTC)
            job.error_message = None
        except Exception as exc:  # noqa: BLE001 — persist failure on job row
            job.status = "failed"
            job.error_message = str(exc)[:500]
            job.completed_at = datetime.now(UTC)

        await self._session.commit()
        await self._session.refresh(job)
        creator = await self._users.get_by_id(user.id, user.organization_id)
        return self._to_response(job, creator.display_name if creator else None, 0)

    async def delete_report(self, user: User, job_id: UUID) -> None:
        row = await self._reports.get_by_id(job_id, user.organization_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        await self._reports.delete(row)
        await self._session.commit()

    async def download_report(self, user: User, job_id: UUID) -> Response:
        row = await self._reports.get_by_id(job_id, user.organization_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        if row.status != "completed" or not row.artifact_content:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report is not ready for download.",
            )

        media_type = "text/csv" if row.format == "csv" else "application/json"
        filename = f"{row.name.replace(' ', '_')}.{row.format}"
        return Response(
            content=row.artifact_content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    async def list_subscriptions(
        self,
        user: User,
        report_id: UUID,
    ) -> SubscriptionListResponse:
        report = await self._reports.get_by_id(report_id, user.organization_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        rows = await self._subscriptions.list_for_report(report_id, user.organization_id)
        data: list[SubscriptionResponse] = []
        for row in rows:
            creator = await self._users.get_by_id(row.created_by, user.organization_id)
            data.append(
                SubscriptionResponse(
                    id=row.id,
                    report_id=row.report_id,
                    channel=row.channel,
                    cadence=row.cadence,
                    email_recipients=row.email_recipients,
                    created_at=row.created_at,
                    created_by_name=creator.display_name if creator else None,
                )
            )
        return SubscriptionListResponse(data=data)

    async def create_subscription(
        self,
        user: User,
        report_id: UUID,
        body: SubscriptionCreateRequest,
    ) -> SubscriptionResponse:
        report = await self._reports.get_by_id(report_id, user.organization_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

        row = ReportSubscription(
            organization_id=user.organization_id,
            report_id=report_id,
            created_by=user.id,
            channel=body.channel,
            cadence=body.cadence,
            email_recipients=body.email_recipients,
        )
        await self._subscriptions.create(row)
        await self._session.commit()
        await self._session.refresh(row)
        creator = await self._users.get_by_id(user.id, user.organization_id)
        return SubscriptionResponse(
            id=row.id,
            report_id=row.report_id,
            channel=row.channel,
            cadence=row.cadence,
            email_recipients=row.email_recipients,
            created_at=row.created_at,
            created_by_name=creator.display_name if creator else None,
        )

    async def delete_subscription(
        self,
        user: User,
        report_id: UUID,
        subscription_id: UUID,
    ) -> None:
        row = await self._subscriptions.get_by_id(
            subscription_id,
            report_id,
            user.organization_id,
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found.")
        await self._subscriptions.delete(row)
        await self._session.commit()

    async def _build_artifact(self, user: User, body: ReportGenerateRequest) -> str:
        scope = await resolve_dashboard_scope(
            self._session,
            user,
            team_id=body.team_id,
        )
        from_dt = body.from_dt
        to_dt = body.to_dt

        if body.report_type in {"tool_usage_summary", "usage_summary"}:
            rows = await self._dashboard.get_usage_by_tool(
                scope, from_dt, to_dt, team_id=body.team_id
            )
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["tool_id", "tool_name", "total_tokens", "estimated_cost", "share_pct"])
            for item in rows.data:
                writer.writerow(
                    [
                        str(item.tool_id),
                        item.tool_name,
                        item.total_tokens,
                        str(item.estimated_cost or 0),
                        item.share_pct,
                    ]
                )
            return buffer.getvalue()

        if body.report_type in {"team_usage", "team_comparison", "budget_variance"}:
            rows = await self._dashboard.get_usage_by_team(scope, from_dt, to_dt)
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["team_id", "team_name", "total_tokens", "estimated_cost"])
            for item in rows.data:
                if body.team_ids and str(item.team_id) not in {str(t) for t in body.team_ids}:
                    continue
                writer.writerow(
                    [
                        str(item.team_id),
                        item.team_name,
                        item.total_tokens,
                        str(item.estimated_cost),
                    ]
                )
            return buffer.getvalue()

        if body.report_type == "cost":
            cost = await self._dashboard.get_cost(scope, from_dt, to_dt, team_id=body.team_id)
            tokens = await self._dashboard.get_tokens(scope, from_dt, to_dt, team_id=body.team_id)
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["metric", "value"])
            writer.writerow(["total_tokens", tokens.total_tokens])
            writer.writerow(["actual_spend", str(cost.actual_spend)])
            writer.writerow(["package_allowance", str(cost.package_allowance)])
            writer.writerow(["overage_cost", str(cost.overage_cost)])
            return buffer.getvalue()

        if body.report_type == "user_usage":
            team_id = body.team_id
            if team_id is None and body.team_ids:
                team_id = body.team_ids[0]
            consumers = await self._dashboard.get_top_consumers(
                scope,
                from_dt,
                to_dt,
                limit=100,
                entity="users",
                team_id=team_id,
            )
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["user_id", "user_name", "team_name", "total_tokens", "estimated_cost"])
            for item in consumers.users:
                writer.writerow(
                    [
                        str(item.entity_id),
                        item.entity_name,
                        item.team_name or "",
                        item.total_tokens,
                        str(item.estimated_cost or 0),
                    ]
                )
            return buffer.getvalue()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported report type: {body.report_type}",
        )

    def _to_response(
        self,
        row: ReportJob,
        created_by_name: str | None,
        subscription_count: int,
    ) -> ReportJobResponse:
        file_size_kb = None
        if row.file_size_bytes is not None:
            file_size_kb = max(1, round(row.file_size_bytes / 1024))
        status_value = row.status if row.status != "failed" else "failed"
        return ReportJobResponse(
            job_id=row.id,
            name=row.name,
            report_type=row.report_type,  # type: ignore[arg-type]
            status=status_value,  # type: ignore[arg-type]
            format=row.format,  # type: ignore[arg-type]
            from_dt=row.period_from,
            to_dt=row.period_to,
            schedule=row.schedule,
            team_ids=[str(team_id) for team_id in row.team_ids],
            created_at=row.created_at,
            completed_at=row.completed_at,
            error_message=row.error_message,
            file_size_kb=file_size_kb,
            created_by_name=created_by_name,
            subscription_count=subscription_count,
        )
