# Usage Tracking Tasks

Usage events, cost calculation, and aggregation.

---

## TASK-USG-001: Usage Event Recording and Cost Calculator

### Description

Implement usage service to persist `usage_events` with pricing snapshot, token totals, estimated_cost, overage_cost using Strategy pattern per pricing_model.

### Dependencies

TASK-DB-004, TASK-ADM-001

### Estimated Complexity

**L**

### Definition of Done

- [ ] Cost calculated from tool config at ingest time (not retroactive on price change)
- [ ] Package overage computed when tokens exceed allowance
- [ ] Unit tests for flat_token and package_with_overage models
- [ ] FR-USG-001 acceptance criteria verified

**FR:** FR-USG-001 · **ADR:** ADR-008

---

## TASK-USG-002: Aggregation Refresh Job

### Description

Celery task `maintenance.refresh_aggregates` rolling up events into `usage_aggregates` (daily granularity; weekly/monthly derived or separate job).

### Dependencies

TASK-USG-001, TASK-INF-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] Aggregates match sum of underlying events in tests
- [ ] Job idempotent and safe to rerun
- [ ] `refreshed_at` updated; dashboard cache invalidation triggered
- [ ] Near-real-time lag target ≤5 minutes under load test smoke

**FR:** FR-USG-001 · **NFR:** NFR-PER-004

---

## TASK-USG-003: Batch Usage Ingestion API

### Description

Implement authenticated API endpoint for batch usage event ingestion (JSON array) with validation, quarantine for invalid references, async processing option.

### Dependencies

TASK-USG-001, TASK-USG-004, TASK-PLT-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Invalid team/tool references rejected or quarantined with error detail
- [ ] Batch processed via Celery for large payloads
- [ ] Throughput smoke test ≥10K records/minute per worker (NFR-PER-004)

**FR:** FR-USG-002

---

## TASK-USG-004: Idempotency Key Handling

### Description

Implement idempotency for ingestion using `vendor_event_id`, content hash, and `usage.ingest_idempotency` table with 7-day TTL cleanup.

### Dependencies

TASK-DB-004, TASK-USG-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Duplicate events do not double-count tokens
- [ ] Idempotency records expire per retention policy
- [ ] Integration test replays same batch without count increase

**FR:** FR-USG-002
