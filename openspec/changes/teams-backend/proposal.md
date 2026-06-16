# Proposal: Teams Backend

**Status:** ✅ Completed (2026-06-16)

## Why

The admin **Teams** page (`/admin/teams`) and downstream features (members, credentials, uploads, alerts) depend on team entities. [frontend-mapping.md](../../specifications/apis/frontend-mapping.md) lists four `teams.ts` functions — all **mock**. Auth is wired; teams are the next admin primitive per FR-ADM-002 and OpenAPI `/teams`.

## What Changes (this slice)

- Alembic migration `004_admin_teams`: `admin.teams` per [database.md](../../specifications/database.md).
- OpenAPI-aligned endpoints:
  - `GET /api/v1/teams` → `TeamListResponse`
  - `POST /api/v1/teams` → `Team` (201)
  - `GET /api/v1/teams/{teamId}` → `Team`
  - `PATCH /api/v1/teams/{teamId}` → `Team`
  - `DELETE /api/v1/teams/{teamId}` → 204 *(frontend contract; deactivates or removes empty team)*
- JWT protection; writes restricted to `super_admin`.
- Wire `frontend/src/api/teams.ts` with snake_case ↔ camelCase adapter.
- FE-only fields (`tokenBudget`, `toolIds`, usage totals) return safe defaults until tools/usage slices land.

## Out of Scope (later slices)

- `admin.team_memberships` and `/teams/{id}/members`
- Team tool assignment persistence
- Budget fields and usage rollups on team rows
- Team Admin scoped write access
- `team_ids` on `/auth/me`

## Dependencies

- [authentication-backend](../authentication-backend/proposal.md) — JWT + dev org seed
