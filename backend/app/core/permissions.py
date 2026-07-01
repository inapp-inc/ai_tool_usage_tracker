"""Dynamic permission enforcement — replaces rbac.py guards (Phase 2 cutover)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.models.auth import User
from app.models.roles import RolePermission, VALID_RESOURCES
from app.teams.membership_repository import TeamMembershipRepository

ORG_WIDE_ROLE_NAMES = frozenset({"super_admin", "org_admin", "organization_admin"})
ORG_ADMIN_NOTIFY_ROLES = ORG_WIDE_ROLE_NAMES | frozenset({"team_admin"})
ORG_UPLOAD_ROLES = ORG_ADMIN_NOTIFY_ROLES

PermissionRow = dict[str, bool]


class PermissionCache:
    """In-process TTL cache keyed by role_id."""

    _store: dict[uuid.UUID, tuple[dict[str, PermissionRow], float]] = {}
    TTL = 60.0

    @classmethod
    def _evaluate(cls, row: PermissionRow | None, action: str) -> bool:
        if row is None:
            return False
        if action == "write":
            return bool(row.get("can_write"))
        if action == "read":
            return bool(row.get("can_read") or row.get("can_write"))
        return False

    @classmethod
    async def _load(cls, role_id: uuid.UUID, session: AsyncSession) -> dict[str, PermissionRow]:
        result = await session.execute(
            select(RolePermission).where(RolePermission.role_id == role_id)
        )
        rows = result.scalars().all()
        return {
            row.resource: {
                "can_read": row.can_read,
                "can_write": row.can_write,
                "team_scoped": row.team_scoped,
            }
            for row in rows
        }

    @classmethod
    async def check(
        cls,
        role_id: uuid.UUID,
        resource: str,
        action: str,
        session: AsyncSession,
    ) -> bool:
        now = time.monotonic()
        if role_id in cls._store:
            perms, expiry = cls._store[role_id]
            if now < expiry:
                return cls._evaluate(perms.get(resource), action)

        perms = await cls._load(role_id, session)
        cls._store[role_id] = (perms, now + cls.TTL)
        return cls._evaluate(perms.get(resource), action)

    @classmethod
    async def get_row(
        cls,
        role_id: uuid.UUID,
        resource: str,
        session: AsyncSession,
    ) -> PermissionRow | None:
        now = time.monotonic()
        if role_id in cls._store:
            perms, expiry = cls._store[role_id]
            if now < expiry:
                return perms.get(resource)

        perms = await cls._load(role_id, session)
        cls._store[role_id] = (perms, now + cls.TTL)
        return perms.get(resource)

    @classmethod
    def invalidate(cls, role_id: uuid.UUID) -> None:
        cls._store.pop(role_id, None)

    @classmethod
    def clear(cls) -> None:
        """Test helper — reset cache between tests."""
        cls._store.clear()


def require_permission(resource: str, action: str) -> Callable:
    """FastAPI dependency factory for resource-level permission checks."""

    if resource not in VALID_RESOURCES:
        raise ValueError(f"Unknown resource: {resource}")
    if action not in ("read", "write"):
        raise ValueError(f"Unknown action: {action}")

    async def _guard(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        if current_user.role_name in ORG_WIDE_ROLE_NAMES:
            return current_user

        role_id = current_user.role_id
        if role_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        allowed = await PermissionCache.check(role_id, resource, action, session)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return _guard


def get_scoped_team_ids_for(resource: str) -> Callable:
    """Dependency factory returning managed team IDs when permission is team_scoped."""

    async def _dependency(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> list[uuid.UUID]:
        if current_user.role_name in ORG_WIDE_ROLE_NAMES:
            return []

        role_id = current_user.role_id
        if role_id is None:
            return []

        row = await PermissionCache.get_row(role_id, resource, session)
        if row is None or not row.get("team_scoped"):
            return []

        repo = TeamMembershipRepository(session)
        return await repo.active_team_ids_for_user(current_user.id)

    return _dependency


def require_super_admin() -> Callable:
    """Guard for role-management endpoints — super_admin only."""

    async def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return _guard
