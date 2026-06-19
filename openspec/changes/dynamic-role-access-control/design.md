# Design: Dynamic Role Access Control

## Context

The codebase currently enforces RBAC via five hardcoded role strings stored as
a VARCHAR enum on `auth.users.role` and checked in `backend/app/core/rbac.py`
through four FastAPI `Depends()` functions: `require_team_admin_or_above`,
`require_finance_viewer_access`, `require_auditor_access`, and
`get_managed_team_ids`. Any change to who can access what requires a code
change and a redeploy.

Stakeholders require that a Super Admin can create custom roles, assign
resource-level read/write permissions per role through a settings UI, and link
users to roles — all without touching code. This design replaces the static enum
with a DB-backed permission model.

**In-force ADRs constraining this design:**

| ADR | Constraint |
|---|---|
| ADR-001 | Modular monolith — new `roles/` bounded context added, no separate service |
| ADR-002 | FastAPI + Python — no framework change |
| ADR-003 | PostgreSQL as system of record — new tables in `auth` schema |
| ADR-005 | JWT + server-side RBAC — JWT stays; RBAC policy layer moves to DB |
| ADR-012 | API-first — OpenAPI spec updated before/alongside implementation |
| ADR-013 | Phase 1 secrets via `.env` — no new secret management required |

ADR-005's hardcoded role policy section is superseded by this change. A new ADR
(ADR-020) is recorded capturing the dynamic permissions decision.

---

## Goals / Non-Goals

### Goals

- Replace `auth.users.role` VARCHAR with `auth.users.role_id` UUID FK.
- Seed five system roles and their current permission sets on migration.
- Provide `require_permission(resource, action)` factory used in all routers.
- Expose CRUD API for roles and their permission matrices (super_admin only).
- Deliver Settings > Roles matrix UI and user role assignment dropdown.
- In-process TTL permission cache (60 s) to avoid per-request DB hits.

### Non-Goals

- Fine-grained field-level permissions (read whole resource or nothing).
- Row-level security at the database layer (app-layer scoping only).
- Permission inheritance / role hierarchy.
- SSO/SAML role mapping (Phase 2, FR-P2-002).
- Multi-process cache synchronisation (Redis cache deferred to Phase 2 if needed).

---

## Decisions

### 1. Two-phase database migration

**Decision:** Migration runs in two Alembic revisions:
- **Rev A (`016_roles_add_tables`):** Add `auth.roles` and `auth.role_permissions`
  tables; seed system roles and their permission rows; add `role_id` nullable FK
  to `auth.users`; backfill `role_id` from existing `role` string; set `role_id`
  NOT NULL; drop `chk_user_role` CHECK constraint; drop `role` column.
- All steps run in a single transaction with a rollback-safe backfill.

**Rationale:** Atomic migration avoids a window where both columns coexist in
an inconsistent state. Phase 1 has a single organisation so backfill is fast.

**Alternatives considered:**
- Two separate migrations (add column, then drop old) — safer for zero-downtime
  deployments on large tables; deferred to Phase 2 if table grows significantly.

---

### 2. Permission enforcement: dependency factory pattern

**Decision:** `backend/app/core/permissions.py` exposes:

```python
def require_permission(resource: str, action: str) -> Callable:
    async def _guard(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> User:
        if current_user.role_name == "super_admin":   # resolved from JWT claim
            return current_user
        allowed = await PermissionCache.check(current_user.role_id, resource, action, session)
        if not allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current_user
    return Depends(_guard)
```

`action="write"` checks `can_write OR can_write` (write implies read per spec).
`action="read"` checks `can_read OR can_write`.

Team scoping: a second dependency `get_scoped_team_ids(resource)` replaces
`get_managed_team_ids`. It reads `team_scoped` from the cached permission row
and returns managed team IDs if true, else `[]` (no filter).

**Rationale:** Factory pattern keeps router signatures clean; aligns with
existing `Depends()` pattern already used in all routers.

**Alternatives considered:**
- Middleware (before route dispatch) — harder to inject per-resource context;
  rejected.
- Permission decorator — Python decorators don't compose cleanly with async
  FastAPI; rejected.

---

### 3. In-process TTL cache

**Decision:** Use a simple dict-based TTL cache in `PermissionCache` class
(singleton per worker process), keyed by `role_id` (UUID), storing the full
permission map for that role with an expiry timestamp. TTL = 60 seconds.
Cache is invalidated (key deleted) when `PUT /roles/{role_id}/permissions`
is called in the same process.

```python
class PermissionCache:
    _store: dict[uuid.UUID, tuple[dict, float]] = {}  # role_id → (perms, expiry)
    TTL = 60.0

    @classmethod
    async def check(cls, role_id, resource, action, session) -> bool:
        now = time.monotonic()
        if role_id in cls._store:
            perms, expiry = cls._store[role_id]
            if now < expiry:
                return cls._evaluate(perms.get(resource), action)
        perms = await cls._load(role_id, session)
        cls._store[role_id] = (perms, now + cls.TTL)
        return cls._evaluate(perms.get(resource), action)

    @classmethod
    def invalidate(cls, role_id: uuid.UUID) -> None:
        cls._store.pop(role_id, None)
```

