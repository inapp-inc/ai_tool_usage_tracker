# Tasks: Reporting Backend

Reference [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md). Depends on auth, usage aggregates, and admin schema.

---

## 1. Schema and storage (reporting-schema spec)

- [ ] 1.1 Create Alembic revision `007_reporting`: `reporting.report_jobs` with status, filters JSONB, storage_key
- [ ] 1.2 Implement `ReportJobRepository` and SQLAlchemy model
- [ ] 1.3 Implement `LocalReportStorage` — write/read under `LOCAL_STORAGE_ROOT/reports/{org_id}/{job_id}/`
- [ ] 1.4 Update OpenAPI download description for local API streaming (ADR-017)

## 2. Report engine scaffold (report-rendering spec)

- [ ] 2.1 Create `backend/app/reporting/` package per design.md
- [ ] 2.2 Implement shared `ReportScopeResolver` (reuse or extract from dashboard scope)
- [ ] 2.3 Implement aggregate query helpers in `engine/queries/`
- [ ] 2.4 Implement JSON, CSV, PDF renderers in `engine/renderers/`
- [ ] 2.5 Add WeasyPrint to worker Dockerfile dependencies for PDF

## 3. Report type implementations

- [ ] 3.1 `tool_usage_summary` handler (FR-RPT-001)
- [ ] 3.2 `team_usage` handler (FR-RPT-002)
- [ ] 3.3 `cost` handler — spend, allowance, overage columns (FR-RPT-003)
- [ ] 3.4 `user_usage` handler (FR-RPT-004)
- [ ] 3.5 `alert_history` handler — query notifications.alerts (FR-RPT-005)
- [ ] 3.6 `api_key_activity` handler — audit log only, masked ids (FR-RPT-006)

## 4. Celery async (report-delivery-api spec)

- [ ] 4.1 Add `reports` queue to Celery routing (INF-003 alignment)
- [ ] 4.2 Implement `reports.generate_async` task — update job status, write artifact, set storage_key
- [ ] 4.3 Implement sync/async threshold logic (10s budget, row count, async flag)
- [ ] 4.4 Add notification stub on job completion (`report_ready`)

## 5. Report API (report-delivery-api spec)

- [ ] 5.1 Register router at `/api/v1/reports`
- [ ] 5.2 Implement `POST /api/v1/reports/generate` — 200 sync / 202 async
- [ ] 5.3 Implement `GET /api/v1/reports/jobs/{jobId}` — ReportJob response
- [ ] 5.4 Implement `GET /api/v1/reports/jobs/{jobId}/download` — stream local file; 409 if not ready
- [ ] 5.5 Enforce job ownership and org isolation (404 cross-org)

## 6. Test fixtures

- [ ] 6.1 Create `tests/fixtures/reporting_seed.sql` — aggregates, tools, teams, alerts, audit events
- [ ] 6.2 Add pytest helpers for sync/async report requests per role

## 7. Tests — reporting-schema

- [ ] 7.1 `tests/integration/test_reporting_migration.py`
- [ ] 7.2 `tests/integration/test_report_jobs.py::test_job_lifecycle`
- [ ] 7.3 `tests/integration/test_report_storage.py::test_storage_key`

## 8. Tests — report-rendering

- [ ] 8.1 `tests/integration/test_report_queries.py::test_uses_aggregates`
- [ ] 8.2 `tests/integration/test_report_rbac.py` — TA, TM, FV, forbidden team
- [ ] 8.3 `tests/integration/test_report_types.py` — all six report types + no secrets
- [ ] 8.4 `tests/integration/test_report_renderers.py` — CSV and PDF validity

## 9. Tests — report-delivery-api

- [ ] 9.1 `tests/integration/test_report_api_sync.py`
- [ ] 9.2 `tests/integration/test_report_api_async.py`
- [ ] 9.3 `tests/integration/test_report_api_jobs.py`
- [ ] 9.4 `tests/integration/test_report_api_download.py`

## 10. Performance and documentation

- [ ] 10.1 `tests/performance/test_report_perf.py` — sync ≤10s on reference fixture
- [ ] 10.2 OpenAPI / Redocly lint after download description update
- [ ] 10.3 Update README with report generation examples

## 11. Verification & Evidence

- [ ] 11.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 11.2 Collect functional evidence for each scenario — populate verification.md § Evidence Log
- [ ] 11.3 Confirm Hallucination Risk mitigations in verification.md § Hallucination Risk Register
- [ ] 11.4 Confirm ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 11.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer)
- [ ] 11.6 Run `openspec validate reporting-backend --type change --strict` before archive
