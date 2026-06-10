# Collector Schema — Delta Specification

## ADDED Requirements

### Requirement: Collector configuration persistence

The system SHALL persist collector integrations in `ingestion.collector_configs` with tool, optional team, credential reference, provider, and schedule.

#### Scenario: Collector config migration applies

- **GIVEN** ingestion schema exists
- **WHEN** collector migration runs
- **THEN** tables `ingestion.collector_configs` and `ingestion.collector_runs` exist

#### Scenario: Schedule enum validation

- **GIVEN** a collector config with schedule `hourly` or `daily`
- **WHEN** the record is inserted
- **THEN** the insert succeeds
- **AND** invalid schedule values are rejected

### Requirement: Collector run history

The system SHALL record each collection execution in `ingestion.collector_runs` with status and record counts.

#### Scenario: Successful run recorded

- **GIVEN** a completed collection job
- **WHEN** ingestion finishes
- **THEN** a run row exists with status `completed` and `records_ingested` count

#### Scenario: Failed run stores error without secrets

- **GIVEN** vendor API returns authentication failure
- **WHEN** collection fails
- **THEN** run status is `failed`
- **AND** `error_message` does not contain the API token
