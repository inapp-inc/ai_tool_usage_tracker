# Proposal: User Management Backend

## Why

After authentication (change `authentication-backend`), Super Admins must provision platform users, assign RBAC roles, and organize users into teams before usage tracking, ingestion, or dashboards can operate. FR-ADM-002 requires team CRUD and multi-team membership. E2E-001 (Super Admin setup) depends on creating teams and assigning members.

The OpenAPI contract defines team endpoints (`/teams/*`) but has **no user administration endpoints** — users can only be created via dev seed today. This change delivers the **user management backend**: admin schema migrations, platform user CRUD, team management API, and RBAC enforcement for administration routes.

## What Changes

- Add Alembic migration `003_admin_teams`: `admin.teams`, `admin.team_memberships` per [database.md](../../specifications/database.md).
- Implement OpenAPI team endpoints: `GET/POST /teams`, `GET/PATCH /teams/{teamId}`, `GET/POST /teams/{teamId}/members`, `DELETE /teams/{teamId}/members/{userId}`.
- Add **new** platform user endpoints (OpenAPI extension): `GET/POST /users`, `GET/PATCH /users/{userId}` for Super Admin user lifecycle.
- Extend `GET /auth/me` to populate `team_ids` from active memberships (depends on `authentication-backend`).
- Implement RBAC policies for user and team routes (minimal TASK-PLT-002 scope for administration tag).
- Record audit events on user create/update/deactivate and team/member mutations (minimal TASK-PLT-003 hooks or stub ready for full audit service).
- Add repositories, services, integration tests, and OpenAPI schema additions for user endpoints.

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `admin-schema-teams` | PostgreSQL `admin.teams` and `admin.team_memberships` migrations, models, repositories |
| `platform-user-admin` | Super Admin API to list, create, update, and deactivate organization users |
| `team-management` | Team CRUD and member assignment per FR-ADM-002 and OpenAPI `/teams/*` |

### Modified Capabilities

None — FR-ADM-002 and FR-PLT-001 requirements exist in `openspec/requirements/`. OpenAPI gains new `/users/*` paths (implementation extends contract; delta captured in `platform-user-admin` spec).

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/admin/` package (users + teams submodules) |
| **Database** | `admin` schema tables; soft-remove memberships via `removed_at` |
| **API** | 8 team endpoints + 4 new user endpoints under `/api/v1` |
| **OpenAPI** | Add `Users` tag and schemas: `User`, `UserCreateRequest`, `UserUpdateRequest`, `UserListResponse` |
| **Auth** | `/auth/me` returns populated `team_ids`; user routes require Super Admin |
| **Dependencies** | Requires `authentication-backend` (auth schema, JWT, `auth.users`) |
| **Tests** | Integration tests for user CRUD, team CRUD, membership, RBAC 403, deactivated team |
| **Downstream** | Unblocks E2E-001, TASK-ADM-001 (tools), ingestion team attribution, dashboard scoping, [usage-collector-backend](../usage-collector-backend/proposal.md) team-scoped collectors |

## Usage collector dependency (FR-ING-004)

Team membership from this change determines **Team Admin scope** for collector configuration (`team_id` on `ingestion.collector_configs`). Collectors assigned to team T require TA membership on T per ADR-015 — same rule as team member management.

## Open Questions

1. **Prerequisite:** `authentication-backend` must be applied first (or concurrently). **Assumption:** this change depends on auth schema and JWT middleware.
2. **Team Admin scope:** No `is_admin` flag on `team_memberships`. **Assumption:** users with platform role `team_admin` may manage members only for teams where they hold an active membership; `super_admin` manages all teams.
3. **Password on user create:** **Assumption:** Super Admin sets initial password on create; optional `send_invite` deferred to Phase 2.
4. **Audit service:** Full TASK-PLT-003 may not exist. **Assumption:** emit audit events via repository hook or thin `AuditService` interface stub that logs until PLT-003 completes.
5. **User delete:** **Assumption:** deactivate via `active: false` only — no hard delete (preserves historical usage FK integrity).
