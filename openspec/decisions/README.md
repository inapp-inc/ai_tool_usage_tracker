# Architecture Decision Records

Project-specific ADRs for the **AI Tool Usage Tracker**.

## Format

Each ADR uses:

- **Context** — forces and constraints driving the decision
- **Decision** — what was chosen
- **Consequences** — positive, negative, and neutral outcomes
- **Alternatives** — options considered and rejected

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](./ADR-001-modular-monolith-architecture.md) | Modular Monolith Architecture | Accepted |
| [ADR-002](./ADR-002-fastapi-python-backend.md) | FastAPI Python Backend | Accepted |
| [ADR-003](./ADR-003-postgresql-system-of-record.md) | PostgreSQL as System of Record | Accepted |
| [ADR-004](./ADR-004-celery-redis-async-processing.md) | Celery and Redis Async Processing | Accepted |
| [ADR-005](./ADR-005-jwt-rbac-authentication.md) | JWT and RBAC Authentication (Phase 1) | Accepted |
| [ADR-006](./ADR-006-react-spa-frontend.md) | React SPA Frontend | Accepted |
| [ADR-007](./ADR-007-aws-eks-deployment.md) | AWS EKS Deployment Topology | Accepted |
| [ADR-008](./ADR-008-cqrs-lite-redis-caching.md) | CQRS-Lite Read Models and Redis Caching | Accepted |
| [ADR-009](./ADR-009-s3-object-storage-ingestion.md) | S3 Object Storage for Uploads and Reports | Accepted |
| [ADR-010](./ADR-010-opentelemetry-observability.md) | OpenTelemetry Observability Stack | Accepted |
| [ADR-011](./ADR-011-vendor-parser-adapter-pattern.md) | Vendor Parser Adapter Pattern | Accepted |
| [ADR-012](./ADR-012-api-first-openapi-contract.md) | API-First OpenAPI Contract | Accepted |
| [ADR-013](./ADR-013-docker-compose-local-storage.md) | Docker Compose + Local Volume Storage (Phase 1) | Accepted · **Supersedes ADR-007 & ADR-009 for Phase 1** |

> **Phase 1 deployment:** Follow **ADR-013** and [deployment.md](../specifications/deployment.md). ADR-007 (EKS) and ADR-009 (S3) apply to **Phase 2 cloud migration** only.

## Governance

ADRs are immutable once accepted. To change a decision, create a new ADR that supersedes the prior record.

## Related Documents

- [Architecture overview](../architecture/01-architecture-overview.md)
- [Deployment specification](../specifications/deployment.md)
- [Functional requirements](../requirements/README.md)
- [Non-functional requirements](../requirements/NFR.md)
- [Project specification](../project.md)
