# Tasks: Notifications Backend

Reference [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md).

---

## 1. Schema (notifications-schema spec)

- [ ] 1.1 Ensure `admin.thresholds` migration exists (bundle in change if missing)
- [ ] 1.2 Create Alembic revision `006_notifications`: `notifications.alerts`, `notifications.notifications`
- [ ] 1.3 Add unique partial index `uq_active_alert_period` and notification indexes
- [ ] 1.4 Implement SQLAlchemy models and repositories for Alert, Notification, Threshold

## 2. Threshold management (threshold-management spec)

- [ ] 2.1 Create `backend/app/admin/thresholds/` router, service, schemas
- [ ] 2.2 Implement `GET/POST /api/v1/thresholds` with cursor pagination
- [ ] 2.3 Implement `PATCH/DELETE /api/v1/thresholds/{thresholdId}`
- [ ] 2.4 Enforce scope CHECK validation and Team Admin scope per ADR-015
- [ ] 2.5 Reject utilization percentage outside 0–100 at API layer

## 3. Evaluation engine (threshold-evaluation spec)

- [ ] 3.1 Implement `evaluation/engine.py` — compare aggregates to active thresholds
- [ ] 3.2 Implement alert create, update current_value, resolve lifecycle
- [ ] 3.3 Implement dedupe via unique constraint handling
- [ ] 3.4 Add Celery task `alerts.evaluate_thresholds` on `alerts` queue
- [ ] 3.5 Register hourly Beat schedule; export `trigger_for_org` hook for USG-002

## 4. Notification fan-out (notification-center-api / NTF-002)

- [ ] 4.1 Implement `AlertService.fan_out_notifications` with recipient resolution
- [ ] 4.2 Build OpenAPI-aligned notification payload and deep links
- [ ] 4.3 Support notification types: `threshold_breach`, `credential_expiry`, `report_ready` stubs

## 5. Notification center API (notification-center-api spec)

- [ ] 5.1 Register router at `/api/v1/notifications`
- [ ] 5.2 Implement `GET /notifications` with `unread_only` and cursor pagination
- [ ] 5.3 Implement `GET /notifications/unread-count`
- [ ] 5.4 Implement `POST /notifications/{notificationId}/read`
- [ ] 5.5 Filter all queries by `user_id = current_user` and RBAC scope

## 6. Email delivery (email-delivery spec)

- [ ] 6.1 Implement SMTP client and Jinja2 templates per ADR-018
- [ ] 6.2 Add Celery task `notifications.send_email` on `email` queue with retry/backoff
- [ ] 6.3 Wire critical alert and credential expiry emails from evaluation/credential jobs
- [ ] 6.4 Add `EMAIL_BACKEND=log` for development; document `SMTP_*` in `.env.example`
- [ ] 6.5 Ensure logs never contain SMTP passwords or credential secrets

## 7. Celery and compose

- [ ] 7.1 Add `alerts` and `email` queues to worker routing (INF-003)
- [ ] 7.2 Verify Beat container runs evaluation schedule without duplicate execution

## 8. Test fixtures

- [ ] 8.1 Create `tests/fixtures/notifications_seed.sql` — thresholds, aggregates, users by role
- [ ] 8.2 Add pytest helpers for evaluation task invocation and email task mocks

## 9. Tests — schema and thresholds

- [ ] 9.1 `tests/integration/test_notifications_migration.py`
- [ ] 9.2 `tests/integration/test_alerts_repository.py::test_dedupe_constraint`
- [ ] 9.3 `tests/integration/test_notifications_repository.py::test_payload`
- [ ] 9.4 `tests/integration/test_thresholds_api.py` — all five threshold scenarios

## 10. Tests — evaluation and API

- [ ] 10.1 `tests/integration/test_threshold_evaluation.py` — four evaluation scenarios
- [ ] 10.2 `tests/integration/test_notifications_api.py` — six notification API scenarios

## 11. Tests — email

- [ ] 11.1 `tests/integration/test_email_tasks.py` — four email scenarios

## 12. Documentation

- [ ] 12.1 Update README with threshold and notification API examples
- [ ] 12.2 Document SMTP configuration and dev log backend

## 13. Verification & Evidence

- [ ] 13.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 13.2 Collect functional evidence for each scenario — populate verification.md § Evidence Log
- [ ] 13.3 Confirm Hallucination Risk mitigations in verification.md § Hallucination Risk Register
- [ ] 13.4 Confirm ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 13.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer)
- [ ] 13.6 Run `openspec validate notifications-backend --type change --strict` before archive
