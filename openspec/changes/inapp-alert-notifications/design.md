# Design: In-App Alert Notifications

## Backend Changes

### 1. Threshold notification flags (existing columns)

No new DB column. Frontend channel maps to `notify_in_app` and `notify_email` on `admin.thresholds`:

```yaml
# Effective mapping from UI channel
in_app:            { notify_in_app: true,  notify_email: false }
email:             { notify_in_app: false, notify_email: true }
in_app_and_email:  { notify_in_app: true,  notify_email: true }
```

Default on create: `notify_in_app=true`, `notify_email=false`. `webhook_url` is cleared on save.

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
  { value: "in_app",            label: "In-App Notification" },
  { value: "email",             label: "Email" },
  { value: "in_app_and_email",  label: "In-App + Email" },
];
```

Default: `in_app`. Webhook URL field removed.

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
