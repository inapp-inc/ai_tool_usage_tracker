# ADR-003: PostgreSQL as System of Record

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The platform stores usage events, cost calculations, team/tool configuration, thresholds, alerts, audit logs, and user/role data. Requirements demand ACID transactions for cost attribution, relational reporting (joins across teams, tools, users), 24-month data retention with configurable policies, and append-only audit trails. Reference scale targets ~50 million usage events over the retention window.

Dashboard and report queries are read-heavy; writes occur during ingestion bursts and administrative changes.

---

## Decision

Use **PostgreSQL 15+** as the **single system of record** for all transactional and aggregate data in Phase 1, deployed as a **Docker container** with a persistent volume — **not Amazon RDS**.

Implementation:

- Schema namespaces per bounded context (`auth`, `admin`, `ingestion`, `usage`, `reporting`, `notifications`, `audit`).
- `usage_events` as append-oriented fact table; `usage_aggregates` for pre-computed rollups (daily/team/tool/user).
- Declarative table partitioning on `usage_events` by month when row count exceeds 10M.
- Alembic for backward-compatible schema migrations.

---

## Consequences

### Positive

- ACID guarantees for ingestion commits and cost calculations.
- Mature SQL for complex reports (cost, team comparison, alert history).
- Docker deployment aligns with project stack; same Compose/network as FastAPI and Celery; no RDS cost or vendor lock-in for the database tier.
- Daily `pg_dump` + persistent volume satisfies backup requirements (NFR-BKP-001) without managed RDS snapshots.
- Strong indexing and EXPLAIN tooling for performance tuning (NFR-SCL-003).
- Single database simplifies modular monolith transaction boundaries.

### Negative

- Analytical queries at very large scale may eventually require read replicas or OLAP offload (Phase 2).
- All modules share one database instance—connection pool sizing critical under load.
- Schema migration discipline required for zero-downtime deploys.
- Single-container PostgreSQL is a single point of failure until a streaming replica is added (Phase 2); host/volume backup discipline is operator responsibility.

### Neutral

- MongoDB/document store not needed; usage data is highly structured and relational.
- Redis used for cache/broker only, not primary persistence.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **MongoDB** | Weaker fit for financial aggregates, joins, and audit immutability guarantees; project specifies PostgreSQL. |
| **Polyglot persistence (PostgreSQL + separate analytics DB)** | Premature for Phase 1 scale; adds sync complexity. |
| **SQLite** | Insufficient for multi-user production, HA, and 5,000-user concurrent access. |
| **Amazon RDS** | Project deploys PostgreSQL in Docker with persistent volumes; avoids managed DB cost and matches local/prod parity. |
| **Event store only (Event Sourcing)** | Rejected in ADR-001; replay not required for MVP reporting needs. |

**Supersedes:** None  
**Related:** ADR-001, ADR-008