**Rationale:** No new infrastructure (Redis) required for Phase 1. Permission
changes take effect within 60 s across all requests in the same process;
acceptable for an admin-only settings change.

**Alternatives considered:**
- Redis cache — consistent across processes; adds operational dependency; deferred.
- `functools.lru_cache` — no TTL support without a wrapper; custom class simpler.

---

### 4. Router guard replacement map

All existing guards in `backend/app/core/rbac.py` are replaced as follows:

| Old guard | New guard | Resource | Action |
|---|---|---|---|
| `require_team_admin_or_above` on insights | `require_permission("insights", "read")` | insights | read |
| `require_team_admin_or_above` on alerts | `require_permission("alerts", "read/write")` | alerts | read or write |
| `require_team_admin_or_above` on uploads | `require_permission("uploads", "read/write")` | uploads | read or write |
| `require_team_admin_or_above` on users | `require_permission("members", "read/write")` | members | read or write |
| `require_team_admin_or_above` on collectors | `require_permission("collectors", "read/write")` | collectors | read or write |
| `require_finance_viewer_access` on reports | `require_permission("reports", "read")` | reports | read |
| `require_super_admin` on report writes | `require_permission("reports", "write")` | reports | write |
| `require_auditor_access` on audit-logs | `require_permission("audit_logs", "read")` | audit_logs | read |
| `require_super_admin` on tools writes | `require_permission("tools", "write")` | tools | write |
| `require_super_admin` on teams writes | `require_permission("teams", "write")` | teams | write |
| `require_super_admin` on credentials | `require_permission("credentials", "read/write")` | credentials | read or write |
| bare `get_current_user` on my_usage | `require_permission("my_usage", "read")` | my_usage | read |

`get_managed_team_ids` is replaced by `get_scoped_team_ids(resource)` which
reads the `team_scoped` flag from the cached permission row.

---

### 5. Frontend permission resolution

**Decision:** On login, `GET /auth/me` returns the user's `role_id` and
`role_name`. A second call `GET /api/v1/roles/{role_id}/permissions` fetches
the full permission map and stores it in the Zustand auth store. Sidebar items
and `RoleGuard` read from this store rather than comparing `user.platformRole`
to hardcoded role strings.

**Rationale:** Avoids per-navigation API calls; one fetch on login populates
all guards. TTL on client = session lifetime (re-fetched on token refresh).

**Alternatives considered:**
- Embed permission map in JWT — JWT size grows; permissions can change mid-session;
  rejected.
- Check permissions via API on each route change — too slow; rejected.

---

## Module Structure

```
backend/
  alembic/
    versions/016_roles_add_tables.py
  app/
    core/
      permissions.py        # require_permission factory + PermissionCache
    roles/
      router.py             # GET/POST/PATCH/DELETE /roles, GET/PUT /roles/{id}/permissions
      service.py            # RoleService
      schemas.py            # RoleResponse, PermissionMatrixItem, etc.
      repository.py         # RoleRepository, RolePermissionRepository
    models/
      roles.py              # Role + RolePermission SQLAlchemy models
    # rbac.py retained for backward compat during transition; guards deprecated

frontend/
  src/
    pages/
      settings/
        RolesPage.tsx       # matrix table
    components/
      auth/
        RoleGuard.tsx       # updated to use permission store
      layout/
        Sidebar.tsx         # updated to use permission store
    store/
      authStore.ts          # extended with permissionMap: Record<resource, {can_read, can_write}>
    api/
      roles.ts              # fetchRoles, fetchRolePermissions, updateRolePermissions
```

---

## Migration Plan

1. Write Alembic revision `016_roles_add_tables`.
2. Run migration in dev: `docker compose exec api alembic upgrade head`.
3. Verify all 5 system roles seeded and all users backfilled.
4. Implement `permissions.py` and `roles/` module.
5. Replace guards in all routers (mechanical find-replace using table in Decision 4).
6. Update `GET /auth/me` to return `role_id` and `role_name`.
7. Update frontend auth store and `RoleGuard`.
8. Build Settings > Roles page.
9. Update `openapi.yaml` with new `/roles` paths.

**Rollback:** Revert Alembic migration restores `role` column and drops new tables.
Since `role_id` backfill is derived from `role`, no data is lost on rollback.

---

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Cache staleness across multiple API worker processes | 60 s TTL acceptable for admin-only settings change; Redis cache in Phase 2 if needed |
| Migration backfill fails for users with an unknown role string | Migration aborts on unmapped role; manual fix before re-run |
| Frontend permission map stale after admin changes another user's role mid-session | User must re-login or token refresh triggers re-fetch; acceptable for Phase 1 |
| System role name immutability complicates i18n | Display name can be overridden in UI without changing DB value; deferred |
| Replacing all router guards in one PR risks regression | Each router file tested independently; verification plan includes per-resource curl tests |

## Open Questions

- **ADR-005 supersession:** New ADR-020 recorded to capture dynamic permissions
  decision. ADR-005 is not modified (immutable).
- **`/auth/me` backward compatibility:** The `role` string field in the JWT
  response stays for Phase 1 to avoid breaking any clients reading it; deprecated
  in Phase 2.
