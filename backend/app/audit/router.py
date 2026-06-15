"""Audit log API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthenticatedUser
from app.core.rbac import require_super_admin
from app.db.session import get_session
from app.platform.org_store import OrgDataStore

router = APIRouter(prefix="/audit-log", tags=["Audit"])
AUDIT_KEY = "audit_log"


@router.get("", operation_id="listAuditLog")
async def list_audit_log(
    search: str = Query(default=""),
    category: str = Query(default=""),
    from_value: str = Query(default="", alias="from"),
    to_value: str = Query(default="", alias="to"),
    current_user: AuthenticatedUser = Depends(require_super_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    store = OrgDataStore(session)
    items = await store.list_items(current_user.organization_id, AUDIT_KEY)

    def in_range(created_at: str) -> bool:
        if not from_value and not to_value:
            return True
        try:
            ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if from_value:
                start = datetime.fromisoformat(from_value.replace("Z", "+00:00"))
                if ts < start:
                    return False
            if to_value:
                end = datetime.fromisoformat(to_value.replace("Z", "+00:00"))
                if ts > end:
                    return False
        except ValueError:
            return True
        return True

    filtered: list[dict[str, Any]] = []
    for item in items:
        if category and item.get("category") != category:
            continue
        if search:
            haystack = " ".join(
                str(item.get(key, ""))
                for key in (
                    "description",
                    "actor_name",
                    "actor_email",
                    "target_name",
                    "action",
                )
            ).lower()
            if search.lower() not in haystack:
                continue
        if not in_range(str(item.get("created_at", ""))):
            continue
        filtered.append(item)

    return {"data": filtered}
