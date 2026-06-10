# ADR-012: API-First OpenAPI Contract

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

OpenSpec principles require **API-first design**, modular architecture, and testability. The React SPA, future integrations, and QA contract testing all depend on a stable, versioned HTTP API. FastAPI generates OpenAPI automatically, but the team needs an explicit governance decision that the OpenAPI spec is the **single source of truth** for frontend/backend integration.

The API surface covers 10+ resource areas: auth, tools, teams, credentials, thresholds, uploads, dashboard, reports, notifications, and audit logs.

---

## Decision

Adopt an **API-first** approach with **OpenAPI 3.x** as the integration contract:

- Canonical spec location: `openspec/specifications/apis/openapi.yaml` (maintained alongside FastAPI implementation).
- URL versioning: `/api/v1/` prefix for all endpoints.
- Error format: **RFC 7807** Problem Details for consistent client error handling.
- Authentication documented as HTTP Bearer JWT (ADR-005).
- Pagination: cursor-based for large collections.
- Idempotency: `Idempotency-Key` header on ingestion commit and other sensitive POST operations.
- Correlation: `X-Correlation-ID` required/propagated on all requests.

FastAPI auto-generated schema MUST be reconciled with canonical spec in CI; drift fails the build.

Contract tests (Schemathesis or equivalent) validate implementation against spec on each PR.

---

## Consequences

### Positive

- Frontend and backend teams work from one contract; reduces integration defects.
- Enables automated contract testing and mock server generation.
- Documents RBAC-scoped endpoints for security review.
- Supports future external API consumers (vendor sync, integrations) in Phase 2.

### Negative

- Dual maintenance of FastAPI routes and canonical YAML until fully generated-from-code workflow matures.
- Breaking API changes require version bump (`/api/v2/`) and deprecation policy.

### Neutral

- GraphQL rejected for Phase 1; REST sufficient for CRUD + report endpoints.
- gRPC not required; browser clients use JSON REST.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Code-first without published spec** | Violates OpenSpec API-first principle; hinders contract testing. |
| **GraphQL** | Overhead for report export downloads and file upload; team REST familiarity. |
| **gRPC** | Poor browser support; SPA requires REST/JSON gateway anyway. |
| **Ad hoc undocumented REST** | Not testable or reviewable; high integration risk. |
| **OpenAPI generated only at runtime (no checked-in spec)** | No PR-level diff review of API changes. |

**Supersedes:** None  
**Related:** ADR-002, ADR-005, ADR-006
