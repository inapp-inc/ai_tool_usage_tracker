# Celery Worker Setup — Delta Specification

## ADDED Requirements

### Requirement: Celery queue routing

The system SHALL route Celery tasks to named queues per ADR-004: `ingestion`, `reports`, `alerts`, `email`, `maintenance`.

#### Scenario: Task routed to correct queue

- **GIVEN** a sample task declared for queue `ingestion`
- **WHEN** the task is dispatched from the API
- **THEN** the worker consuming `ingestion` queue executes it

### Requirement: Task context propagation

The system SHALL attach `correlation_id` and `organization_id` to Celery task base class for observability.

#### Scenario: Failed task logs correlation id

- **GIVEN** a task that raises an exception
- **WHEN** the failure is logged
- **THEN** the log includes the correlation_id from task headers

### Requirement: Beat scheduler

The system SHALL run Celery Beat without duplicate schedule execution in Compose.

#### Scenario: Beat container starts

- **GIVEN** the compose stack with beat service
- **WHEN** stack is up
- **THEN** beat process runs and registers placeholder schedule entries
