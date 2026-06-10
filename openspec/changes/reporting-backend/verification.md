# Verification Plan: Reporting Backend

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### reporting-schema

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Report jobs table | Migration creates report jobs schema | Given prior migrations, when 007_reporting runs, then reporting.report_jobs exists | `tests/integration/test_reporting_migration.py` | ☐ |
| Report jobs table | Job lifecycle status transitions | Given queued job, when worker completes, then status queued→processing→completed with timestamps | `tests/integration/test_report_jobs.py::test_job_lifecycle` | ☐ |
| Local artifact storage reference | Completed job stores storage key | Given completed CSV job, when inspected, then storage_key set and file exists locally | `tests/integration/test_report_storage.py::test_storage_key` | ☐ |

### report-rendering

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Aggregate-based report queries | Standard report uses aggregates | Given aggregates exist, when sync tool summary runs, then query hits usage_aggregates | `tests/integration/test_report_queries.py::test_uses_aggregates` | ☐ |
| RBAC-scoped report data | Team Admin team filter | Given TA on T1 T2, when team_usage runs, then only T1 T2 data | `tests/integration/test_report_rbac.py::test_team_admin_filter` | ☐ |
| RBAC-scoped report data | Team Member user usage personal scope | Given TM, when user_usage without user_id, then personal rows only | `tests/integration/test_report_rbac.py::test_team_member_scope` | ☐ |
| RBAC-scoped report data | Finance Viewer read-only | Given FV, when report generated, then read-only success | `tests/integration/test_report_rbac.py::test_finance_viewer` | ☐ |
| Tool usage summary report | Tool usage summary for period | Given multi-tool usage, when tool_usage_summary, then tokens and share per tool | `tests/integration/test_report_types.py::test_tool_usage_summary` | ☐ |
| Team usage report | Team usage rows include cost metrics | Given team aggregates, when team_usage, then tokens utilization cost columns | `tests/integration/test_report_types.py::test_team_usage` | ☐ |
| Cost report | Cost columns populated | Given cost data, when cost report, then spend allowance overage separate | `tests/integration/test_report_types.py::test_cost_report` | ☐ |
| User usage report | User rows for authorized scope | Given filters in scope, when user_usage, then user token and cost rows | `tests/integration/test_report_types.py::test_user_usage` | ☐ |
| Alert history report | Alerts listed chronologically | Given alerts in period, when alert_history, then chronological severity status | `tests/integration/test_report_types.py::test_alert_history` | ☐ |
| API key activity report | No secret values in output | Given credential audit events, when api_key_activity, then no full secrets in output | `tests/integration/test_report_types.py::test_api_key_no_secrets` | ☐ |
| Multi-format rendering | Valid CSV export | Given csv format sync, when complete, then text/csv parseable with headers | `tests/integration/test_report_renderers.py::test_csv_valid` | ☐ |
| Multi-format rendering | Valid PDF export | Given pdf format sync, when complete, then application/pdf valid binary | `tests/integration/test_report_renderers.py::test_pdf_valid` | ☐ |

### report-delivery-api

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Synchronous report generation | Sync JSON report within budget | Given standard dataset async false json, when POST generate, then 200 within 10s | `tests/integration/test_report_api_sync.py::test_sync_json` | ☐ |
| Synchronous report generation | Sync CSV download | Given async false csv, when POST generate, then 200 text/csv | `tests/integration/test_report_api_sync.py::test_sync_csv` | ☐ |
| Asynchronous report generation | Async job queued | Given async true, when POST generate, then 202 with job_id queued | `tests/integration/test_report_api_async.py::test_async_queued` | ☐ |
| Asynchronous report generation | Async job completes with artifact | Given queued job, when worker runs, then completed with local artifact | `tests/integration/test_report_api_async.py::test_async_completes` | ☐ |
| Report job status | Poll job until completed | Given completed job, when GET jobs/{id}, then status completed with download path | `tests/integration/test_report_api_jobs.py::test_poll_completed` | ☐ |
| Report job status | Job not found for other org | Given other org job id, when GET jobs/{id}, then 404 | `tests/integration/test_report_api_jobs.py::test_cross_org_404` | ☐ |
| Report artifact download | Download completed report | Given completed job, when GET download, then file returned correct content type | `tests/integration/test_report_api_download.py::test_download_success` | ☐ |
| Report artifact download | Download before completion rejected | Given queued job, when GET download, then 409 Problem Details | `tests/integration/test_report_api_download.py::test_download_not_ready` | ☐ |
| Exported data respects RBAC | Unauthorized team filter denied | Given TA not on team T, when generate with team_id T, then 403 | `tests/integration/test_report_rbac.py::test_forbidden_team_filter` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| S3 presigned URL implementation | Implement S3 despite ADR-013 | Code review + ADR-017; local path integration test |
| Secret leakage in API key report | Include secret_ciphertext in CSV | Assert output grep for no raw secret patterns |
| Sync path scans usage_events | Slow query missing 10s budget | SQL log assertion uses aggregates table |
| Wrong ReportType enum strings | Use `tool-usage` vs `tool_usage_summary` | Contract test against OpenAPI enum |
| PDF response as JSON base64 | Wrong content-type | Assert Content-Type application/pdf |
| Cross-org job download | Allow download by job uuid only | Cross-org 404 tests on status and download |
| Missing reports Celery queue | Task on default queue | Assert task routed to `reports` queue |
| storage_key absolute path | Store full host path breaking portability | Unit test storage_key is relative under reports/ |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-004 | Celery reports queue | Worker integration test consumes reports queue |
| ADR-008 | Aggregate read model | `test_uses_aggregates` passes |
| ADR-013 | Local volume storage | Artifact file on mounted volume in Compose test |
| ADR-017 | storage_key + API download not S3 | `test_storage_key` + download test without S3 mocks |
| ADR-005 | RBAC | RBAC integration test suite passes |
| ADR-012 | OpenAPI contract | Schema validation on ReportJob and generate responses |

---

## 4. Evidence Requirements

### Functional

- [ ] All 24 Spec Alignment scenarios — pytest output per row
- [ ] Perf smoke: sync report ≤10s — `tests/performance/test_report_perf.py`

### Structural

- [ ] Code review confirms six report type modules and shared engine
- [ ] ADR-017 local storage implementation verified

### Edge Case

- [ ] API key report output scanned for secrets
- [ ] Download 409 before job complete
- [ ] Auto-async fallback when sync exceeds threshold (if implemented)

---

## 5. Evidence Log

| Scenario | Evidence Type | Location / Link | Collected By | Date |
|----------|---------------|-----------------|--------------|------|
| _TBD_ | _TBD_ | _TBD_ | | |

---

## 6. Audit Record

- [ ] All Spec Alignment rows pass with evidence
- [ ] Evidence Log complete
- [ ] Hallucination mitigations confirmed
- [ ] ADR compliance confirmed
- [ ] Scope excludes scheduled reports (RPT-004)

**Reviewer:** _______________  
**Date:** _______________
