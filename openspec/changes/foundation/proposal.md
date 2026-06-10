# Proposal: Foundation

## Why

All product changes (authentication, user management, collector, dashboards, reporting, notifications) depend on a shared **foundation layer**: Docker Compose dev stack, FastAPI skeleton with bounded contexts, Celery workers, Alembic migrations, CI pipeline, and React SPA scaffold (TASK-INF-001 – TASK-INF-006).

TASK-INF-001 is **partially implemented** (compose + minimal backend). INF-002 through INF-006 are **not implemented**. Without completing foundation, downstream OpenSpec changes cannot be applied reliably.

This change delivers the **complete Phase 1 foundation** — unblocking every backend and frontend feature change.

## What Changes

### TASK-INF-001 (complete)
- Verify and harden existing `docker-compose.yml` (postgres, redis, api, worker, beat, volumes, healthchecks)
- Add optional `migrate` one-shot service for Alembic
- Live `docker compose up --build` verification documented

### TASK-INF-002 (new)
- Restructure `backend/app/` into bounded contexts: `auth`, `admin`, `ingestion`, `usage`, `dashboard`, `reporting`, `notifications`, `audit`, `core`, `db`, `api/v1`
- Mount all routes under `/api/v1` prefix; move health to `GET /api/v1/health`
- Pydantic `Settings` for DATABASE_URL, REDIS_URL, JWT placeholders, storage, Celery
- Problem Details exception handler stub (TASK-PLT-005 alignment)

### TASK-INF-003 (new)
- Celery queue routing: `ingestion`, `reports`, `alerts`, `email`, `maintenance` per ADR-004
- Task base class with `correlation_id`, `organization_id`
- Beat schedule placeholder; sample routed task from API

### TASK-INF-004 (new)
- Alembic async setup, multi-schema support
- Initial revision `001_initial_schemas` (empty schemas per database.md)
- Migration on deploy via compose `migrate` service or API entrypoint

### TASK-INF-005 (new)
- GitHub Actions: ruff, mypy, pytest, OpenAPI Redocly lint, bandit/pip-audit
- Postgres + Redis service containers in CI

### TASK-INF-006 (new)
- React + TypeScript + Vite + MUI frontend scaffold
- React Router, TanStack Query, auth context shell, API client (`/api/v1`, JWT + correlation ID headers)
- i18n en-US structure; placeholder routes (login, dashboard, admin)

## Capabilities

| Capability | Task | Description |
|------------|------|-------------|
| `docker-compose-dev-stack` | INF-001 | Compose stack, volumes, healthchecks, local dev docs |
| `fastapi-application-skeleton` | INF-002 | Bounded contexts, `/api/v1`, settings, health |
| `celery-worker-setup` | INF-003 | Queues, Beat, task base, worker/API shared config |
| `alembic-migrations` | INF-004 | Alembic async, initial schemas, migrate job |
| `github-actions-ci` | INF-005 | PR pipeline lint/test/security/OpenAPI |
| `react-spa-scaffold` | INF-006 | Frontend app shell, API client, i18n, routes |

### Modified Capabilities

None.

## Impact

| Area | Impact |
|------|--------|
| **Backend** | Major restructure from flat scaffold to bounded contexts |
| **Frontend** | New `frontend/` directory |
| **CI** | New `.github/workflows/` |
| **Docker** | Optional `migrate` service; frontend service stub in compose (dev profile) |
| **Tests** | Extend `tests/infra/`; add CI test job |
| **Downstream** | **Prerequisite** for all OpenSpec changes: authentication-backend, user-management-backend, usage-collector-backend, dashboard-backend, reporting-backend, notifications-backend |

## Dependency graph

```text
foundation (this change)
  → authentication-backend
  → user-management-backend
  → usage-collector-backend (+ file ingest)
  → dashboard-backend / notifications-backend / reporting-backend
```

## Open Questions

1. **Overlap with authentication-backend INF-002 bundle:** Foundation delivers skeleton only; auth change adds auth routes/models. **Apply foundation first.**
2. **Frontend in Compose:** Dev profile adds `frontend` Vite service on port 5173. **Assumption:** yes for local dev.
3. **Python version in CI:** Match Dockerfile (3.12 Linux). **Assumption:** 3.12 in CI matrix.
