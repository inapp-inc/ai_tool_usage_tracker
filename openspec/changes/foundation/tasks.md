# Tasks: Foundation

Reference [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md). Maps to TASK-INF-001 – TASK-INF-006 in [01-foundation.md](../../tasks/01-foundation.md).

**Prerequisite for:** all downstream OpenSpec changes.

---

## 1. Complete Docker Compose stack (INF-001)

- [ ] 1.1 Verify live `docker compose up --build`; document result in verification Evidence Log *(blocked: Docker Desktop offline on dev machine; `docker compose config` validated)*
- [x] 1.2 Add `migrate` one-shot service running `alembic upgrade head`
- [x] 1.3 Update API healthcheck URL to `http://127.0.0.1:8000/api/v1/health`
- [x] 1.4 Add optional `frontend` service under Compose profile `dev` (port 5173)
- [x] 1.5 Extend `tests/infra/test_compose_config.py` for migrate service and healthcheck path

## 2. FastAPI skeleton (INF-002)

- [x] 2.1 Create bounded context packages: auth, admin, ingestion, usage, dashboard, reporting, notifications, audit, core, db
- [x] 2.2 Add `backend/app/api/v1/router.py` and mount at `/api/v1` in `main.py`
- [x] 2.3 Move health handler to `GET /api/v1/health` matching OpenAPI `HealthResponse`
- [x] 2.4 Extend `config.py` Settings with JWT placeholders, storage, ENVIRONMENT
- [x] 2.5 Add `core/exceptions.py` Problem Details stub handler
- [x] 2.6 Add `tests/infra/test_project_structure.py` for package layout
- [x] 2.7 Add `tests/integration/test_health.py` and `tests/unit/test_config.py`

## 3. Database layer (INF-002 + INF-004 prep)

- [x] 3.1 Add `db/session.py` async session factory and FastAPI dependency
- [x] 3.2 Add `db/base.py` declarative base for future models
- [x] 3.3 Add sync session helper for Celery worker tasks

## 4. Alembic migrations (INF-004)

- [x] 4.1 Initialize Alembic under `backend/alembic/` with async env
- [x] 4.2 Create revision `001_initial_schemas` creating auth, admin, ingestion, usage, notifications, reporting, audit schemas
- [x] 4.3 Add downgrade for initial revision
- [x] 4.4 Wire `migrate` compose service and document in README
- [x] 4.5 Add `tests/integration/test_migrations.py`

## 5. Celery setup (INF-003)

- [x] 5.1 Configure queue routes per ADR-004 in `celery_app.py`
- [x] 5.2 Update worker command to consume all five queues
- [x] 5.3 Implement `BaseTask` with correlation_id and organization_id logging
- [x] 5.4 Add Beat placeholder schedule in `celery_app.py`
- [x] 5.5 Add sample `ping_queue` task for integration testing
- [x] 5.6 Add `tests/integration/test_celery_queues.py`

## 6. CI pipeline (INF-005)

- [x] 6.1 Create `.github/workflows/ci.yml` with backend-lint, backend-test, openapi-lint, security, frontend jobs
- [x] 6.2 Configure Postgres and Redis GitHub service containers for pytest
- [x] 6.3 Add ruff, mypy, bandit, pip-audit to backend dev dependencies or CI install step
- [x] 6.4 Verify Redocly lint on `openspec/specifications/apis/openapi.yaml`

## 7. React SPA scaffold (INF-006)

- [x] 7.1 Scaffold `frontend/` with Vite, React 18, TypeScript, MUI
- [x] 7.2 Add React Router with placeholder routes: login, dashboard, admin
- [x] 7.3 Add TanStack Query provider and AuthContext shell
- [x] 7.4 Implement API client with `/api/v1` base, JWT and X-Correlation-ID headers
- [x] 7.5 Add en-US i18n resource structure (NFR-LOC-001)
- [x] 7.6 Add frontend unit tests for client headers and placeholder routes
- [x] 7.7 Document frontend dev commands in README

## 8. Documentation and alignment

- [x] 8.1 Update README: health URL, migrate job, frontend dev, apply order
- [x] 8.2 Update `openspec/tasks/01-foundation.md` implementation status after apply
- [x] 8.3 Note in `authentication-backend` proposal that foundation supersedes its INF-002 bundle (if not already)

## 9. Verification & Evidence

- [ ] 9.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment
- [ ] 9.2 Collect functional evidence — populate verification.md § Evidence Log
- [ ] 9.3 Confirm Hallucination Risk mitigations in verification.md § Hallucination Risk Register
- [ ] 9.4 Confirm ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 9.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer)
- [x] 9.6 Run `openspec validate foundation --type change --strict` before archive
