# ADR-008: CQRS-Lite Read Models and Redis Caching

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

Dashboard widgets and standard reports are read-heavy operations that must meet strict latency targets: **≤3 seconds p95** for dashboards and **≤10 seconds p95** for standard reports (NFR-PER-001, NFR-PER-002). Write paths (usage ingestion, admin config changes) mutate normalized `usage_events` and require aggregation updates.

Full **event sourcing** and separate read databases were rejected in ADR-001 as unnecessary for MVP complexity.

---

## Decision

Implement **CQRS-lite** with pre-computed aggregates and **Redis cache-aside**:

**Write path:**
1. Ingestion commits `usage_events` (facts).
2. Cost calculator applies tool pricing (Strategy pattern).
3. Aggregation job updates `usage_aggregates` (daily/team/tool/user rollups).

**Read path:**
1. Dashboard/report queries read from `usage_aggregates` (not raw events for standard widgets).
2. Redis cache-aside with TTL **1–5 minutes** keyed by `organization_id`, scope, and date range hash.
3. Cache invalidation on: usage commit, pricing change, team membership change.

Dashboard responses SHOULD include `last_updated_at` to reflect eventual consistency (near-real-time SLA ≤5 minutes, NFR-PER-004).

---

## Consequences

### Positive

- Predictable read performance for dashboards at reference scale.
- Reduced PostgreSQL load for repeated dashboard refreshes.
- Simpler than full CQRS/event sourcing; fits modular monolith.
- Cache invalidation rules are bounded and testable.

### Negative

- Eventual consistency between ingestion and dashboard display (up to aggregation lag + cache TTL).
- Cache invalidation bugs cause stale data—requires monitoring and admin refresh option.
- Redis memory sizing needed as org count and filter permutations grow.

### Neutral

- Raw `usage_events` still queried for detailed drill-down and large ad-hoc reports.
- Materialized views in PostgreSQL acceptable alternative/complement to application-level aggregates.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Query raw events for all dashboards** | Will not meet 3s p95 at 50M event scale without heavy runtime aggregation. |
| **Full CQRS with separate read DB** | Operational complexity disproportionate for Phase 1. |
| **Event sourcing** | Rejected in ADR-001; no replay requirement for MVP. |
| **No caching (PostgreSQL only)** | Higher DB load; risk of missing p95 targets under concurrent dashboard users. |
| **CDN caching of API responses** | User-specific RBAC-scoped data unsuitable for shared CDN cache. |

**Supersedes:** None  
**Related:** ADR-003, ADR-004
