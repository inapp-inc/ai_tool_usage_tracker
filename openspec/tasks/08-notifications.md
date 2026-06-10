# Notification Tasks

Threshold evaluation, in-app notifications, and email delivery.

---

## TASK-NTF-001: Threshold Evaluation Engine

### Description

Celery task `alerts.evaluate_thresholds` (hourly Beat + post-ingestion trigger) comparing aggregates to active thresholds; dedupe active alerts per period.

### Dependencies

TASK-ADM-004, TASK-USG-002, TASK-INF-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] Warning and critical severities create distinct alert records
- [ ] Resolved alerts when usage drops below limit
- [ ] No duplicate active alerts for same threshold period
- [ ] FR-NTF-003 acceptance criteria pass

**FR:** FR-NTF-003

---

## TASK-NTF-002: Alerts and In-App Notification Persistence

### Description

Create alert records and user notifications with payload (tool, team, threshold, current value, deep link) on threshold breach and other event types (report ready, credential expiry).

### Dependencies

TASK-DB-005, TASK-NTF-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Notification payload matches OpenAPI schema
- [ ] Deep links route to correct dashboard/report context
- [ ] Users only see notifications in RBAC scope

**FR:** FR-NTF-001

---

## TASK-NTF-003: Notification Center API

### Description

Implement `GET /notifications`, `GET /notifications/unread-count`, `POST /notifications/{id}/read` with cursor pagination.

### Dependencies

TASK-NTF-002, TASK-PLT-002

### Estimated Complexity

**S**

### Definition of Done

- [ ] Unread counter accurate after mark-read
- [ ] Pagination matches OpenAPI cursor pattern
- [ ] FR-NTF-001 acceptance criteria pass

**FR:** FR-NTF-001 · **OpenAPI:** `/notifications`

---

## TASK-NTF-004: Email Notification Worker

### Description

Celery `email` queue task sending SMTP/SES emails for critical alerts, credential expiry, scheduled reports; retry with backoff; no secrets in logs.

### Dependencies

TASK-NTF-001, TASK-ADM-003, TASK-INF-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] Critical alert email within 5 min p95 in staging test
- [ ] Warning email respects opt-out preference (NFR-CMP-004)
- [ ] Failed delivery logged and metric incremented
- [ ] FR-NTF-002 acceptance criteria pass

**FR:** FR-NTF-002 · **NFR:** NFR-PER-005, NFR-CMP-004
