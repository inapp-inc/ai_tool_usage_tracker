# Vendor Collector Adapters — Delta Specification

## ADDED Requirements

### Requirement: Vendor API usage fetch

The system SHALL fetch usage from vendor APIs using decrypted credentials at collection time only.

#### Scenario: OpenAI usage normalized

- **GIVEN** valid OpenAI credential and active collector
- **WHEN** collection runs
- **THEN** vendor response is mapped to canonical usage events with tool_id, team_id, tokens, and timestamps

#### Scenario: Idempotent vendor event ingestion

- **GIVEN** the same vendor event id collected twice
- **WHEN** the second run ingests
- **THEN** duplicate events are ignored per FR-USG-002 idempotency rules

### Requirement: Post-collection pipeline hooks

The system SHALL trigger usage aggregate refresh after successful collection.

#### Scenario: Aggregates refresh after collection

- **GIVEN** new usage events ingested from collection
- **WHEN** collection completes
- **THEN** aggregate refresh job is enqueued
- **AND** threshold evaluation hook is invoked for the organization
