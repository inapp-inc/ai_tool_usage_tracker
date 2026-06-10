# Alembic Migrations — Delta Specification

## ADDED Requirements

### Requirement: Alembic async framework

The system SHALL initialize Alembic with async SQLAlchemy engine support for PostgreSQL.

#### Scenario: Migration upgrade on empty database

- **GIVEN** an empty PostgreSQL database
- **WHEN** `alembic upgrade head` runs
- **THEN** initial revision applies without error
- **AND** application schemas from database.md are created

#### Scenario: Autogenerate against models

- **GIVEN** SQLAlchemy models registered
- **WHEN** `alembic revision --autogenerate` is run in dev
- **THEN** a new revision file is produced

### Requirement: Migration deploy hook

The system SHALL support running migrations via Docker Compose migrate job before API start.

#### Scenario: Migrate service completes

- **GIVEN** pending migrations
- **WHEN** `docker compose run migrate` executes
- **THEN** database is at head revision before API serves traffic
