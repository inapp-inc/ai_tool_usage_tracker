# FastAPI Application Skeleton — Delta Specification

## ADDED Requirements

### Requirement: Bounded context package structure

The system SHALL organize backend code into bounded context packages per ADR-001.

#### Scenario: Package directories exist

- **GIVEN** the backend application
- **WHEN** the project is inspected
- **THEN** packages exist for auth, admin, ingestion, usage, dashboard, reporting, notifications, audit, core, db, and api/v1

### Requirement: API v1 prefix and health endpoint

The system SHALL expose health at `GET /api/v1/health` matching OpenAPI contract.

#### Scenario: Health under v1 prefix

- **GIVEN** a running API
- **WHEN** `GET /api/v1/health` is called
- **THEN** response status is 200 with database and redis status fields

### Requirement: Application settings

The system SHALL load configuration from environment via Pydantic Settings.

#### Scenario: Required settings validated

- **GIVEN** missing `DATABASE_URL` in non-default dev mode
- **WHEN** the application starts
- **THEN** startup fails with a clear configuration error
