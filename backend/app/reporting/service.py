"""Reporting API backed by organization settings."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthenticatedUser
from app.platform.org_store import OrgDataStore

REPORTS_KEY = "reports"
SUBSCRIPTIONS_KEY = "report_subscriptions"


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._store = OrgDataStore(session)

    async def list_reports(self, user: AuthenticatedUser) -> list[dict[str, Any]]:
        return await self._store.list_items(user.organization_id, REPORTS_KEY)

    async def create_report(
        self, user: AuthenticatedUser, body: dict[str, Any]
    ) -> dict[str, Any]:
        report_id = str(uuid.uuid4())
        record = {
            "id": report_id,
            "name": body["name"],
            "type": body["type"],
            "format": body["format"],
            "status": "completed",
            "schedule": body["schedule"],
            "period_from": body["period_from"],
            "period_to": body["period_to"],
            "team_ids": body.get("team_ids", []),
            "generated_at": datetime.now(UTC).isoformat(),
            "file_size_kb": 64,
            "created_by_name": user.display_name or user.email,
            "created_at": datetime.now(UTC).isoformat(),
            "error_message": None,
            "subscription_count": 0,
        }
        await self._store.append_item(user.organization_id, REPORTS_KEY, record)
        await self._session.commit()
        return record

    async def delete_report(self, user: AuthenticatedUser, report_id: str) -> bool:
        deleted = await self._store.delete_item(
            user.organization_id, REPORTS_KEY, report_id
        )
        if deleted:
            subs = await self._store.list_items(
                user.organization_id, SUBSCRIPTIONS_KEY
            )
            subs = [s for s in subs if s.get("report_id") != report_id]
            await self._store.save_items(
                user.organization_id, SUBSCRIPTIONS_KEY, subs
            )
            await self._session.commit()
        return deleted

    async def list_subscriptions(
        self, user: AuthenticatedUser, report_id: str
    ) -> list[dict[str, Any]]:
        items = await self._store.list_items(user.organization_id, SUBSCRIPTIONS_KEY)
        return [item for item in items if item.get("report_id") == report_id]

    async def create_subscription(
        self, user: AuthenticatedUser, report_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "channel": body["channel"],
            "cadence": body["cadence"],
            "email_recipients": body.get("email_recipients", []),
            "created_at": datetime.now(UTC).isoformat(),
            "created_by_name": user.display_name or user.email,
        }
        await self._store.append_item(
            user.organization_id, SUBSCRIPTIONS_KEY, record
        )
        reports = await self._store.list_items(user.organization_id, REPORTS_KEY)
        for report in reports:
            if report.get("id") == report_id:
                await self._store.update_item(
                    user.organization_id,
                    REPORTS_KEY,
                    report_id,
                    {
                        "subscription_count": int(
                            report.get("subscription_count", 0)
                        )
                        + 1
                    },
                )
                break
        await self._session.commit()
        return record

    async def delete_subscription(
        self, user: AuthenticatedUser, report_id: str, subscription_id: str
    ) -> bool:
        items = await self._store.list_items(
            user.organization_id, SUBSCRIPTIONS_KEY
        )
        filtered = [
            item
            for item in items
            if not (
                item.get("id") == subscription_id
                and item.get("report_id") == report_id
            )
        ]
        if len(filtered) == len(items):
            return False
        await self._store.save_items(
            user.organization_id, SUBSCRIPTIONS_KEY, filtered
        )
        reports = await self._store.list_items(user.organization_id, REPORTS_KEY)
        for report in reports:
            if report.get("id") == report_id:
                await self._store.update_item(
                    user.organization_id,
                    REPORTS_KEY,
                    report_id,
                    {
                        "subscription_count": max(
                            0, int(report.get("subscription_count", 0)) - 1
                        )
                    },
                )
                break
        await self._session.commit()
        return True
