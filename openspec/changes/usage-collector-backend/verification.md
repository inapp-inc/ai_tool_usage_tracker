# Verification Plan: Usage Collector Backend

---

## 1. Spec Alignment

### collector-schema

| Req ID | Scenario | Verification Artifact | Status |
|--------|----------|----------------------|--------|
| Collector configuration persistence | Collector config migration applies | `tests/integration/test_collector_migration.py` | ☐ |
| Collector configuration persistence | Schedule enum validation | `tests/integration/test_collector_migration.py::test_schedule_enum` | ☐ |
| Collector run history | Successful run recorded | `tests/integration/test_collector_runs.py::test_success` | ☐ |
| Collector run history | Failed run stores error without secrets | `tests/integration/test_collector_runs.py::test_failure_no_secret` | ☐ |

### provider-connect-api

| Req ID | Scenario | Verification Artifact | Status |
|--------|----------|----------------------|--------|
| Provider-managed connect flow | Connect with new API token | `tests/integration/test_collectors_api.py::test_connect_token` | ☐ |
| Provider-managed connect flow | Connect using existing credential | `tests/integration/test_collectors_api.py::test_connect_credential_id` | ☐ |
| Provider-managed connect flow | Team Admin forbidden on non-administered team | `tests/integration/test_collectors_api.py::test_ta_forbidden` | ☐ |
| Manage collector configuration | Update schedule to daily | `tests/integration/test_collectors_api.py::test_patch_schedule` | ☐ |
| Manage collector configuration | On-demand collection run | `tests/integration/test_collectors_api.py::test_run_now` | ☐ |
| Manage collector configuration | List collectors for organization | `tests/integration/test_collectors_api.py::test_list` | ☐ |

### vendor-collector-adapters

| Req ID | Scenario | Verification Artifact | Status |
|--------|----------|----------------------|--------|
| Vendor API usage fetch | OpenAI usage normalized | `tests/integration/test_collector_adapters.py::test_openai` | ☐ |
| Vendor API usage fetch | Idempotent vendor event ingestion | `tests/integration/test_collector_adapters.py::test_idempotent` | ☐ |
| Post-collection pipeline hooks | Aggregates refresh after collection | `tests/integration/test_collector_pipeline.py::test_aggregate_hook` | ☐ |

### scheduled-collection

| Req ID | Scenario | Verification Artifact | Status |
|--------|----------|----------------------|--------|
| Hourly scheduled collection | Hourly collector executes | `tests/integration/test_collector_schedule.py::test_hourly` | ☐ |
| Daily scheduled collection | Daily collector executes | `tests/integration/test_collector_schedule.py::test_daily` | ☐ |
| Inactive collector skipped | Disabled collector not run | `tests/integration/test_collector_schedule.py::test_inactive_skipped` | ☐ |

---

## 2. Hallucination Risk Register

| Risk | Mitigation |
|------|------------|
| Token returned in API response | Assert connect response has no api_token field |
| Plaintext credential in logs | Failure test grep for token pattern |
| Wrong schedule enum | DB + API validation tests |
| Missing aggregate refresh hook | Pipeline integration test |
| Adapter not using idempotency | Duplicate vendor id test |

---

## 3. Pattern & ADR Compliance

| ADR | Verification |
|-----|--------------|
| ADR-011 | Adapter protocol unit tests |
| ADR-015 | TA forbidden team connect test |
| ADR-019 | Hourly/daily schedule tests + connect API |

---

## 4. Evidence Requirements

- [ ] All 16 scenarios — pytest output
- [ ] OpenAPI Collectors tag lint clean

---

## 5. Evidence Log

| Scenario | Evidence | Collected By | Date |
|----------|----------|--------------|------|
| _TBD_ | _TBD_ | | |

---

## 6. Audit Record

- [ ] All scenarios pass
- [ ] Evidence Log complete

**Reviewer:** _______________ **Date:** _______________
