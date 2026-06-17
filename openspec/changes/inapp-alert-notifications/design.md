# Design: In-App Alert Notifications

## Backend Changes

### 1. Threshold `notification_channel` field

Add `inapp` to the allowed `notification_channel` enum on thresholds:

```sql
-- Existing: email | slack | webhook
-- New values: inapp | inapp_and_email
ALTER TABLE notifications.alerts
  ADD COLUMN notification_channel VARCHAR(32) NOT NULL DEFAULT 'inapp';
```

OpenAPI `ThresholdCreateRequest` / `ThresholdUpdateRequest` schema:

```yaml
notification_channel:
  type: string
  enum: [inapp, email, inapp_and_email]
  default: inapp
```

### 2. Threshold evaluator — create notification record

When a threshold breach occurs and `notification_channel` includes `inapp`:

```python
async def notify_inapp(session, threshold, breach_value):
    # Resolve recipient user IDs based on threshold scope
    for user_id in resolve_recipients(threshold):
        session.add(Notification(
            user_id=user_id,
            title=f"Alert: {threshold.name}",
            body=f"{breach_value} exceeded limit of {threshold.limit_value}",
            deep_link=f"/alerts/{threshold.id}",
            source_type="threshold_breach",
            source_id=str(threshold.id),
            read=False,
        ))
    await session.commit()
```

### 3. `GET /api/v1/notifications/unread-count` (already spec'd)

Returns `{ unread_count: integer }` for the current user. Used by header bell polling.

---

## Frontend Changes

### Header bell component (`NotificationBell.tsx`)

```
AppHeader
  └── NotificationBell
        ├── IconButton + Badge (unread count)
        └── Popover
              ├── NotificationItem × N (max 5)
              └── "Mark all read" button
```

**Data fetching:**
- On mount: `GET /api/v1/notifications/unread-count` (sets badge)
- Poll every 60 seconds with `useQuery({ refetchInterval: 60_000 })`
- On popover open: `GET /api/v1/notifications?unread_only=true&limit=5`
- On "Mark all read": `POST /api/v1/notifications/read-all` (new endpoint) or loop mark-read

### Notification item display

```
[icon]  Alert: OpenAI token usage exceeded 90%
        Team: Data Science · 2 min ago
```

Clicking an item: navigates to `deep_link`, marks notification read.

### Alert form — Notification Channel dropdown

`AlertsPage.tsx` (or `ThresholdsPage.tsx`): update channel dropdown options:

```ts
const CHANNEL_OPTIONS = [
  { value: "inapp",          label: "In-App Notification" },
  { value: "email",          label: "Email" },
  { value: "inapp_and_email", label: "In-App + Email" },
];
```

Default: `inapp`.

Remove any previous free-text email address field when channel is `inapp`.

---

## New API Endpoint

### `POST /api/v1/notifications/read-all`

Marks all unread notifications for the current user as read.

```yaml
path: /notifications/read-all
method: POST
auth: Bearer JWT
responses:
  200: { marked_read: integer }
```

---

## Polling Strategy

| Action | Endpoint | Interval |
|--------|----------|----------|
| Badge count | `GET /notifications/unread-count` | Every 60 s |
| Popover list | `GET /notifications?unread_only=true&limit=5` | On popover open only |
| Mark read | `POST /notifications/{id}/read` | On click |
| Mark all read | `POST /notifications/read-all` | On button click |
