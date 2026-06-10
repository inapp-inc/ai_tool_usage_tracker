# ADR-018: Phase 1 SMTP Email Delivery

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

FR-NTF-002 requires email notifications for critical threshold breaches and credential expiry reminders. Original NFR references may imply cloud email services (SES). ADR-013 mandates Phase 1 deployment on Docker Compose with secrets from host `.env` — no AWS SES dependency.

---

## Decision

Deliver Phase 1 email via **SMTP** configured through environment variables:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`
- Celery `email` queue task sends multipart HTML/text messages
- Retry with exponential backoff (max 5 attempts) on transient failures
- Development may use `EMAIL_BACKEND=log` to write messages to structured logs instead of SMTP

Critical alert emails MUST be enqueued when threshold `notify_email=true` and severity is `critical`. Warning emails respect per-threshold `notify_email` flag.

---

## Consequences

### Positive

- Works with corporate SMTP relays and local dev tools (Mailhog, Mailpit).
- Aligns with ADR-013 self-hosted Compose model.
- No cloud vendor lock-in for MVP.

### Negative

- Deliverability and reputation management are operator responsibility.
- No built-in bounce handling in Phase 1.

### Neutral

- SES or SendGrid adapter can supersede in Phase 2 via new ADR.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **AWS SES (Phase 1)** | Contradicts ADR-013 |
| **In-app only** | Violates FR-NTF-002 P0 |
| **Synchronous send in API** | Blocks requests; violates async worker pattern ADR-004 |

**Supersedes:** None  
**Superseded by:** None  
**Related:** ADR-004, ADR-013, FR-NTF-002
