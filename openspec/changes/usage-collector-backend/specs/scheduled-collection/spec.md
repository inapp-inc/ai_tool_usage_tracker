# Scheduled Collection — Delta Specification

## ADDED Requirements

### Requirement: Hourly scheduled collection

The system SHALL run collectors configured with `schedule: hourly` at least once per hour via Celery Beat.

#### Scenario: Hourly collector executes

- **GIVEN** an active collector with hourly schedule
- **WHEN** the hourly Beat tick fires
- **THEN** `ingestion.collect_usage` is enqueued for that collector
- **AND** `last_run_at` is updated on the config

### Requirement: Daily scheduled collection

The system SHALL run collectors configured with `schedule: daily` once per calendar day.

#### Scenario: Daily collector executes

- **GIVEN** an active collector with daily schedule
- **WHEN** the daily Beat schedule fires
- **THEN** collection runs for the prior period
- **AND** usage is ingested without duplicate vendor events

### Requirement: Inactive collector skipped

The system SHALL NOT schedule collection for configs with `active: false`.

#### Scenario: Disabled collector not run

- **GIVEN** a collector with `active: false`
- **WHEN** Beat schedules are evaluated
- **THEN** no collection task is enqueued for that collector
