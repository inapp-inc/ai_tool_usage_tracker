"""Alert rules API backed by organization settings."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthenticatedUser
from app.platform.org_store import OrgDataStore

RULES_KEY = "alert_rules"
EVENTS_KEY = "alert_events"


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._store = OrgDataStore(session)

    async def list_rules(self, user: AuthenticatedUser) -> list[dict[str, Any]]:
        return await self._store.list_items(user.organization_id, RULES_KEY)

    async def create_rule(
        self, user: AuthenticatedUser, body: dict[str, Any]
    ) -> dict[str, Any]:
        rule_id = str(uuid.uuid4())
        record = {
            "id": rule_id,
            "name": body["name"],
            "severity": body["severity"],
            "threshold_type": body["threshold_type"],
            "threshold_value": body["threshold_value"],
            "scope": body["scope"],
            "team_id": body.get("team_id"),
            "team_name": body.get("team_name"),
            "channel": body["channel"],
            "webhook_url": body.get("webhook_url"),
            "email_recipients": body.get("email_recipients", []),
            "status": body.get("status", "active"),
            "trigger_count": 0,
            "last_triggered_at": None,
            "created_at": datetime.now(UTC).isoformat(),
        }
        await self._store.append_item(user.organization_id, RULES_KEY, record)
        await self._session.commit()
        return record

    async def update_rule(
        self, user: AuthenticatedUser, rule_id: str, body: dict[str, Any]
    ) -> dict[str, Any] | None:
        updated = await self._store.update_item(
            user.organization_id, RULES_KEY, rule_id, body
        )
        if updated is None:
            return None
        await self._session.commit()
        return updated

    async def delete_rule(self, user: AuthenticatedUser, rule_id: str) -> bool:
        deleted = await self._store.delete_item(
            user.organization_id, RULES_KEY, rule_id
        )
        if deleted:
            await self._session.commit()
        return deleted

    async def list_events(self, user: AuthenticatedUser) -> list[dict[str, Any]]:
        return await self._store.list_items(user.organization_id, EVENTS_KEY)

    async def acknowledge_event(
        self, user: AuthenticatedUser, event_id: str
    ) -> dict[str, Any] | None:
        updated = await self._store.update_item(
            user.organization_id,
            EVENTS_KEY,
            event_id,
            {
                "acknowledged_at": datetime.now(UTC).isoformat(),
                "acknowledged_by": user.display_name or user.email,
            },
        )
        if updated is None:
            return None
        await self._session.commit()
        return updated
