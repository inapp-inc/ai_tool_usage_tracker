# Proposal: Reporting Backend

## Why

Finance and operations stakeholders need exportable reports (tool usage, team usage, cost, user usage, alert history, API key activity) beyond dashboard widgets. FR-RPT-001 through FR-RPT-007 require a report rendering engine, CSV/PDF export, sync generation within **10 seconds**, and async Celery jobs for large reports. OpenAPI defines `POST /reports/generate` and job polling/download endpoints — none are implemented.

This change delivers the **reporting backend**: `reporting.report_jobs` schema, shared query/render pipeline, six report types, sync/async API, and local-volume artifact storage per ADR-013.

## What Changes

- Add Alembic migration `007_reporting`: `reporting.report_jobs` (Phase 1; `report_schedules` deferred to TASK-RPT-004).
- Implement report rendering engine (TASK-RPT-001): JSON, CSV, PDF renderers; RBAC-scoped queries against `usage.usage_aggregates` and supporting tables.
- Implement six report types (TASK-RPT-003): `tool_usage_summary`, `team_usage`, `cost`, `user_usage`, `alert_history`, `api_key_activity`.
- Implement report API (TASK-RPT-002):
  - `POST /api/v1/reports/generate` — sync 200 or async 202
  - `GET /api/v1/reports/jobs/{jobId}` — job status
  - `GET /api/v1/reports/jobs/{jobId}/download` — download from local storage
- Add Celery task `reports.generate_async` on `reports` queue writing artifacts to `LOCAL_STORAGE_ROOT/reports/`.
- Store artifact path in `report_jobs.storage_key` (local path; not S3).
- Hook async completion notification (in-app `report_ready` stub until TASK-NTF-003).
- Integration tests per report type; perf smoke for sync ≤10s on standard dataset.

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `reporting-schema` | PostgreSQL `reporting.report_jobs` migration and repository |
| `report-rendering` | Query layer, RBAC filters, JSON/CSV/PDF renderers, six report type implementations |
| `report-delivery-api` | Sync/async generate API, Celery worker, local artifact download |

### Modified Capabilities

None — FR-RPT-* requirements exist in `openspec/requirements/04-reporting.md`. OpenAPI download description adapted operationally to local storage (ADR-013); no requirement text change.

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/reporting/` bounded context |
| **Database** | `reporting.report_jobs` table |
| **Storage** | PDF/CSV under `/var/lib/ai-tracker/storage/reports/{org_id}/{job_id}/` |
| **Celery** | New `reports` queue task for async generation |
| **API** | 3 report endpoints under `/api/v1/reports` |
| **Dependencies** | Auth/RBAC, usage aggregates from [usage-collector-backend](../usage-collector-backend/proposal.md) / USG-002, teams, tools, alerts, audit log |
| **Tests** | Per-type integration tests, async job flow, RBAC, no-secret leak test |
| **Downstream** | Unblocks TASK-UI-005, E2E-005, TASK-RPT-004 (schedules) |

## Usage collector dependency (FR-ING-004)

Report queries use the same aggregate read model as dashboards. Scheduled **hourly/daily collector runs** keep cost and usage reports current without manual CSV uploads. Report integration tests SHOULD use collector-populated aggregate fixtures.

## Open Questions

1. **Scheduled reports (FR-RPT-007 P1):** **Out of scope** — TASK-RPT-004 separate change.
2. **OpenAPI presigned S3 URL:** **Assumption:** implement local download URL/token; update OpenAPI `download_url` description in implementation task.
3. **PDF library:** **Assumption:** WeasyPrint or ReportLab for PDF generation in worker container.
4. **P1 report types:** `alert_history` and `api_key_activity` included in scope (FR-RPT-005/006 P1) with test fixtures.
5. **Aggregation dependency:** Same as dashboard — aggregates populated by file ingest or **usage collector** (FR-ING-004).
