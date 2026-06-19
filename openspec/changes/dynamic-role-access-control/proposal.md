# Proposal: Dynamic Role Access Control

## Why

FR-PLT-001 currently mandates five hardcoded roles enforced by inline Python guards
in `backend/app/core/rbac.py`. Admins cannot create custom roles, adjust which pages
a role can access, or re-map permissions without a code change and redeploy. This
blocks tenant-specific access configurations and the settings-driven role management
that stakeholders require for the upcoming demo and beyond.

This change replaces the hardcoded role enum with a database-driven permission model
where a Super Admin can create roles, assign read/write access per resource, and link
users to roles through a Settings UI — all without touching code.

## What Changes

- **BREAKING:** `auth.users.role` VARCHAR enum column replaced by `auth.users.role_id`
  UUID FK pointing to new `auth.roles` table. Existing five roles seeded as system
  roles; all current users backfilled to matching system role rows.
- New `auth.roles` table: id, org_id, name, description, is_system, created_at.
- New `auth.role_permissions` table: id, role_id, resource, can_read, can_write,
  team_scoped — one row per role × resource combination.
- New `backend/app/core/permissions.py`: generic `require_permission(resource, action)`
  dependency factory replacing all role-specific guards in `rbac.py`.
- In-memory TTL permission cache (60 s) keyed by role_id; invalidated on any
  `role_permissions` write.
- New API module `backend/app/roles/` exposing CRUD endpoints for roles and their
  permission matrices.
- New frontend Settings > Roles page: matrix table (resources × roles) with
  read/write toggles and a "+ New Role" action.
- User edit form extended with role assignment dropdown populated from `GET /roles`.
- `openspec/specifications/apis/openapi.yaml` updated with new `/roles` paths and
  updated security descriptions for all guarded endpoints.

## Capabilities

### New Capabilities

| Capability | Spec file |
|---|---|
| `role-permission-schema` | Database schema for roles and permissions tables |
| `permission-enforcement` | Generic permission dependency factory and cache |
| `role-management-api` | REST API for role and permission CRUD |
| `role-settings-ui` | Frontend Settings > Roles matrix UI and user role assignment |

### Modified Capabilities

| Capability | Change |
|---|---|
| `jwt-authentication` (authentication-backend) | `/auth/me` response must return `role_name` from joined `roles` table instead of raw `role` string |
| `platform-user-admin` (user-management-backend) | User create/edit must accept `role_id` instead of `role` string |

## Impact

| Area | Impact |
|---|---|
| **Database** | Two new tables in `auth` schema; Alembic migration adds tables, backfills `role_id`, drops `role` column; CHECK constraint `chk_user_role` removed |
| **Backend** | `core/rbac.py` guards replaced with `core/permissions.py`; new `roles/` module; all routers updated |
| **JWT claims** | `role` claim in JWT stays as string for backward compat during transition; resolved from DB at `/auth/me` |
| **Frontend** | New Settings > Roles page; user edit form role dropdown; `RoleGuard` updated to use permission checks via API |
| **API contract** | New `/api/v1/roles` endpoints; existing guarded endpoints unchanged externally |
| **Cache** | In-process TTL cache — no new infrastructure required for Phase 1 |
| **Seed / dev scripts** | `seed_dev_roles.py` updated to use `role_id` references |
| **OpenAPI spec** | New paths, updated security descriptions |

## Open Questions

1. **JWT role claim:** Should the JWT carry `role_id` (UUID) or keep `role` as a string
   derived from the system role name? Keeping the string avoids breaking existing
   token validation but means the claim may lag if a user's role changes mid-session.
   **Assumption:** keep `role` string in JWT for Phase 1; permission checks always
   hit DB (with cache) on each request rather than trusting the JWT claim.

2. **Permission granularity:** The resource list covers 12 modules. Should `write`
   imply `read` (i.e., no user can write without read)? **Assumption:** yes — the
   enforcement layer treats `can_write=true` as implying `can_read=true`.

3. **System role permissions:** Can a Super Admin edit the permissions of a system
   role (e.g., give `finance_viewer` write access to uploads)? **Assumption:** yes —
   system roles are protected from deletion but their permission rows are editable,
   allowing full customisation.

4. **Multi-org:** `auth.roles` carries `org_id` for future multi-tenant isolation.
   Phase 1 has a single organisation; enforcement filters by `org_id` but no
   cross-org isolation logic is required in this change.

5. **ADR supersession:** This change supersedes ADR-005's hardcoded role policy
   mapping. A new ADR will be recorded capturing the dynamic permissions decision.
   ADR-005 itself is not modified (immutable per schema rules).
