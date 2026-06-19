# Proposal: In-App Alert Notifications

**Status:** 🚧 In progress

## Why

When a usage threshold is breached, administrators want alert notifications in the application header — a notification bell with unread count and recent items — without requiring webhook or email setup.

## What Changes (this slice)

### 1. Notification channel: In-App (no webhook)

The Alerts form **removes Webhook**. Channel options map to existing threshold flags:

| UI value | `notify_in_app` | `notify_email` | Behaviour |
|----------|-----------------|----------------|-----------|
| `in_app` | true | false | In-app notification only (default) |
| `email` | false | true | Email only (future SMTP) |
| `in_app_and_email` | true | true | Both |

### 2. Header notification bell

A notification bell icon appears in the app header for all authenticated users. It:
- Shows an unread count badge (from `GET /api/v1/notifications/unread-count`)
- Expands to a popover listing the 5 most recent unread notifications
- "Mark all read" action
- Link to full Notifications view (future)

### 3. Threshold evaluation → in-app notification record

When a threshold is breached and the channel includes `inapp`, the evaluator creates a `notifications.notifications` row for each user in scope (team members / org-level). The notification contains:
- `title`: e.g. "Alert: OpenAI token usage exceeded 90%"
- `body`: threshold name, current value, limit, team context
- `deep_link`: URL to the relevant dashboard or alert detail
- `source_type`: `threshold_breach`
- `source_id`: threshold UUID

### 4. Polling / refresh

The frontend polls `GET /api/v1/notifications/unread-count` every 60 seconds to update the badge. On notification popover open, it fetches `GET /api/v1/notifications?unread_only=true&limit=5`.

## Out of Scope

- Webhook notifications (removed from Alerts UI)
- WebSocket / push delivery (polling is sufficient for MVP)
- Full notifications inbox page (header popover only for this slice)
- Email delivery changes (existing email channel unchanged)
- Per-user notification preferences

## Dependencies

- Existing `notifications.notifications` table and `notification-center-api` spec
- Existing threshold evaluation engine (`notifications-backend` change)
- FR-NTF-001 (Notification Center)
- FR-ADM-004 (Threshold Management)
