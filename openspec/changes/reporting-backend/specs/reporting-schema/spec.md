# Reporting Schema — Delta Specification

## ADDED Requirements

### Requirement: Report jobs table

The system SHALL persist report generation jobs in `reporting.report_jobs` per [database.md](../../../specifications/database.md).

#### Scenario: Migration creates report jobs schema

- **GIVEN** prior migrations applied
- **WHEN** Alembic migration `007_reporting` runs
- **THEN** table `reporting.report_jobs` exists with columns for type, format, filters, status, and timestamps

#### Scenario: Job lifecycle status transitions

- **GIVEN** a queued report job
- **WHEN** async processing starts and completes successfully
- **THEN** status transitions from `queued` to `processing` to `completed`
- **AND** `started_at` and `completed_at` are populated

### Requirement: Local artifact storage reference

The system SHALL store completed report artifact paths using `storage_key` relative to `LOCAL_STORAGE_ROOT/reports/` per ADR-013.

#### Scenario: Completed job stores storage key

- **GIVEN** a successfully generated CSV report job
- **WHEN** the job completes
- **THEN** `storage_key` contains a relative path under the reports directory
- **AND** the file exists at the resolved local path in the worker container
