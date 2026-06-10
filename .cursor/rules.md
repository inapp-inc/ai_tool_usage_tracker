# Cursor Rules — AI Tool Usage Tracker

These rules govern all AI-assisted implementation in this repository. They are **mandatory** unless a written ADR or OpenSpec change explicitly supersedes them.

## Project Context

- **Product:** AI Tool Usage Tracker (Phase 1 MVP)
- **Frontend:** React, TypeScript (strict), Material UI, TanStack Query, Recharts
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Celery, Alembic
- **Data:** PostgreSQL 15 (Docker), Redis, **local volume file storage** (`STORAGE_BACKEND=local`)
- **Spec sources:** `openspec/requirements/`, `openspec/specifications/`, `openspec/architecture/`, `openspec/decisions/`, `openspec/tasks/`

---

## 1. TypeScript (Frontend)

### Strict mode — required

- Enable and preserve `"strict": true` in `tsconfig.json` (including `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`).
- Do **not** disable strict checks locally with `@ts-ignore`, `@ts-expect-error`, or `// @ts-nocheck` except with a one-line justification and linked task ID.
- Prefer `unknown` over implicit or explicit unsafe casts; narrow with type guards.

### No `any` — forbidden

- Never use the `any` type.
- Never use `as any` or untyped `JSON.parse` results without validation.
- For API payloads, use types generated from or aligned with `openspec/specifications/apis/openapi.yaml`, or validate at runtime with Zod (or equivalent) at API boundaries.

### Frontend architecture

- **UI layer:** React components, hooks, routes — no direct `fetch` in presentational components.
- **Application layer:** TanStack Query hooks and use-case functions orchestrate server state.
- **Infrastructure layer:** API client modules call `/api/v1` with typed request/response shapes.
- Dependencies point inward: UI → application → infrastructure. Domain types live in `types/` or generated OpenAPI types, not inside components.

---

## 2. Python (Backend)

### Type safety

- Use type hints on all public functions, methods, and module boundaries.
- Run `mypy` (strict or project-configured) in CI; fix violations before merge.
- Avoid `Any` in domain and application layers; use `Protocol`, `TypedDict`, or Pydantic models.

### Clean Architecture — required

Layer order (dependencies point **inward** only):

| Layer | Responsibility | Examples |
|-------|----------------|----------|
| **Domain** | Entities, value objects, domain rules | `Tool`, `UsageEvent`, pricing strategies |
| **Application** | Use cases, orchestration, ports (interfaces) | `CreateToolUseCase`, `ParserPort`, `ToolRepository` |
| **Infrastructure** | Adapters: DB, local storage, SMTP, Celery, parsers | SQLAlchemy repos, filesystem storage adapter, email adapter |
| **API** | FastAPI routers, thin controllers | HTTP mapping only — no business logic |

**Forbidden:**

- Business logic in routers or Celery task bodies beyond delegation to use cases.
- Domain/application layers importing FastAPI, SQLAlchemy session, or boto3 directly.
- Cross-module direct SQL against another bounded context's tables.

Structure MUST align with bounded contexts: `auth`, `admin`, `ingestion`, `usage`, `dashboard`, `reporting`, `notifications`, `audit`.

---

## 3. Repository Pattern — mandatory

- All persistence goes through **repository interfaces (ports)** defined in the application layer.
- Infrastructure provides SQLAlchemy (or test double) **adapter** implementations.
- Repositories MUST enforce `organization_id` (tenant scope) on every query and write.
- Do not expose raw SQLAlchemy models outside infrastructure; map to domain entities or read DTOs at repository boundaries.
- One repository per aggregate root unless a documented read-model exception exists in OpenSpec.

---

## 4. Dependency Injection — mandatory

### Backend (FastAPI)

- Wire dependencies with `Depends()` and a composition root / container module.
- Inject use cases into routers; inject repositories into use cases.
- Do not instantiate repositories or database sessions inside domain logic.
- Celery tasks receive dependencies via shared factory or task base class — same wiring rules as API.

### Frontend

- Inject API clients and services through React context or explicit constructor/factory parameters in hooks.
- Avoid importing singleton HTTP clients inside leaf components.

---

## 5. API Validation — mandatory

### Contract source of truth

- Canonical contract: `openspec/specifications/apis/openapi.yaml` and `components/*.yaml`.
- **Never** change a public endpoint, request schema, response schema, status code, or auth requirement in code without updating the OpenSpec API specification **first**.

### Backend

