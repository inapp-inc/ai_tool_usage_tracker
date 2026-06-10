# Docker Compose Dev Stack — Delta Specification

## ADDED Requirements

### Requirement: Development stack services

The system SHALL provide a Docker Compose stack with `postgres`, `redis`, `api`, `worker`, and `beat` services on a shared internal network per [local-development.md](../../../specifications/local-development.md).

#### Scenario: All services start healthy

- **GIVEN** valid `.env` with `POSTGRES_PASSWORD` set
- **WHEN** `docker compose up --build` is run
- **THEN** all services reach healthy status
- **AND** Postgres passes `pg_isready`

#### Scenario: Persistent volumes

- **GIVEN** the compose stack
- **WHEN** services are defined
- **THEN** named volumes exist for postgres, redis, storage, and backups data

### Requirement: Service hostname connectivity

The system SHALL connect API and workers to PostgreSQL and Redis using Compose service hostnames.

#### Scenario: API health reports dependencies

- **GIVEN** a running stack
- **WHEN** health endpoint is queried
- **THEN** database and redis connectivity status is reported as ok
