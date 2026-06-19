# Tasks: In-App Alert Notifications

## 1. Backend

- [x] 1.1 Migration `024_in_app_notifications` — create `notifications.notifications` table
- [x] 1.2 Use existing `notify_in_app` / `notify_email` flags on `admin.thresholds` (default in-app only)
- [x] 1.3 Threshold evaluator creates `ThresholdEvent` + in-app rows when breach detected
- [x] 1.4 Recipient resolution: org → admins; team → team admins + super admins; user → target user
- [x] 1.5 `GET /api/v1/notifications`, `GET /unread-count`, `POST /{id}/read`, `POST /read-all`
- [x] 1.6 Evaluator runs after successful collector sync (usage ingest)
- [ ] 1.7 Email delivery (unchanged / future)

## 2. Frontend

- [x] 2.1 `NotificationBell.tsx` in app header with unread badge
- [x] 2.2 Poll `GET /notifications/unread-count` every 60 s
- [x] 2.3 Popover lists 5 recent unread on open
- [x] 2.4 Click item → navigate to alert history + mark read
- [x] 2.5 "Mark all read" → `POST /notifications/read-all`
- [x] 2.6 Alerts form channel: In-App / Email / In-App + Email (webhook removed)
- [x] 2.7 Default channel `in_app`; hide email field when in-app only
- [x] 2.8 `frontend/src/api/notifications.ts`

## 3. Tests

- [x] 3.1 Backend: breach creates notification records for scoped users
- [x] 3.2 Backend: read-all marks unread and returns count
- [ ] 3.3 Frontend component tests (optional)

## Notes

- Webhook channel removed from Alerts UI; `webhook_url` column retained for backward compatibility but always cleared on save.
- Full notifications inbox page remains out of scope (header popover only).
