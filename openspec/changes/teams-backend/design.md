# Design: Teams Backend

**Status:** ✅ Completed (2026-06-16)

## Data model

`admin.teams` (see database.md):

| Column | Notes |
|--------|-------|
| `id` | UUID PK |
| `organization_id` | FK → `auth.organizations` |
| `name` | Unique per org, max 100 |
| `description` | Optional, max 500 |
| `active` | Default `true`; PATCH `active: false` deactivates |
| `created_at`, `updated_at` | Timestamps |

`member_count` is computed (0 until memberships slice).

## API contract

Aligned with `components/schemas.yaml` (`Team`, `TeamCreateRequest`, `TeamUpdateRequest`, `TeamListResponse`).

### Frontend adapter mapping

| OpenAPI (snake_case) | Frontend (camelCase) |
|----------------------|----------------------|
| `member_count` | `memberCount` |
| `created_at` | `createdAt` |
| `active` | `status` (`active` / `inactive`) |
| — | `tokenBudget`, `costBudget`, `toolIds`, usage fields → defaults |

Create/update requests send only `name`, `description`, and `active` (via status on update when applicable).

## Authorization

| Operation | Roles |
|-----------|-------|
| List / get | Any authenticated user in org |
| Create / update / delete | `super_admin` |

## Errors

| Case | Status |
|------|--------|
| Duplicate name in org | 409 |
| Team not found | 404 |
| Non–super-admin write | 403 |

## Migration chain

`001_initial_schemas` → `002_auth` → `003_collector_usage` → **`004_admin_teams`**
