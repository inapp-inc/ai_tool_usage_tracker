"""Permission service — DB reads/writes + Redis caching."""

from __future__ import annotations

import json
import logging
import uuid

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.permissions import RolePermission
from app.permissions.schemas import PageAccess, RolePermissionMatrix

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 minutes — matches frontend stale time

CONFIGURABLE_ROLES = ["team_admin", "finance_viewer", "auditor"]

ALL_PAGES = [
    "insights",
    "admin:teams",
    "admin:groups",
    "admin:members",
    "admin:credentials",
    "alerts",
    "uploads",
    "audit",
]

DEFAULT_PERMISSIONS: dict[str, dict[str, dict[str, bool]]] = {
    "team_admin": {
        "insights":          {"read": True,  "write": False},
        "admin:teams":       {"read": True,  "write": False},
        "admin:groups":      {"read": True,  "write": True},
        "admin:members":     {"read": True,  "write": True},
        "admin:credentials": {"read": False, "write": False},
        "alerts":            {"read": True,  "write": True},
        "uploads":           {"read": True,  "write": True},
        "audit":             {"read": False, "write": False},
    },
    "finance_viewer": {p: {"read": p == "insights", "write": False} for p in ALL_PAGES},
    "auditor": {
        p: {"read": p in ("insights", "audit"), "write": False} for p in ALL_PAGES
    },
}


def _cache_key(org_id: uuid.UUID) -> str:
    return f"role_permissions:{org_id}"


def _get_redis_client() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(str(settings.redis_url), decode_responses=True)


async def _invalidate_cache(org_id: uuid.UUID) -> None:
    try:
        client = _get_redis_client()
        await client.delete(_cache_key(org_id))
        await client.aclose()
    except Exception:
        logger.warning("Failed to invalidate permissions cache for org %s", org_id)


class PermissionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------ seed

    async def seed_defaults(self, org_id: uuid.UUID) -> None:
        """Insert default permissions for a new org (safe to call repeatedly)."""
        rows = [
            {
                "organization_id": org_id,
                "role": role,
                "page": page,
                "can_read": perms["read"],
                "can_write": perms["write"],
            }
            for role, page_map in DEFAULT_PERMISSIONS.items()
            for page, perms in page_map.items()
        ]
        stmt = (
            pg_insert(RolePermission)
            .values(rows)
            .on_conflict_do_nothing(
                index_elements=["organization_id", "role", "page"]
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()

    # ----------------------------------------------------------------- fetch

    async def get_org_permissions(
        self, org_id: uuid.UUID
    ) -> dict[str, dict[str, dict[str, bool]]]:
        """Return { role: { page: { read, write } } } — Redis-cached."""
        try:
            client = _get_redis_client()
            cached = await client.get(_cache_key(org_id))
            await client.aclose()
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis unavailable, falling back to DB for permissions")

        result = await self._session.execute(
            select(RolePermission).where(RolePermission.organization_id == org_id)
        )
        rows = result.scalars().all()

        if not rows:
            await self.seed_defaults(org_id)
            result = await self._session.execute(
                select(RolePermission).where(RolePermission.organization_id == org_id)
            )
            rows = result.scalars().all()

        perms: dict[str, dict[str, dict[str, bool]]] = {}
        for row in rows:
            perms.setdefault(row.role, {})[row.page] = {
                "read": row.can_read,
                "write": row.can_write,
            }

        try:
            client = _get_redis_client()
            await client.setex(_cache_key(org_id), CACHE_TTL, json.dumps(perms))
            await client.aclose()
        except Exception:
            pass

        return perms

    def has_permission(
        self,
        perms: dict[str, dict[str, dict[str, bool]]],
        role: str,
        page: str,
        action: str,
    ) -> bool:
        if role == "super_admin":
            return True
        return bool(perms.get(role, {}).get(page, {}).get(action, False))

    # ----------------------------------------------------------------- matrix

    def _rows_to_matrix(self, rows: list[RolePermission]) -> RolePermissionMatrix:
        data: dict[str, dict[str, dict[str, bool]]] = {r: {} for r in CONFIGURABLE_ROLES}
        for row in rows:
            if row.role in data:
                data[row.role][row.page] = {"read": row.can_read, "write": row.can_write}
        return RolePermissionMatrix(
            team_admin={p: PageAccess(**v) for p, v in data["team_admin"].items()},
            finance_viewer={p: PageAccess(**v) for p, v in data["finance_viewer"].items()},
            auditor={p: PageAccess(**v) for p, v in data["auditor"].items()},
        )

    async def get_matrix(self, org_id: uuid.UUID) -> RolePermissionMatrix:
        await self.seed_defaults(org_id)
        result = await self._session.execute(
            select(RolePermission).where(RolePermission.organization_id == org_id)
        )
        return self._rows_to_matrix(result.scalars().all())

    async def update_matrix(
        self,
        org_id: uuid.UUID,
        updated_by: uuid.UUID,
        matrix: RolePermissionMatrix,
    ) -> RolePermissionMatrix:
        matrix_dict = matrix.model_dump()
        rows_to_upsert = []
        for role in CONFIGURABLE_ROLES:
            for page, access in matrix_dict.get(role, {}).items():
                if page not in ALL_PAGES:
                    continue
                can_write = access.get("write", False)
                can_read  = access.get("read", False) or can_write  # write implies read
                rows_to_upsert.append({
                    "organization_id": org_id,
                    "role": role,
                    "page": page,
                    "can_read": can_read,
                    "can_write": can_write,
                    "updated_by": updated_by,
                })

        if rows_to_upsert:
            stmt = (
                pg_insert(RolePermission)
                .values(rows_to_upsert)
                .on_conflict_do_update(
                    index_elements=["organization_id", "role", "page"],
                    set_={
                        "can_read":   pg_insert(RolePermission).excluded.can_read,
                        "can_write":  pg_insert(RolePermission).excluded.can_write,
                        "updated_by": pg_insert(RolePermission).excluded.updated_by,
                    },
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()

        await _invalidate_cache(org_id)

        result = await self._session.execute(
            select(RolePermission).where(RolePermission.organization_id == org_id)
        )
        return self._rows_to_matrix(result.scalars().all())
