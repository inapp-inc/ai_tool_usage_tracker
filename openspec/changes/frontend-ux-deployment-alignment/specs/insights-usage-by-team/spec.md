# Delta Spec: Insights Usage by Team

## MODIFIED Requirements

### Requirement: Usage by team widget

The system SHALL implement `GET /api/v1/dashboard/usage-by-team` returning consumption comparison rows for **API teams** (`admin.tools`), not member groups (`admin.teams`).

#### Scenario: Organization-wide API team ranking

- **GIVEN** a Super Admin and multiple active tools with usage in `pricing_config`
- **WHEN** the usage-by-team widget loads for a date range
- **THEN** each row includes `team_id` (tool UUID), `team_name`, `total_tokens`, and `estimated_cost`
- **AND** tokens/cost are summed from `daily_usage` within `from`/`to` when daily data exists

#### Scenario: Single team filter

- **GIVEN** Insights Team filter selects one API team
- **WHEN** `GET /dashboard/usage-by-team?tool_id={uuid}` is called
- **THEN** only that tool's usage row is returned

#### Scenario: Insights By Team tab

- **GIVEN** the Insights **By Team** tab
- **WHEN** the table renders
- **THEN** rows list API team names with token/cost/budget columns sourced from `fetchTeamUsage` → `/dashboard/usage-by-team`
- **AND** the page-level Team filter dropdown lists API teams from `fetchToolOptions`
