# Tasks: In-App Alert Notifications

## 1. Backend

- [ ] 1.1 Add `notification_channel` column to `notifications.alerts` (migration); enum: `inapp | email | inapp_and_email`; default `inapp`
- [ ] 1.2 Update `ThresholdCreateRequest` / `ThresholdUpdateRequest` schemas — add `notification_channel` enum field
- [ ] 1.3 Remove email-address field from threshold create request (channel `inapp` requires no email)
- [ ] 1.4 Update threshold evaluator: when channel includes `inapp`, create `Notification` records for all scoped recipients
- [ ] 1.5 Implement recipient resolution: `team` scope → team members; `org` scope → all users; `user` scope → single user
- [ ] 1.6 Implement `POST /api/v1/notifications/read-all` endpoint
- [ ] 1.7 Update OpenAPI spec: `notification_channel` on threshold schemas, `/notifications/read-all` path

## 2. Frontend

- [ ] 2.1 Create `NotificationBell.tsx` component in app header
- [ ] 2.2 Badge: fetch `GET /notifications/unread-count` on mount; poll every 60 s
- [ ] 2.3 Popover: fetch `GET /notifications?unread_only=true&limit=5` on open
- [ ] 2.4 Notification item: display title, body snippet, relative timestamp; click → navigate to `deep_link` + mark read
- [ ] 2.5 "Mark all read" button → `POST /notifications/read-all`; refresh badge
- [ ] 2.6 Update Alerts/Threshold form: replace email channel dropdown with `CHANNEL_OPTIONS` (`inapp`, `email`, `inapp_and_email`)
- [ ] 2.7 Default channel to `inapp`; hide email address field when channel is `inapp`
- [ ] 2.8 Create `frontend/src/api/notifications.ts` — `fetchUnreadCount`, `fetchNotifications`, `markRead`, `markAllRead`

## 3. Tests

- [ ] 3.1 Backend: threshold breach with `inapp` channel creates notification records for scoped users
- [ ] 3.2 Backend: `read-all` endpoint marks all unread as read; returns correct count
- [ ] 3.3 Backend: unread-count decreases after mark-all-read
- [ ] 3.4 Frontend: bell badge shows unread count; disappears after mark-all-read
- [ ] 3.5 Frontend: channel dropdown defaults to "In-App Notification"; email field hidden
