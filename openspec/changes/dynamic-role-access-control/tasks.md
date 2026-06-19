# Tasks: Dynamic Role Access Control

Implementation checklist for change `dynamic-role-access-control`.
Reference [design.md](./design.md), [specs](./specs/), and [verification.md](./verification.md).

---

## 1. Database Migration

- [x] 1.1 Create `backend/app/models/roles.py` with `Role` and `RolePermission` SQLAlchemy models in `auth` schema — UUID PKs, `is_system` bool, `team_scoped` bool, unique constraint on `(role_id, resource)`
- [x] 1.2 Write Alembic revision `027_roles_add_tables`: create `auth.roles` and `auth.role_permissions` tables
- [x] 1.3 In same revision: seed 5 system roles (`super_admin`, `team_admin`, `finance_viewer`, `auditor`, `team_member`) with `is_system = true`
- [x] 1.4 In same revision: seed `auth.role_permissions` rows for each system role matching current RBAC matrix (use design.md guard replacement table as source of truth)
- [x] 1.5 In same revision: add nullable `role_id` UUID FK column to `auth.users` referencing `auth.roles.id`
- [x] 1.6 In same revision: backfill `auth.users.role_id` by joining on role name string; abort migration if any unmatched rows exist
- [x] 1.7 In separate revision `028_roles_drop_legacy_column`: set `role_id` NOT NULL; drop `chk_user_role` CHECK constraint; drop `role` VARCHAR column
- [x] 1.8 Run migration in dev: `docker compose exec api alembic upgrade head`
- [x] 1.9 Verify: `SELECT COUNT(*) FROM auth.roles WHERE is_system=true` returns 5; `SELECT COUNT(*) FROM auth.users WHERE role_id IS NULL` returns 0

---

## 2. Permission Enforcement Layer

- [x] 2.1 Create `backend/app/core/permissions.py` with `PermissionCache` class: dict-based TTL store (60 s), `check(role_id, resource, action, session)` async method, `invalidate(role_id)` classmethod
- [x] 2.2 Implement `require_permission(resource, action)` factory returning a FastAPI `Depends`-compatible async guard; super_admin bypasses DB lookup
- [x] 2.3 Implement `get_scoped_team_ids_for(resource)` dependency replacing `get_managed_team_ids`; reads `team_scoped` from cached permission row; returns managed team IDs if true, else `[]`
- [x] 2.4 Define `VALID_RESOURCES` set of exactly 12 keys: `insights`, `alerts`, `uploads`, `members`, `reports`, `audit_logs`, `tools`, `teams`, `credentials`, `collectors`, `settings`, `my_usage`
- [x] 2.5 Write unit tests for `PermissionCache`: cache hit on second call, invalidation, write-implies-read, missing-row-denied
- [x] 2.6 Update `backend/app/models/auth.py`: replace `role: Mapped[str]` with `role_id: Mapped[uuid.UUID]` FK; add `role_name` property for backward compat in JWT claims

---

## 3. Replace Router Guards

- [x] 3.1 Update `backend/app/dashboard/router.py`: replace all dashboard analytics guards with `require_permission("insights", "read")`; replace `get_managed_team_ids` with `get_scoped_team_ids("insights")`
- [x] 3.2 Update `backend/app/thresholds/router.py`: GET endpoints → `require_permission("alerts", "read")`; write endpoints → `require_permission("alerts", "write")`; scoped list uses `get_scoped_team_ids("alerts")`
- [x] 3.3 Update `backend/app/uploads/router.py`: read → `require_permission("uploads", "read")`; write → `require_permission("uploads", "write")`; scoped list uses `get_scoped_team_ids("uploads")`
- [x] 3.4 Update `backend/app/users/router.py` and `members/router.py`: read → `require_permission("members", "read")`; write → `require_permission("members", "write")`; scoped list uses `get_scoped_team_ids("members")`
- [x] 3.5 Update `backend/app/reports/router.py`: read → `require_permission("reports", "read")`; write → `require_permission("reports", "write")`
- [x] 3.6 Update `backend/app/audit/router.py`: `require_permission("audit_logs", "read")`
- [x] 3.7 Update `backend/app/tools/router.py`: reads → `require_permission("tools", "read")`; writes → `require_permission("tools", "write")`
- [x] 3.8 Update `backend/app/teams/router.py`: reads → `require_permission("teams", "read")`; writes → `require_permission("teams", "write")`
- [x] 3.9 Update `backend/app/credentials/router.py`: `require_permission("credentials", "read/write")`
- [x] 3.10 Update `backend/app/collector/router.py`: reads → `require_permission("collectors", "read")`; writes → `require_permission("collectors", "write")`
- [x] 3.11 Update `backend/app/usage/router.py` and `backend/app/dashboard/router.py` my-usage endpoint: `require_permission("my_usage", "read")`
- [x] 3.12 Mark `backend/app/core/rbac.py` guards as deprecated with docstring; do not delete until Phase 2

---

