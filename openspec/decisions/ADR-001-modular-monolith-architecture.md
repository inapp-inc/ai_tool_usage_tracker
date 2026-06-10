# ADR-001: Modular Monolith Architecture

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The AI Tool Usage Tracker must deliver Phase 1 MVP capabilities—administration, dashboards, usage tracking, reporting, alerts, and file ingestion—for organizations with up to 50 AI tools, 200 teams, and 5,000 users. All modules share core entities (users, teams, tools, pricing) and require ACID consistency for cost attribution and audit trails.

The product team is small, time-to-market is critical, and operational complexity must stay manageable while meeting a 99.5% uptime SLA. The architecture must support future extraction of high-load components without a full rewrite.

---

## Decision

Adopt a **modular monolith** as the primary architecture style:

- Single deployable **FastAPI** backend with strict internal module boundaries (Identity, Administration, Ingestion, Usage, Dashboard, Reporting, Notifications, Audit).
- Modules communicate through **application services**, not direct cross-schema SQL access.
- **Hexagonal (ports & adapters)** applied within each module for infrastructure substitution.
- **Asynchronous workers** (Celery) handle workloads decoupled from the synchronous API, but remain part of the same codebase and deployment unit for Phase 1.

---

## Consequences

### Positive

- Faster MVP delivery with one deployment pipeline and shared transaction boundaries.
- Simpler debugging and tracing compared to distributed microservices.
- Shared domain entities (team, tool, user) avoid distributed transaction patterns (sagas).
- Clear module boundaries enable future service extraction (ingestion, reporting) in Phase 2.
- Lower operational overhead for a single product team.

### Negative

- Entire API tier scales as a unit; cannot independently scale a single module without extraction.
- Discipline required to enforce module boundaries; violations create a "distributed monolith" anti-pattern internally.
- Large codebase in one repository requires strong coding standards and ownership rules.

### Neutral

- Deployment artifact is one Docker image for API; workers may use the same image with different entrypoints.
- Database remains shared PostgreSQL with schema namespaces per module.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Microservices** | Operational cost (service mesh, distributed tracing, contract versioning) exceeds benefit at reference scale; shared entities create coupling anyway. |
| **Traditional layered monolith without modules** | Weak boundaries lead to spaghetti; harder to extract or test domains independently. |
| **Serverless-only (Lambda)** | Long-running ingestion parsing and Celery-style report jobs fit workers better; cold start and timeout limits complicate 50 MB file processing. |
| **Event sourcing** | Full event replay not required for MVP reporting; normalized facts plus aggregates are sufficient. |

**Supersedes:** None  
**Related:** ADR-002, ADR-004, ADR-008
