# Architecture Specifications

Solution architecture for the **AI Tool Usage Tracker**, derived from [project.md](../project.md), [functional requirements](../requirements/README.md), and [NFR](../requirements/NFR.md).

## Documents

| Document | Contents |
|----------|----------|
| [01-architecture-overview.md](./01-architecture-overview.md) | Architecture style, justification, patterns considered, bounded contexts |
| [02-component-diagram.md](./02-component-diagram.md) | Logical and physical component views (Mermaid) |
| [03-sequence-diagrams.md](./03-sequence-diagrams.md) | Key interaction flows (Mermaid) |
| [04-integration-patterns.md](./04-integration-patterns.md) | External and internal integration patterns |
| [05-data-flow.md](./05-data-flow.md) | Data ingestion, aggregation, and read paths |
| [06-deployment-topology.md](./06-deployment-topology.md) | Docker Compose deployment topology (Phase 1); AWS diagrams deferred |
| [../specifications/local-development.md](../specifications/local-development.md) | Docker Compose local stack (TASK-INF-001) |
| [../specifications/deployment.md](../specifications/deployment.md) | Deployment — Docker, CI/CD, secrets, rollback, monitoring, DR |
| [../decisions/ADR-013-docker-compose-local-storage.md](../decisions/ADR-013-docker-compose-local-storage.md) | Phase 1 Docker Compose + local storage |
| [../decisions/README.md](../decisions/README.md) | Architecture Decision Records (ADR-001 – ADR-013) |

## Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture style | Modular monolith + event-driven async | MVP speed, clear module boundaries, ops simplicity |
| API layer | FastAPI (Python) | Project stack; async I/O; OpenAPI-native |
| Frontend | React SPA | Rich dashboards; TanStack Query for server state |
| Primary datastore | PostgreSQL (Docker, not RDS) | Relational reporting; ACID for financial aggregates |
| Cache & queue | Redis **Docker container** | Dashboard cache; Celery broker |
| Object storage | **Local Docker volumes** | Uploads and reports on `storage_data` volume |
| Auth | JWT + RBAC | Phase 1 scope; SSO deferred to Phase 2 |
| Deployment | **Docker Compose** (all envs) | VM/bare-metal host; [ADR-013](../decisions/ADR-013-docker-compose-local-storage.md) |

## Related Artifacts

- OpenAPI contract: [openspec/specifications/apis/openapi.yaml](../specifications/apis/openapi.yaml)
- Functional requirements: `openspec/requirements/`
- Non-functional requirements: `openspec/requirements/NFR.md`
- Architecture Decision Records: [openspec/decisions/README.md](../decisions/README.md)
