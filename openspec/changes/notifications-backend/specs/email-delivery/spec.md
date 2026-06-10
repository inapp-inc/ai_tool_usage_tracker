# Email Delivery — Delta Specification

## ADDED Requirements

### Requirement: Critical alert email delivery

The system SHALL send email for critical threshold breaches when `notify_email` is enabled per FR-NTF-002.

#### Scenario: Critical alert email enqueued

- **GIVEN** a critical threshold breach with `notify_email=true`
- **WHEN** evaluation creates the alert
- **THEN** an email task is queued on the `email` Celery queue
- **AND** the email body includes alert type, tool, team, threshold, current value, timestamp, and platform link

#### Scenario: Warning email respects notify flag

- **GIVEN** a warning threshold with `notify_email=false`
- **WHEN** evaluation creates a warning alert
- **THEN** no email task is enqueued

### Requirement: Credential expiry reminder email

The system SHALL send email reminders before API credential expiration per FR-NTF-002.

#### Scenario: Expiry reminder sent to administrators

- **GIVEN** a credential approaching its expiration reminder threshold
- **WHEN** the expiry check job runs
- **THEN** email is sent to designated Super Admin recipients
- **AND** full credential secrets are not included in the email

### Requirement: Email delivery retry and failure logging

The system SHALL retry failed email delivery with exponential backoff and log failures per FR-NTF-002.

#### Scenario: SMTP failure retried then logged

- **GIVEN** transient SMTP failure
- **WHEN** the email task runs with retries exhausted
- **THEN** failure is logged without SMTP credentials or secrets
- **AND** a failure metric or structured log entry is recorded for Super Admin review
