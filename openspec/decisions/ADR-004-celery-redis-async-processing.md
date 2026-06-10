# ADR-004: Celery and Redis Async Processing

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

Several workloads must not block synchronous API requests:

- Parsing vendor export files up to 50 MB (FR-ING-001).
- Large report generation exceeding 10 seconds (FR-RPT-007).
- Threshold evaluation after ingestion and on hourly schedules (FR-NTF-003).
- Email delivery with retry semantics (FR-NTF-002).

Ingestion spikes must not degrade dashboard API latency below NFR-PER-001 (3s p95). The stack specifies **Celery** and **Redis** in `project.md`.

---

## Decision

Use **Celery** workers with **Redis** as both **message broker** and optional **result backend**, with dedicated queues:

| Queue | Workloads |
|-------|-----------|
| `ingestion` | File parse, import commit |
| `reports` | Async PDF/CSV generation, scheduled reports |
| `alerts` | Threshold evaluation |
| `email` | SMTP/SES delivery |
| `maintenance` | Retention enforcement, aggregate refresh |

**Celery Beat** runs scheduled jobs (hourly threshold scan, daily retention, scheduled reports). Tasks must be idempotent and carry `correlation_id` and `organization_id`.

---

## Consequences

### Positive

- API remains responsive during heavy ingestion and report generation.
- Independent horizontal scaling of worker pools per queue (NFR-SCL-002).
- Retry and backoff for email and external integrations.
- Mature Python ecosystem integration with FastAPI.
- Redis dual-use reduces infrastructure footprint for Phase 1.

### Negative

- At-least-once delivery requires idempotent task design; duplicate processing risk without idempotency keys.
- Redis as broker is a single point of failure unless ElastiCache cluster/HA configured (NFR-AVL-002).
- Operational visibility needed for queue depth (NFR-MON-004 alerting).
- Celery Beat requires leader election (single replica) to avoid duplicate schedules.

### Neutral

- Not full event-driven architecture (no Kafka event log); task queue pattern sufficient for MVP.
- Outbox pattern deferred unless delivery guarantees become critical (see ADR-008).

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **AWS SQS + Lambda** | Vendor file parsing may exceed Lambda timeout/memory; Celery workers better for sustained CPU/IO. |
| **Apache Kafka** | Operational overhead disproportionate for Phase 1 task volumes. |
| **RQ (Redis Queue)** | Less feature-rich than Celery for scheduling, routing, and retries. |
| **Sync processing in API** | Violates NFR-PER-002 and NFR-PER-004; blocks API under load. |
| **BullMQ (Node.js)** | Incompatible with Python/FastAPI backend stack. |
| **ARQ** | Viable Python alternative but Celery specified in project stack and has richer scheduling (Beat). |

**Supersedes:** None  
**Related:** ADR-001, ADR-009