## 4. Role Management API

- [x] 4.1 Create `backend/app/roles/` package: `router.py`, `service.py`, `schemas.py`, `repository.py`
- [x] 4.2 Implement `RoleRepository`: `list_by_org`, `get_by_id`, `create`, `update`, `delete`, `get_permissions`, `replace_permissions`
- [x] 4.3 Implement `RoleService` with business rules: system role delete guard, active-user delete guard, duplicate name guard, system role name immutability
- [x] 4.4 Implement `GET /api/v1/roles` — super_admin only; returns all roles for org
- [x] 4.5 Implement `POST /api/v1/roles` — super_admin only; creates custom role with empty permission matrix (12 rows all false)
- [x] 4.6 Implement `PATCH /api/v1/roles/{role_id}` — super_admin only; name/description update with system name guard
- [x] 4.7 Implement `DELETE /api/v1/roles/{role_id}` — super_admin only; system and active-user guards
- [x] 4.8 Implement `GET /api/v1/roles/{role_id}/permissions` — super_admin or own role; returns exactly 12 rows including defaults for missing rows
- [x] 4.9 Implement `PUT /api/v1/roles/{role_id}/permissions` — super_admin only; atomic replace; validate resource keys against `VALID_RESOURCES`; call `PermissionCache.invalidate(role_id)` after write
- [x] 4.10 Register `roles` router in `backend/app/main.py` or `api/v1/router.py`
- [x] 4.11 Update `PATCH /api/v1/users/{user_id}` to accept `role_id` UUID instead of `role` string
- [x] 4.12 Update `GET /auth/me` response to include `role_name` (string from joined Role) alongside `role_id`

---

## 5. OpenAPI Spec Update

- [x] 5.1 Add `RoleResponse`, `RoleListResponse`, `PermissionMatrixItem`, `CreateRoleRequest`, `UpdateRoleRequest` schemas to `openspec/specifications/apis/components/schemas.yaml`
- [x] 5.2 Add `/roles`, `/roles/{role_id}`, `/roles/{role_id}/permissions` paths to `openspec/specifications/apis/openapi.yaml`
- [ ] 5.3 Update security descriptions on all existing endpoints to reference dynamic permission system rather than role names
- [ ] 5.4 Validate YAML: `python -c "import yaml; yaml.safe_load(open('openspec/specifications/apis/openapi.yaml')); print('OK')"`

---

## 6. Frontend — Settings > Roles Page

- [x] 6.1 Create `frontend/src/api/roles.ts`: `fetchRoles()`, `fetchRolePermissions(roleId)`, `updateRolePermissions(roleId, matrix)`, `createRole(name, description)`, `deleteRole(roleId)`, `patchRole(roleId, updates)`
- [x] 6.2 Create `frontend/src/pages/settings/RolesPage.tsx`: matrix table (12 resource rows × N role columns), read/write toggle cells, lock icon on system role headers, loading and error states
- [x] 6.3 Implement auto-save on toggle: debounce 300 ms then call `updateRolePermissions`; show saving spinner; revert on error
- [x] 6.4 Implement "+ New Role" button: modal with name + description fields; validation (non-empty name); calls `createRole`; appends column to matrix on success
- [x] 6.5 Add `/settings/roles` route in `frontend/src/App.tsx` wrapped in `RoleGuard` for super_admin only
- [x] 6.6 Add "Roles" nav item to Settings section in `frontend/src/components/layout/Sidebar.tsx` (visible to super_admin only)

---

## 7. Frontend — Auth Store + Permission-Based Guards

- [x] 7.1 Extend `frontend/src/store/authStore.ts`: add `permissionMap: Record<string, {can_read: boolean, can_write: boolean, team_scoped: boolean}>` field
- [x] 7.2 On login success and token refresh: call `GET /api/v1/roles/{role_id}/permissions` and populate `permissionMap` in auth store
- [x] 7.3 Update `frontend/src/components/auth/RoleGuard.tsx`: accept `resource` prop as alternative to `roles` prop; check `permissionMap[resource]?.can_read` from auth store
- [x] 7.4 Update all `RoleGuard` usages in `App.tsx` to use `resource` prop instead of `roles` array
- [x] 7.5 Update `frontend/src/components/layout/Sidebar.tsx`: replace `roles: [Role.X]` nav item config with `resource: "resource_key"`; hide item when `permissionMap[resource]?.can_read` is false
- [x] 7.6 Update user edit form in members/users pages: replace role string dropdown with role ID dropdown populated from `fetchRoles()`

---

## 8. Verification & Evidence

- [ ] 8.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 8.2 Collect functional evidence (screenshot / test output / SQL result) for each scenario — one entry per row in verification.md § Evidence Log
- [ ] 8.3 Confirm every Hallucination Risk mitigation step in verification.md § Hallucination Risk Register
- [ ] 8.4 Confirm all ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 8.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer required)
- [ ] 8.6 Run `openspec validate dynamic-role-access-control --type change --strict` before archive
