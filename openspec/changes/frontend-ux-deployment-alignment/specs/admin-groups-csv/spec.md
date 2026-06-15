# Delta Spec: Admin Groups and CSV Teams

## MODIFIED Requirements

### Requirement: Group creation API

The system SHALL create member groups via `POST /api/v1/teams` without server errors when required model imports are present.

#### Scenario: Create group with name only

- **GIVEN** a Super Admin
- **WHEN** `POST /api/v1/teams` is submitted with name and optional description
- **THEN** response status SHALL be `201`
- **AND** assigned API teams (`settings.toolIds`) MAY be empty

#### Scenario: Missing model import regression

- **GIVEN** `TeamService.create_team` implementation
- **WHEN** a group is created
- **THEN** `Team` and `AuthenticatedUser` MUST be imported in `app.admin.teams.service`
- **AND** a missing import SHALL NOT surface as HTTP 500 `NameError`

### Requirement: CSV-imported API teams

Tools ingested via CSV SHALL NOT support vendor sync refresh.

#### Scenario: UI hides refresh for CSV tools

- **GIVEN** a tool with `ingestion_source: "csv"`
- **WHEN** viewed on Admin → Teams
- **THEN** sync/refresh controls SHALL be hidden

#### Scenario: Backend rejects sync

- **GIVEN** a CSV-imported tool
- **WHEN** `POST /api/v1/tools/{id}/sync` is called
- **THEN** the API SHALL reject the operation with an appropriate client error

### Requirement: Upload CSV column mapping

Upload preview SHALL support inspect and preview with column mapping like tool CSV import.

#### Scenario: Upload inspect endpoint

- **GIVEN** an uploaded file
- **WHEN** `GET /api/v1/uploads/{id}/inspect` is called
- **THEN** headers and suggested column mapping are returned

#### Scenario: Upload preview with mapping

- **GIVEN** column mapping selections
- **WHEN** `POST /api/v1/uploads/{id}/preview` is called
- **THEN** parsed preview rows are returned before commit
