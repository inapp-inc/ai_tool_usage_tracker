# Operations and Quality Tasks

Observability, backups, accessibility, and contract validation.

---

## TASK-OPS-001: OpenTelemetry Instrumentation

### Description

Add OTel SDK to FastAPI and Celery workers; propagate trace context and correlation_id; export to collector sidecar or local OTLP endpoint.

### Dependencies

TASK-INF-002, TASK-INF-003, TASK-PLT-005

### Estimated Complexity

**M**

### Definition of Done

- [ ] HTTP spans include route, status, duration
- [ ] Celery tasks linked to parent trace
- [ ] No secrets in span attributes
- [ ] NFR-MON-002 acceptance criteria demonstrable

**NFR:** NFR-MON-001 – 003 · **ADR:** ADR-010

---

## TASK-OPS-002: Prometheus Metrics and Grafana Dashboards

### Description

Expose Prometheus metrics (request latency, error rate, queue depth, cache hit ratio, PG connections) and provision Grafana dashboards per NFR-MON-001.

### Dependencies

TASK-OPS-001, TASK-DSH-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] `/metrics` endpoint or OTel Prometheus exporter configured
- [ ] Grafana dashboard JSON checked into repo
- [ ] Alert rules for error rate >1% and queue >1000 documented

**NFR:** NFR-MON-001, NFR-MON-004

---

## TASK-OPS-003: PostgreSQL Backup Container/Script

### Description

Implement daily `pg_dump -Fc` via cron sidecar or host script targeting Docker Postgres volume backups per database.md; document restore procedure.

### Dependencies

TASK-INF-001

### Estimated Complexity

**S**

### Definition of Done

- [ ] Backup runs daily with 30-day retention on **`backups_data` local volume**
- [ ] Restore drill documented and tested once in staging
- [ ] NFR-BKP-001 acceptance criteria evidence captured

**NFR:** NFR-BKP-001, NFR-BKP-002 · **database.md:** Backups section

---

## TASK-OPS-004: OpenAPI Contract Tests

### Description

Add Schemathesis or Dredd contract tests validating running API against `openspec/specifications/apis/openapi.yaml` in CI.

### Dependencies

TASK-INF-005, core API endpoints implemented

### Estimated Complexity

**M**

### Definition of Done

- [ ] Contract test job runs in CI against test stack
- [ ] Auth endpoints and at least one CRUD resource validated
- [ ] Drift between spec and implementation fails build

**ADR:** ADR-012

---

## TASK-OPS-005: Accessibility Baseline (P1)

### Description

Run axe scans and keyboard walkthrough on core journeys (login, dashboard, admin forms, reports); fix critical WCAG 2.1 AA violations.

### Dependencies

TASK-UI-001 – TASK-UI-006

### Estimated Complexity

**M**

### Definition of Done

- [ ] Zero critical axe violations on core pages
- [ ] Keyboard-only walkthrough checklist completed
- [ ] Warning/Critical alerts use non-color cues (NFR-ACC-003)
- [ ] NFR-ACC-001–003 evidence documented

**NFR:** NFR-ACC-001 – NFR-ACC-003

---

## TASK-OPS-006: Credential Expiry Reminder Job

### Description

Scheduled job scanning `admin.credentials.expires_at` and enqueueing notification + email tasks before expiration (FR-ADM-003).

### Dependencies

TASK-ADM-003, TASK-NTF-002, TASK-NTF-004

### Estimated Complexity

**S**

### Definition of Done

- [ ] Reminder fires at configurable days-before threshold
- [ ] In-app and email notifications sent to Super Admin
- [ ] Job audit-logged; no secret exposure

**FR:** FR-ADM-003 · **NFR:** NFR-PER-005

---

## TASK-OPS-007: End-to-End MVP Smoke Test

### Description

Automated E2E test: login → create tool → create team → upload file → preview → commit → verify dashboard widgets show data → generate cost report.

### Dependencies

TASK-UI-003, TASK-UI-004, TASK-RPT-003, TASK-INF-001

### Estimated Complexity

**L**

### Definition of Done

- [ ] E2E runs in CI against Docker Compose stack
- [ ] Covers primary Phase 1 MVP path from project.md
- [ ] Documented as MVP release gate evidence

**Phase 1 MVP scope:** project.md Phase Strategy
