# Delta Spec: Alert Scope Labels

## MODIFIED Requirements

### Requirement: Alert threshold scope selection

The alerts UI SHALL expose scope options aligned with product terminology and persist scope values compatible with the alerts store.

#### Scenario: Scope dropdown labels

- **GIVEN** the create/edit alert form
- **WHEN** the user opens the Scope dropdown
- **THEN** options SHALL be: **Organization**, **Group**, **Team**, **User**
- **AND** stored values SHALL be `organization`, `team` (Group), `tool` (Team), `user` respectively

#### Scenario: Group scope target

- **GIVEN** scope **Group** selected
- **WHEN** the target dropdown is shown
- **THEN** it SHALL list member groups from `GET /api/v1/teams` with label **Group** / placeholder **Select group**

#### Scenario: Team scope target

- **GIVEN** scope **Team** selected
- **WHEN** the target dropdown is shown
- **THEN** it SHALL list API teams from `GET /api/v1/tools` with label **Team** / placeholder **Select team**

#### Scenario: User scope target

- **GIVEN** scope **User** selected
- **WHEN** the target dropdown is shown
- **THEN** it SHALL list members from `GET /api/v1/members`

#### Scenario: Persist display name

- **GIVEN** a scope target is selected on create or update
- **WHEN** the alert rule is saved
- **THEN** the request SHALL include `team_name` resolved from the selected entity for table display
