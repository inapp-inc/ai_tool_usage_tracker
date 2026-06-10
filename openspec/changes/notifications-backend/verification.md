# Verification Plan: Notifications Backend

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### notifications-schema

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Notifications schema migration | Migration creates alerts and notifications tables | Given admin schema applied, when 006_notifications runs, then alerts and notifications tables exist | `tests/integration/test_notifications_migration.py` | ☐ |
| Active alert deduplication constraint | Active alert deduplication constraint | Given active alert for T period P, when duplicate insert, then constraint violation | `tests/integration/test_alerts_repository.py::test_dedupe_constraint` | ☐ |
| Notification payload storage | Notification payload storage | Given breach notification, when persisted, then payload JSONB has tool team threshold deep link | `tests/integration/test_notifications_repository.py::test_payload` | ☐ |

### threshold-management

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| List and create thresholds | Super Admin creates team-scoped threshold | Given SA valid create, then 201 persisted with scope columns | `tests/integration/test_thresholds_api.py::test_create_sa` | ☐ |
| List and create thresholds | Team Admin creates threshold for administered team | Given TA member of T, when create for T, then 201 | `tests/integration/test_thresholds_api.py::test_create_ta` | ☐ |
| List and create thresholds | Team Admin denied for other team | Given TA not on T, when create for T, then 403 | `tests/integration/test_thresholds_api.py::test_create_ta_forbidden` | ☐ |
| Update and delete thresholds | Update threshold limit | Given SA patches limit_value, then 200 updated | `tests/integration/test_thresholds_api.py::test_update` | ☐ |
| Update and delete thresholds | Utilization percentage validation | Given pct type limit > 100, then 422 | `tests/integration/test_thresholds_api.py::test_pct_validation` | ☐ |

### threshold-evaluation

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Threshold evaluation against usage aggregates | Warning threshold breach creates alert | Given warning threshold exceeded, when eval runs, then warning alert with values | `tests/integration/test_threshold_evaluation.py::test_warning_breach` | ☐ |
| Threshold evaluation against usage aggregates | Critical breach triggers notification pipeline | Given critical breach notify_email true, when eval, then in-app + email enqueued | `tests/integration/test_threshold_evaluation.py::test_critical_pipeline` | ☐ |
| Threshold evaluation against usage aggregates | No duplicate active alerts | Given existing active alert, when eval again, then no duplicate | `tests/integration/test_threshold_evaluation.py::test_no_duplicate` | ☐ |
| Threshold evaluation against usage aggregates | Alert resolved when usage drops below limit | Given usage below limit, when eval, then alert resolved with resolved_at | `tests/integration/test_threshold_evaluation.py::test_resolve` | ☐ |

### notification-center-api

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| List notifications for current user | List includes unread count | Given unread items, when GET /notifications, then data unread_count meta and deep_link fields | `tests/integration/test_notifications_api.py::test_list` | ☐ |
| List notifications for current user | Unread only filter | Given read+unread, when unread_only=true, then unread only | `tests/integration/test_notifications_api.py::test_unread_filter` | ☐ |
| Unread notification count | Unread count matches database | Given 3 unread, when GET unread-count, then unread_count=3 | `tests/integration/test_notifications_api.py::test_unread_count` | ☐ |
| Mark notification as read | Mark read decrements counter | Given unread, when POST read, then read true and count -1 | `tests/integration/test_notifications_api.py::test_mark_read` | ☐ |
| Mark notification as read | Cross-user notification not found | Given other user notification, when mark read, then 404 | `tests/integration/test_notifications_api.py::test_mark_read_404` | ☐ |
| RBAC notification visibility | User does not see out-of-scope notifications | Given alert for team T, when user without T access lists, then excluded | `tests/integration/test_notifications_api.py::test_scope_filter` | ☐ |

### email-delivery

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Critical alert email delivery | Critical alert email enqueued | Given critical breach notify_email true, when eval, then email task queued with required fields | `tests/integration/test_email_tasks.py::test_critical_enqueued` | ☐ |
| Critical alert email delivery | Warning email respects notify flag | Given warning notify_email false, when eval, then no email task | `tests/integration/test_email_tasks.py::test_warning_no_email` | ☐ |
| Credential expiry reminder email | Expiry reminder sent to administrators | Given credential near expiry, when job runs, then email to SA without secrets | `tests/integration/test_email_tasks.py::test_credential_reminder` | ☐ |
| Email delivery retry and failure logging | SMTP failure retried then logged | Given SMTP failure after retries, then logged without credentials | `tests/integration/test_email_tasks.py::test_retry_failure_logged` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| Evaluation queries raw events | Slow/wrong comparison | Assert SQL uses usage_aggregates in test |
| Duplicate alerts on re-eval | Missing unique constraint handling | test_no_duplicate + DB constraint test |
| Notification list returns all org users | Missing user_id filter | test_mark_read_404 + scope_filter |
| Email includes API key secret | Security leak | Assert email body grep in credential test |
| Wrong deep_link path | Broken frontend navigation | Assert deep_link prefix `/dashboard/alerts/` |
| SES instead of SMTP | ADR-013 violation | Code review smtp.py; ADR-018 compliance |
| Threshold scope columns | Mismatch scope vs FK | test_create with each scope type |
| Beat task name typo | Schedule never runs | Integration test invokes task directly |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-004 | alerts + email Celery queues | Task routing unit test |
| ADR-008 | Evaluation uses aggregates | SQL/log assertion in evaluation test |
| ADR-013 | SMTP from env not SES | ADR-018; no boto3 SES imports |
| ADR-015 | TA threshold scope | test_create_ta_forbidden |
| ADR-018 | SMTP retry and logging | test_retry_failure_logged |

---

## 4. Evidence Requirements

### Functional

- [ ] All 22 Spec Alignment scenarios — pytest output per row

### Structural

- [ ] Code review confirms package layout and evaluation dedupe logic
- [ ] ADR-018 SMTP implementation verified

### Edge Case

- [ ] No duplicate active alerts under repeated evaluation
- [ ] Email body contains no credential secrets
- [ ] Cross-user mark-read returns 404

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

**Reviewer:** _______________  
**Date:** _______________
