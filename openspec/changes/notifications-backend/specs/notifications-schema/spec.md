# Notifications Schema — Delta Specification

## ADDED Requirements

### Requirement: Notifications schema migration

The system SHALL persist alerts and in-app notifications in PostgreSQL schema `notifications` per [database.md](../../../specifications/database.md).

#### Scenario: Migration creates alerts and notifications tables

- **GIVEN** prior admin schema migrations applied
- **WHEN** Alembic migration `006_notifications` runs
- **THEN** tables `notifications.alerts` and `notifications.notifications` exist with required columns

#### Scenario: Active alert deduplication constraint

- **GIVEN** an active alert for threshold T in evaluation period P
- **WHEN** inserting another active alert for the same threshold and period
- **THEN** the database rejects the insert via unique constraint `uq_active_alert_period`

#### Scenario: Notification payload storage

- **GIVEN** a threshold breach notification
- **WHEN** the in-app notification is persisted
- **THEN** `payload` JSONB contains tool, team, threshold, current value, and deep link fields
