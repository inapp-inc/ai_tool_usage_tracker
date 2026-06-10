# ADR-010: OpenTelemetry Observability Stack

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The platform must meet **99.5% uptime**, diagnose performance regressions (dashboard ≤3s, reports ≤10s), alert on operational failures (queue depth, error rates), and support audit correlation across API and worker requests (NFR-AUD-004). Project technical direction specifies **OpenTelemetry**, **Prometheus**, and **Grafana**. The modular monolith plus Celery workers require distributed tracing across process boundaries.

---

## Decision

Implement observability using the **OpenTelemetry (OTel)** standard:

| Signal | Implementation |
|--------|----------------|
| **Traces** | OTel SDK in FastAPI and Celery workers; export via OTel Collector |
| **Metrics** | Prometheus exposition; scrape API, workers, PostgreSQL/Redis exporters |
| **Logs** | Structured JSON to stdout; correlation ID, user ID, action, outcome |

**Grafana** dashboards for: API p95 latency, error rate, Celery queue depth, ingestion throughput, cache hit ratio, PostgreSQL connections.

**Alertmanager** (or equivalent) for NFR-MON-004 thresholds (error rate >1%, p95 >3s, queue >1,000).

Trace propagation: `X-Correlation-ID` from API through Celery task kwargs; linked spans for async jobs.

---

## Consequences

### Positive

- End-to-end request tracing across API → worker → database.
- Standard vendor-neutral instrumentation (OpenTelemetry).
- Metrics support capacity planning and SLA validation evidence.
- Correlation IDs link logs, traces, and audit entries for incident response.

### Negative

- Instrumentation overhead (mitigated by 10% trace sampling in production).
- Operational burden to maintain Grafana dashboards and alert rules.
- Log volume costs in CloudWatch/Loki at scale.

### Neutral

- Datadog/New Relic alternatives exist; OTel avoids proprietary lock-in per cloud-native principle.
- Synthetic monitoring (NFR-MON-006) complements but does not replace OTel.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Logs only (no tracing)** | Insufficient for debugging async Celery workflows and latency bottlenecks. |
| **Proprietary APM only (Datadog)** | Higher cost; OTel specified in project stack. |
| **CloudWatch only** | Weaker distributed tracing story for Celery; Grafana+Prometheus richer for SRE dashboards. |
| **No metrics (manual debugging)** | Cannot prove NFR compliance or alert proactively on queue backlog. |

**Supersedes:** None  
**Related:** ADR-004, ADR-007
