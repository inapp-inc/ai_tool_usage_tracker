# Foundation Tasks

Infrastructure and project scaffolding.

---

## TASK-INF-001: Docker Compose Development Stack

### Description

Create `docker-compose.yml` with services: `postgres` (15-alpine + `postgres_data` volume), `redis`, FastAPI `api`, Celery `worker`, Celery `beat`. Wire healthchecks, env files, and internal network per [database.md](../specifications/database.md#docker-deployment).

### Dependencies

None

### Estimated Complexity

**M**

### Definition of Done

- [ ] `docker compose up` starts all services; Postgres passes `pg_isready` *(compose config validated 2026-06-10; live `docker compose up` pending Docker Desktop)*
- [x] API connects to Postgres and Redis via service hostnames
- [x] `.env.example` documents required variables without secrets
- [x] README documents local startup commands

**FR/NFR:** NFR-SEC-008, database Docker deployment

### Implementation Status

**Status:** Implemented (2026-06-10) — `migrate` service, `/api/v1/health` healthcheck, optional `frontend` dev profile added.

**Deliverables:**

| Artifact | Path |
|----------|------|
| Compose stack | `docker-compose.yml` |
| Migrate job | `docker-compose.yml` → `migrate` service |
| Backend scaffold | `backend/` |
| Environment template | `.env.example` |
| Local startup docs | `README.md` |
| Infra tests | `tests/infra/` |
| OpenSpec change | `openspec/changes/foundation/` |

### OpenSpec Alignment Review

| Category | Finding |
|----------|---------|
| **Missing requirements** | Live stack smoke test (`docker compose up`) where Docker Desktop was unavailable; Postgres CPU/RAM limits (NFR-SCL-001 — production); backup sidecar (TASK-OPS-003) |
| **Extra functionality** | FastAPI lifespan connectivity gate; Celery `ping` task; Redis AOF; Redis logical DB split (0/1/2); worker waits for healthy `api`; `POSTGRES_PASSWORD` required validation in Compose |
| **Architecture deviations** | None for INF-001 scope after foundation apply |
| **Security concerns** | Dev Redis without AUTH; ports published on all host interfaces by default; `.env.example` JWT placeholders documented as dev-only — acceptable for local Compose per NFR-SEC-008 |
| **Documentation gaps (resolved)** | Added `local-development.md`; updated `database.md`, `06-deployment-topology.md`, API `HealthResponse` enum, fixed broken `Source-code/project.md` links |

---

## TASK-INF-002: FastAPI Application Skeleton

### Description

Bootstrap FastAPI project with modular structure: `auth`, `admin`, `ingestion`, `usage`, `dashboard`, `reporting`, `notifications`, `audit` packages. Add config loading, lifespan hooks, `/health` endpoint, and OpenAPI `/api/v1` prefix.

### Dependencies

TASK-INF-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Application starts in Docker and locally *(pending Docker Desktop for live verify)*
- [x] `/api/v1/health` returns database and Redis status
- [x] Project structure matches architecture bounded contexts
- [x] Pydantic settings for DATABASE_URL, REDIS_URL, JWT secrets

**Implementation status:** Implemented (2026-06-10) via `openspec/changes/foundation`.

**FR/NFR:** FR-PLT-003, OpenAPI `/health`

---

## TASK-INF-003: Celery Worker and Beat Setup

### Description

Configure Celery with Redis broker, queue routing (`ingestion`, `reports`, `alerts`, `email`, `maintenance`), task base class carrying `correlation_id` and `organization_id`, and Beat schedule placeholder.

### Dependencies

TASK-INF-001, TASK-INF-002

### Estimated Complexity

**M**

### Definition of Done

- [x] Sample task executes on correct queue from API
- [ ] Beat container runs without duplicate schedule execution *(pending live Docker verify)*
- [x] Worker shares SQLAlchemy session factory with API
- [x] Failed tasks log with correlation ID

**Implementation status:** Implemented (2026-06-10) via `openspec/changes/foundation`.

**FR/NFR:** ADR-004, NFR-AUD-004

---

## TASK-INF-004: Alembic Migration Framework

### Description

Initialize Alembic with async SQLAlchemy engine, multi-schema support, and CI step running `alembic upgrade head` against test Postgres.

### Dependencies

TASK-INF-002

### Estimated Complexity

**S**

### Definition of Done

- [ ] `alembic revision --autogenerate` works against models *(manual dev verify when models added)*
- [x] Migration runs via compose `migrate` job
- [x] Downgrade scripts exist for initial revisions

**Implementation status:** Implemented (2026-06-10) via `openspec/changes/foundation`.

**Spec:** database.md Migration Strategy

---

## TASK-INF-005: CI Pipeline (GitHub Actions)

### Description

Add workflow: lint (ruff/black/mypy), backend tests, frontend tests, `@redocly/cli lint` on OpenAPI, dependency scan (bandit/pip-audit).

### Dependencies

TASK-INF-002

### Estimated Complexity

**M**

### Definition of Done

- [x] PR pipeline runs on push
- [x] OpenAPI lint passes on `openspec/specifications/apis/openapi.yaml`
- [x] Test job uses Docker Postgres service container

**Implementation status:** Implemented (2026-06-10) — `.github/workflows/ci.yml`.

**NFR:** NFR-SEC-007, ADR-012

---

## TASK-INF-006: React SPA Scaffold

### Description

Create React + TypeScript + MUI app with React Router, TanStack Query, auth context, API client (`/api/v1`), and en-US i18n resource structure.

### Dependencies

None (parallel with backend)

### Estimated Complexity

**M**

### Definition of Done

- [x] App builds and runs via Vite
- [x] API client attaches JWT and `X-Correlation-ID`
- [x] User-facing strings use i18n keys (NFR-LOC-001)
- [x] Placeholder routes for login, dashboard, admin

**Implementation status:** Implemented (2026-06-10) — `frontend/` (4 vitest tests passing).

**ADR:** ADR-006
