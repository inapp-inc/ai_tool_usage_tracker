# Threshold Management — Delta Specification

## ADDED Requirements

### Requirement: List and create thresholds

The system SHALL implement `GET /api/v1/thresholds` and `POST /api/v1/thresholds` per OpenAPI and FR-ADM-004.

#### Scenario: Super Admin creates team-scoped threshold

- **GIVEN** an authenticated Super Admin
- **WHEN** a valid `ThresholdCreateRequest` with scope `team` and `team_id` is submitted
- **THEN** the response status is 201
- **AND** the threshold is persisted with correct scope reference columns

#### Scenario: Team Admin creates threshold for administered team

- **GIVEN** a Team Admin with active membership on team T
- **WHEN** creating a threshold scoped to team T
- **THEN** the response status is 201

#### Scenario: Team Admin denied for other team

- **GIVEN** a Team Admin not a member of team T
- **WHEN** creating a threshold scoped to team T
- **THEN** the response status is 403 Forbidden

### Requirement: Update and delete thresholds

The system SHALL implement `PATCH` and `DELETE` on `/api/v1/thresholds/{thresholdId}` with scoped permissions.

#### Scenario: Update threshold limit

- **GIVEN** an existing active threshold
- **WHEN** Super Admin patches `limit_value`
- **THEN** the response status is 200 with updated threshold

#### Scenario: Utilization percentage validation

- **GIVEN** threshold type `package_utilization_pct`
- **WHEN** `limit_value` is greater than 100
- **THEN** the response status is 422 Unprocessable Entity
