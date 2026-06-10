# Verification Plan: Foundation

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### docker-compose-dev-stack

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Development stack services | All services start healthy | Given valid .env, when compose up, then all services healthy | Manual: `docker compose up --build` + `docker compose ps` | ☐ |
| Development stack services | Persistent volumes | Given compose file, when inspected, then named volumes for postgres/redis/storage/backups | `tests/infra/test_compose_config.py` | ☐ |
| Service hostname connectivity | API health reports dependencies | Given running stack, when health queried, then database and redis ok | `tests/integration/test_health.py::test_health_v1_connectivity` | ☐ |

### fastapi-application-skeleton

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Bounded context package structure | Package directories exist | Given backend app, when inspected, then all bounded context packages exist | `tests/infra/test_project_structure.py` | ☐ |
| API v1 prefix and health endpoint | Health under v1 prefix | Given running API, when GET /api/v1/health, then 200 with status fields | `tests/integration/test_health.py::test_health_v1_ok` | ☐ |
| Application settings | Required settings validated | Given missing DATABASE_URL, when app starts, then clear config error | `tests/unit/test_config.py::test_missing_database_url` | ☐ |

### celery-worker-setup

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Celery queue routing | Task routed to correct queue | Given ingestion task, when dispatched, then ingestion worker executes | `tests/integration/test_celery_queues.py::test_ingestion_queue_routing` | ☐ |
| Task context propagation | Failed task logs correlation id | Given failing task with correlation_id, when failure logged, then id present | `tests/integration/test_celery_queues.py::test_correlation_id_on_failure` | ☐ |
| Beat scheduler | Beat container starts | Given compose with beat, when stack up, then beat process running | Manual: `docker compose ps beat` | ☐ |

### alembic-migrations

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Alembic async framework | Migration upgrade on empty database | Given empty DB, when alembic upgrade head, then schemas created | `tests/integration/test_migrations.py::test_initial_schemas` | ☐ |
| Alembic async framework | Autogenerate against models | Given models registered, when autogenerate run, then revision produced | Manual dev verification | ☐ |
| Migration deploy hook | Migrate service completes | Given pending migrations, when compose run migrate, then DB at head | Manual: `docker compose run --rm migrate` | ☐ |

### github-actions-ci

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Pull request pipeline | CI runs lint and tests | Given PR, when CI triggers, then ruff/mypy/pytest pass | CI run URL in Evidence Log | ☐ |
| Pull request pipeline | OpenAPI lint in CI | Given CI run, when openapi job runs, then Redocly lint passes | CI run URL | ☐ |
| Security scanning in CI | Security scan job completes | Given PR, when security job runs, then bandit/pip-audit complete | CI run URL | ☐ |

### react-spa-scaffold

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Frontend application shell | Dev server starts | Given npm install, when npm run dev, then app on dev port | Manual or CI frontend job | ☐ |
| Frontend application shell | Production build succeeds | Given frontend, when npm run build, then assets produced | CI frontend job | ☐ |
| API client with auth headers | API client attaches headers | Given JWT in context, when request made, then Authorization and X-Correlation-ID sent | `frontend/src/api/client.test.ts` | ☐ |
| Internationalization structure | Login page uses i18n keys | Given login route en-US, when rendered, then strings from i18n | `frontend/src/routes/LoginPage.test.tsx` | ☐ |
| Placeholder routes | Router navigates to placeholders | Given router, when /login /dashboard /admin, then pages render | `frontend/src/App.test.tsx` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| Health still at `/health` | Forgot to update compose healthcheck | Assert healthcheck URL in compose test; integration test hits `/api/v1/health` only |
| Flat package structure | Only renamed folders without router wiring | Structure test lists all packages + `api/v1/router.py` |
| Celery default queue only | Worker not consuming named queues | Integration test dispatches to `ingestion` queue explicitly |
| Alembic sync engine in async app | Wrong engine type breaks upgrade | Migration integration test on fresh Postgres |
| CI without service containers | Tests pass locally fail in CI | CI workflow uses Postgres + Redis services |
| Frontend hardcoded strings | i18n keys skipped | LoginPage test asserts no raw English literals in component |
| Duplicate INF work in auth change | Auth change re-scaffolds skeleton | Code review: auth change adds routes only, not new layout |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-001 | Bounded contexts | `test_project_structure.py` passes |
| ADR-004 | Celery queue routing | `test_celery_queues.py` passes |
| ADR-006 | React + MUI frontend | Frontend builds; MUI in package.json |
| ADR-012 | OpenAPI health contract | Health response matches OpenAPI schema |
| ADR-013 | Compose + .env secrets | `.env.example` documented; no secrets in repo |

---

## 4. Evidence Requirements

### Functional

- [ ] All Spec Alignment scenarios — pytest output or manual compose verification per row
- [ ] Live `docker compose up --build` smoke documented in Evidence Log

### Structural

- [ ] Code review confirms bounded context directories per design.md
- [ ] Compose healthcheck uses `/api/v1/health`

### Edge Case

- [ ] Missing DATABASE_URL fails fast at startup
- [ ] Migrate job idempotent (second run succeeds with no pending revisions)

---

## 5. Evidence Log

| Scenario | Evidence Type | Location / Link | Collected By | Date |
|----------|---------------|-----------------|--------------|------|
| _TBD_ | _TBD_ | _TBD_ | | |

---

## 6. Audit Record

- [ ] All Spec Alignment rows pass with evidence
- [ ] Evidence Log complete
- [ ] Hallucination mitigations confirmed
- [ ] ADR compliance confirmed
- [ ] Scope excludes auth routes and product features

**Reviewer:** _______________  
**Date:** _______________
