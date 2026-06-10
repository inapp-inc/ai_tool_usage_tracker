# Proposal: Notifications Backend

## Why

Threshold breaches, credential expiry, and async report completion require in-app and email notification delivery (Module 5, FR-NTF-001 – FR-NTF-003). The dashboard alerts widget and E2E-004 depend on active alert records and user notifications. OpenAPI defines `/notifications/*` and `/thresholds/*` endpoints — none are implemented.

This change delivers the **notifications backend**: threshold CRUD, evaluation engine, alert/notification persistence, notification center API, and email worker — unblocking TASK-UI-006, dashboard `/alerts` widget, and reporting completion hooks.

## What Changes

- Add Alembic migration `006_notifications`: `notifications.alerts`, `notifications.notifications` (thresholds assumed in `003_admin_core` or added if missing).
- Implement threshold management API (TASK-ADM-004): `GET/POST /thresholds`, `PATCH/DELETE /thresholds/{thresholdId}`.
- Implement threshold evaluation engine (TASK-NTF-001): Celery `alerts.evaluate_thresholds` on hourly Beat + post-usage-aggregate refresh hook; dedupe active alerts per period.
- Implement alert and in-app notification creation (TASK-NTF-002) with OpenAPI payload fields and deep links.
- Implement notification center API (TASK-NTF-003): `GET /notifications`, `GET /notifications/unread-count`, `POST /notifications/{id}/read`.
- Implement email notification worker (TASK-NTF-004): Celery `email` queue, SMTP via env config, retry with exponential backoff.
- RBAC scoping for thresholds, notifications, and email recipients.
- Integration tests for FR-NTF-001 – FR-NTF-003 and FR-ADM-004.

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `notifications-schema` | PostgreSQL `notifications.*` tables, models, repositories |
| `threshold-management` | Threshold CRUD API per FR-ADM-004 and OpenAPI `/thresholds` |
| `threshold-evaluation` | Celery evaluation engine, alert lifecycle, deduplication |
| `notification-center-api` | In-app notification list, unread count, mark-read |
| `email-delivery` | SMTP email worker for critical alerts and credential expiry reminders |

### Modified Capabilities

None — requirements exist in `openspec/requirements/05-notifications.md` and `01-administration.md` (FR-ADM-004).

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/notifications/` bounded context; extend `admin/` for thresholds |
| **Database** | `notifications.alerts`, `notifications.notifications`; uses `admin.thresholds` |
| **Celery** | `alerts` and `email` queue tasks; Beat schedule for hourly evaluation |
| **API** | 3 notification + 4 threshold endpoints under `/api/v1` |
| **Dependencies** | Auth/RBAC, usage aggregates from [usage-collector-backend](../usage-collector-backend/proposal.md) / USG-002, teams/tools, credentials |
| **Tests** | Evaluation dedupe, RBAC, notification payload, email retry mocks |
| **Downstream** | Unblocks dashboard alerts widget, E2E-004, TASK-UI-006, report_ready notifications |

## Usage collector dependency (FR-ING-004)

Threshold evaluation compares usage aggregates to configured limits. The collector module triggers **aggregate refresh and evaluation hooks** after each successful vendor API collection. Evaluation integration tests should invoke the post-collection hook or seed collector-sourced aggregates.

## Open Questions

1. **Threshold migration:** If `admin.thresholds` not yet migrated, **bundle** into this change as part of threshold-management.
2. **SMTP vs SES:** Phase 1 uses **SMTP** from `.env` per ADR-013 (not AWS SES). **Assumption:** document `SMTP_*` settings.
3. **Post-ingestion trigger:** Hook from usage aggregation refresh and **[usage-collector-backend](../usage-collector-backend/proposal.md)** post-collection; stub callable until then.
4. **Acknowledge alert API:** Not in OpenAPI Phase 1 — resolved via evaluation only; acknowledge columns populated if added later.
5. **Warning email opt-out:** Respect `notify_email` and threshold severity per NFR-CMP-004.
