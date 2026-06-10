# Threshold Evaluation — Delta Specification

## ADDED Requirements

### Requirement: Threshold evaluation against usage aggregates

The system SHALL evaluate active thresholds against current usage aggregates on a scheduled hourly cycle and after usage aggregate refresh per FR-NTF-003.

#### Scenario: Warning threshold breach creates alert

- **GIVEN** an active warning threshold and usage exceeding the limit
- **WHEN** evaluation runs
- **THEN** an alert record is created with severity `warning`, `current_value`, and `limit_value`

#### Scenario: Critical breach triggers notification pipeline

- **GIVEN** an active critical threshold breached
- **WHEN** evaluation completes
- **THEN** in-app notifications are created for authorized recipients
- **AND** email delivery is enqueued when `notify_email` is true

#### Scenario: No duplicate active alerts

- **GIVEN** an existing active alert for a threshold in the current evaluation period
- **WHEN** evaluation runs again without usage dropping below the limit
- **THEN** no additional active alert is created for that threshold period

#### Scenario: Alert resolved when usage drops below limit

- **GIVEN** an active alert and usage falling below the threshold limit
- **WHEN** evaluation runs
- **THEN** alert status becomes `resolved`
- **AND** `resolved_at` is populated
