# Proposal: Authentication Backend

## Why

The AI Tool Usage Tracker cannot deliver any product feature until users can authenticate securely. FR-PLT-001 and NFR-SEC-003 require JWT-based login, token lifecycle management, and a `/auth/me` profile endpoint before administration, ingestion, dashboards, or reporting can be built. The foundation scaffold (TASK-INF-001) exists but has no database schema, no user model, and no auth routes.

This change delivers the **authentication backend slice** — auth database schema, JWT issuance/validation, and OpenAPI-aligned `/auth/*` endpoints — unblocking TASK-PLT-002 (RBAC middleware) and all downstream modules.

## What Changes

- Add Alembic migration for `auth` schema: `organizations`, `users`, `refresh_tokens` per [database.md](../../specifications/database.md).
- Implement `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, and `GET /api/v1/auth/me` per [openapi.yaml](../../specifications/apis/openapi.yaml).
- Add password hashing (Argon2id), JWT access/refresh token issuance, and refresh token rotation with hashed storage.
- Add JWT validation dependency for protected routes (middleware foundation; full RBAC policy matrix deferred to TASK-PLT-002).
- Add login rate limiting (Redis-backed) per NFR-SEC-003.
- Add SQLAlchemy models, repositories, and integration tests for auth flows.
- Add dev-only seed script for default organization and Super Admin user.

**Prerequisite:** Apply the [`foundation`](../foundation/proposal.md) change first — it delivers bounded contexts, `/api/v1` router prefix, Alembic framework, and `GET /api/v1/health`. This change adds auth routes and `002_auth` migration only (no duplicate INF-002 skeleton work).

**BREAKING:** Health endpoint is at `GET /api/v1/health` after foundation (not root `/health`).

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `auth-schema` | PostgreSQL `auth` schema migrations, models, and repositories for organizations, users, and refresh tokens |
| `jwt-authentication` | Login, refresh, current-user profile, JWT validation dependency, rate limiting |

### Modified Capabilities

None — functional requirements (FR-PLT-001, NFR-SEC-003) already exist in `openspec/requirements/`. This change implements them; no requirement text changes.

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/auth/` package; Alembic migrations; config extensions for JWT TTL and secrets |
| **Database** | New `auth` schema tables; dev seed data |
| **API** | Three new auth endpoints; Bearer security scheme enforced on future routes |
| **Redis** | Login rate-limit counters; optional token blocklist hook (future) |
| **Dependencies** | `python-jose` or `PyJWT`, `argon2-cffi`, Alembic, SQLAlchemy async |
| **Tests** | Unit tests (token service, password hashing); integration tests (login, refresh, expired token, rate limit) |
| **Documentation** | Update README auth section; align `.env.example` with JWT variables |
| **Downstream** | Unblocks TASK-PLT-002 (RBAC), TASK-UI-001 (login UI), all protected APIs including [usage-collector-backend](../usage-collector-backend/proposal.md) connect API |

## Usage collector dependency (FR-ING-004)

JWT authentication and RBAC from this change are **prerequisites** for the provider-managed connect API (`POST /api/v1/collectors`) where administrators submit vendor API tokens. Tokens are stored via FR-ADM-003 credentials — not in auth module — but every collector endpoint requires Bearer JWT validation implemented here.

## Open Questions

1. **Prerequisite tasks:** INF-002 (FastAPI skeleton) and INF-004 (Alembic) are not complete. This change includes minimal scaffolding for both as prerequisites — confirm whether to split into a separate change or bundle here. **Assumption:** bundle minimal INF-002/INF-004 scope needed for auth only.
2. **Organization resolution at login:** Single-tenant dev seed vs email+org slug at login for multi-tenant readiness. **Assumption:** email unique per organization; dev seed creates one org; login accepts email+password only (org inferred from user record).
3. **Refresh token delivery:** OpenAPI includes optional `refresh_token` in TokenResponse. **Assumption:** always issue refresh token in Phase 1 with rotation on `/auth/refresh`.
4. **RBAC scope:** Full role permission matrix (TASK-PLT-002) is out of scope for this change; only JWT presence/validity and `/auth/me` role exposure are in scope.