- Every endpoint MUST use Pydantic v2 request/response models aligned with OpenAPI.
- Validate path, query, header, and body inputs before use-case execution.
- Return errors as RFC 7807 Problem Details (`application/problem+json`) per OpenAPI `responses.yaml`.
- Enforce RBAC in application layer after authentication — not only in UI.

### Frontend

- Validate external data at the boundary (API client / query function) before use in UI.
- Do not assume server responses match types without runtime checks where data is untrusted.

---

## 6. Tests — required

Generate or update tests with every implementation task. Do not merge behavior changes without test evidence.

| Layer | Minimum expectation |
|-------|---------------------|
| **Domain / use cases** | Unit tests for business rules and edge cases |
| **Repositories** | Integration tests against PostgreSQL (test container or Docker) |
| **API** | Integration tests for happy path, 401/403, validation errors |
| **Parsers / cost logic** | Fixture-based unit tests per vendor format |
| **Frontend** | Component tests for critical flows; API hooks mocked with typed fixtures |
| **Contract** | Schemathesis or equivalent against running API vs OpenAPI (CI) |

Tests MUST reference task IDs or FR/NFR IDs in descriptions where applicable (e.g. `TASK-ADM-001`, `FR-ADM-001`).

Run relevant suites before marking work complete:

```bash
# Backend (adjust paths to project layout)
pytest
mypy .

# Frontend
npm run test
npm run lint
npx @redocly/cli lint openspec/specifications/apis/openapi.yaml
```

---

## 7. OpenSpec — update after implementation

After completing an implementation slice:

1. **Verify** behavior matches `openspec/requirements/` and task Definition of Done in `openspec/tasks/`.
2. **Update OpenSpec artifacts** when behavior, contracts, or design decisions change:
   - API changes → `openspec/specifications/apis/`
   - Schema changes → `openspec/specifications/database.md` + Alembic revision notes
   - New/changed decisions → new ADR in `openspec/decisions/` (do not edit accepted ADRs — supersede)
   - Completed tasks → mark Done in task file or change folder `tasks.md`
   - Durable behavior → delta specs under `openspec/changes/<change-id>/specs/` when using OpenSpec change workflow
3. **Document** spec updates in the handoff: list files changed in `openspec/` alongside code changes.

If implementation reveals a spec gap, **update the spec first**, then code — never the reverse for public behavior.

---

## 8. Public Contracts — immutable without spec change

**Public contracts** include:

- OpenAPI paths, methods, schemas, and error formats
- Database columns and constraints documented in `openspec/specifications/database.md`
- JWT/RBAC role semantics documented in requirements
- Event/task payload shapes consumed by other services or workers

### Required workflow for contract changes

1. Update `openspec/specifications/apis/` (and requirements if FR/NFR impact).
2. Get explicit review or approval when the change is breaking.
3. Implement code to match the updated spec.
4. Update contract tests and consumer types (frontend generated types / Zod schemas).
5. Record decision in ADR if architectural (see `openspec/decisions/`).

**Breaking changes** require a new API version prefix (e.g. `/api/v2/`) or a documented migration — never silent breakage.

---

## 9. Security and Quality Baselines

- No secrets, credentials, or JWTs in source control, logs, or error messages.
- Encrypt vendor credentials at rest (see ADR-003, NFR-SEC-001).
- Use parameterized queries / ORM only — no string-concatenated SQL.
- Propagate `X-Correlation-ID` on API and worker boundaries.
- Prefer smallest diff that satisfies the task; do not refactor unrelated code.
- Match existing naming, folder layout, and patterns in the codebase.

---

## 10. Implementation Workflow

When implementing from `openspec/tasks/`:

1. Read the task **Description**, **Dependencies**, and **Definition of Done**.
2. Read linked FR/NFR and OpenAPI operations before writing code.
3. Implement backend and/or frontend following Clean Architecture and repository/DI rules.
4. Add/update tests proving Definition of Done.
5. Update OpenSpec specifications if any public surface changed.
6. Report: task ID, files changed, spec files changed, tests run.

Do **not** create git commits or pull requests unless the user explicitly requests it.

---

## Quick Reference — Spec Locations

| Artifact | Path |
|----------|------|
| Functional requirements | `openspec/requirements/` |
| Non-functional requirements | `openspec/requirements/NFR.md` |
| OpenAPI | `openspec/specifications/apis/openapi.yaml` |
| Database spec | `openspec/specifications/database.md` |
| Testing spec | `openspec/specifications/testing.md` |
| Deployment spec | `openspec/specifications/deployment.md` |
| Architecture | `openspec/architecture/` |
| ADRs | `openspec/decisions/` |
| Implementation tasks | `openspec/tasks/` |
| OpenSpec config | `openspec/config.yaml` |
