# ADR-002: FastAPI Python Backend

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The project technical direction specifies **Python** and **FastAPI** for the backend. The platform must expose REST APIs for a React SPA, validate complex ingestion payloads, enforce RBAC, integrate with PostgreSQL, Redis, S3, and Celery, and produce an **OpenAPI contract** as the integration source of truth (OpenSpec API-first principle).

Backend workloads include CRUD administration, aggregate queries for dashboards, file parsing orchestration, cost calculation, and background task enqueueing.

---

## Decision

Use **FastAPI** with **Pydantic v2** for request/response validation and **SQLAlchemy 2** for PostgreSQL persistence as the sole backend API framework for Phase 1.

Structure:

- Routers (API layer) → Application services (use cases) → Domain models → Repository adapters.
- Automatic OpenAPI generation from route and schema definitions.
- Async endpoints where I/O-bound; sync acceptable for CPU-bound parsing delegated to Celery.

---

## Consequences

### Positive

- Native OpenAPI generation aligns with API-first and contract testing requirements.
- Pydantic provides strong input validation (NFR-SEC-006 injection prevention).
- Python ecosystem suits data parsing (CSV, JSON, XLSX vendor exports) and numerical cost calculations.
- Async I/O improves concurrent dashboard API throughput under load.
- Aligns with documented project stack in `project.md`.

### Negative

- Single-language backend team required (Python); no Node.js/NestJS option in Phase 1.
- CPU-heavy parsing must not block the event loop—requires Celery delegation discipline.
- SQLAlchemy learning curve for developers unfamiliar with ORM patterns.

### Neutral

- FastAPI is younger than Django but sufficient for this greenfield product.
- GIL limits CPU parallelism in one process; mitigated by multiple Uvicorn workers and Celery processes.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **NestJS (Node.js/TypeScript)** | Superseded by project decision to use Python/FastAPI; would split stack from stated direction. |
| **Django + DRF** | Heavier framework; FastAPI better fit for API-only backend with OpenAPI-native design. |
| **Flask** | Lacks built-in async, automatic OpenAPI, and modern validation ergonomics. |
| **Go (Gin/Fiber)** | Strong performance but weaker fit for rapid vendor parser development and team Python alignment. |

**Supersedes:** None  
**Related:** ADR-001, ADR-012
