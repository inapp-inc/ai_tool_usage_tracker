# Reporting Tasks

Operational and financial report generation.

---

## TASK-RPT-001: Report Rendering Engine

### Description

Build report query layer and renderers for JSON, CSV, and PDF output shared by sync and async flows. Include period/team/tool/user filters with RBAC.

### Dependencies

TASK-USG-002, TASK-PLT-002

### Estimated Complexity

**L**

### Definition of Done

- [ ] Renderers produce valid CSV/PDF for sample datasets
- [ ] Query layer uses aggregates tables for standard reports
- [ ] Finance Viewer read-only enforced

**FR:** FR-RPT-007 · **NFR:** NFR-PER-002

---

## TASK-RPT-002: Sync and Async Report API

### Description

Implement `POST /reports/generate`, `GET /reports/jobs/{jobId}`, `GET /reports/jobs/{jobId}/download` with sync path ≤10s and async queue for large reports.

### Dependencies

TASK-RPT-001, TASK-ING-001, TASK-INF-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] Async jobs store artifacts in object storage with presigned download
- [ ] In-app notification on async completion
- [ ] OpenAPI response codes 200/202 implemented
- [ ] FR-RPT-007 acceptance criteria pass

**FR:** FR-RPT-007

---

## TASK-RPT-003: Report Type Implementations

### Description

Implement six report types: tool usage summary, team usage, cost, user usage, alert history, API key activity — each matching FR-RPT-001 through FR-RPT-006 filters.

### Dependencies

TASK-RPT-001, TASK-PLT-004, TASK-ADM-003

### Estimated Complexity

**XL**

### Definition of Done

- [ ] Each report type has integration test with seeded data
- [ ] Cost report separates spend, allowance, overage
- [ ] API key activity report never exposes secret values
- [ ] All six FR-RPT-001–006 acceptance criteria addressed

**FR:** FR-RPT-001 – FR-RPT-006

---

## TASK-RPT-004: Scheduled Report Delivery (P1)

### Description

Implement `reporting.report_schedules` CRUD and Celery Beat task `reports.run_scheduled_report` emailing CSV/PDF to configured recipients in org timezone.

### Dependencies

TASK-RPT-002, TASK-NTF-004, TASK-PLT-006

### Estimated Complexity

**L**

### Definition of Done

- [ ] Schedule fires per cron in organization timezone
- [ ] Email contains correct attachment for RBAC-visible data
- [ ] FR-RPT-007 scheduled delivery acceptance criteria pass

**FR:** FR-RPT-007 (P1)
