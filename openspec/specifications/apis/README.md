# API Specifications

OpenAPI 3.0 contracts for the **AI Tool Usage Tracker** platform.

## Canonical Spec

| File | Description |
|------|-------------|
| [openapi.yaml](./openapi.yaml) | Main OpenAPI entry point — paths, tags, `$ref` to components |
| [local-development.md](../local-development.md) | Docker Compose stack, env vars, interim `/health` probe |
| [testing.md](../testing.md) | Test strategy — unit, integration, contract, E2E, performance, security, acceptance |
| [deployment.md](../deployment.md) | Docker, CI/CD, secrets, rollback, monitoring, alerting, backup, DR |
| [database.md](../database.md) | PostgreSQL entities, indexes, constraints, migrations, retention |
| [components/schemas.yaml](./components/schemas.yaml) | Request/response schemas and validation rules |
| [components/responses.yaml](./components/responses.yaml) | Standard error and success response definitions |
| [components/parameters.yaml](./components/parameters.yaml) | Shared query, path, and header parameters |
| [components/examples.yaml](./components/examples.yaml) | Named request/response examples |
| [components/security.yaml](./components/security.yaml) | Authentication schemes and RBAC role definitions |

## Conventions

| Aspect | Standard |
|--------|----------|
| Base path | `/api/v1` |
| Auth | `Authorization: Bearer <JWT>` |
| Errors | RFC 7807 Problem Details (`application/problem+json`) |
| Pagination | Cursor-based: `limit` + `cursor` |
| Correlation | `X-Correlation-ID` header (optional on request; echoed in response) |
| Idempotency | `Idempotency-Key` on `POST /uploads/{uploadId}/commit` |
| Date filters | ISO 8601 `from` / `to` query params (UTC storage, org TZ display) |

## Authentication Requirements Summary

| Endpoint group | Auth | Roles |
|----------------|------|-------|
| `/auth/login`, `/health` | None | Public |

> **TASK-INF-001 interim:** The running Compose stack exposes `GET /health` at the **root** (no `/api/v1` prefix). TASK-INF-002 will mount the contract path at `/api/v1/health`. Response shape matches `HealthResponse`; dependency failures return `"error"` (see [local-development.md](../local-development.md)).
| `/auth/refresh`, `/auth/me` | Bearer JWT | Any authenticated |
| `/tools`, `/credentials` (write) | Bearer JWT | `super_admin` |
| `/teams` (write) | Bearer JWT | `super_admin`, `team_admin` (scoped) |
| `/thresholds` | Bearer JWT | `super_admin`, `team_admin` (scoped) |
| `/uploads` | Bearer JWT | `super_admin`, `team_admin` (scoped) |
| `/dashboard/*` | Bearer JWT | Role-scoped read |
| `/reports/*` | Bearer JWT | Role-scoped read |
| `/notifications/*` | Bearer JWT | Any authenticated (scoped) |
| `/audit-logs/*` | Bearer JWT | `super_admin`, `auditor` |

## Related Documents

- [ADR-012 API-First OpenAPI Contract](../../decisions/ADR-012-api-first-openapi-contract.md)
- [Integration patterns](../../architecture/04-integration-patterns.md)
- [Functional requirements](../../requirements/README.md)

## Validation

```bash
# Requires openapi-cli or swagger-cli
npx @redocly/cli lint openspec/specifications/apis/openapi.yaml
```
