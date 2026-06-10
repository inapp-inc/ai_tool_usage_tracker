# Provider Connect API — Delta Specification

## ADDED Requirements

### Requirement: Provider-managed connect flow

The system SHALL expose an API for the frontend to connect a vendor provider using an API token and collection schedule per FR-ING-004.

#### Scenario: Connect with new API token

- **GIVEN** an authorized Super Admin
- **WHEN** `POST /api/v1/collectors` is submitted with `provider`, `tool_id`, `api_token`, and `schedule: hourly`
- **THEN** the response status is 201
- **AND** a credential is stored encrypted and a collector config is created
- **AND** the response does not include the plaintext token

#### Scenario: Connect using existing credential

- **GIVEN** an existing stored credential for the tool
- **WHEN** connect request references `credential_id` and `schedule: daily`
- **THEN** collector config links to that credential without re-exposing the secret

#### Scenario: Team Admin forbidden on non-administered team

- **GIVEN** a Team Admin not a member of team T
- **WHEN** connect request includes `team_id` for T
- **THEN** the response status is 403 Forbidden

### Requirement: Manage collector configuration

The system SHALL support list, update, delete, and on-demand run for collector configs.

#### Scenario: Update schedule to daily

- **GIVEN** an active hourly collector
- **WHEN** PATCH sets `schedule: daily`
- **THEN** subsequent Beat scheduling uses daily cadence

#### Scenario: On-demand collection run

- **GIVEN** an active collector
- **WHEN** `POST /collectors/{id}/run` is called by an authorized user
- **THEN** a collection job is enqueued immediately
- **AND** response includes run id or 202 accepted status

#### Scenario: List collectors for organization

- **GIVEN** multiple collector configs in the org
- **WHEN** `GET /collectors` is called by Super Admin
- **THEN** paginated list returns provider, tool, team, schedule, active, last_run_at
