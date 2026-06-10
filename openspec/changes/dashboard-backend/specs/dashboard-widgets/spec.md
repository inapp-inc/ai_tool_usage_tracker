# Dashboard Widgets — Delta Specification

## ADDED Requirements

### Requirement: Token usage widget

The system SHALL implement `GET /api/v1/dashboard/tokens` returning aggregate input, output, and total tokens with `last_updated_at` per OpenAPI `TokenUsageWidget`.

#### Scenario: Token totals for date range

- **GIVEN** usage aggregates exist for the selected `from`/`to` dates
- **WHEN** an authorized user requests the token widget
- **THEN** the response includes `input_tokens`, `output_tokens`, `total_tokens`, and `last_updated_at`
- **AND** totals reflect the authorized RBAC scope

#### Scenario: Date filter changes totals

- **GIVEN** usage in January and February
- **WHEN** the user applies a February-only date filter
- **THEN** token totals include February data only

### Requirement: Cost overview widget

The system SHALL implement `GET /api/v1/dashboard/cost` returning actual spend, package allowance, overage, and `last_updated_at` per OpenAPI `CostOverviewWidget`.

#### Scenario: Cost breakdown displayed

- **GIVEN** aggregated cost data for the period
- **WHEN** an authorized user requests the cost widget
- **THEN** `actual_spend`, `package_allowance`, and `overage_cost` are returned

#### Scenario: Tool without package allowance

- **GIVEN** usage for tools with no package allowance configured
- **WHEN** the cost widget loads
- **THEN** `overage_cost` is zero or not applicable
- **AND** `actual_spend` reflects token-based cost only

### Requirement: Usage by tool widget

The system SHALL implement `GET /api/v1/dashboard/usage-by-tool` with per-tool tokens, cost, and `share_pct`.

#### Scenario: Multi-tool breakdown with share percentages

- **GIVEN** usage across multiple tools in the period
- **WHEN** the widget is requested
- **THEN** each tool entry includes `total_tokens` and `share_pct` summing to approximately 100%

#### Scenario: Inactive tool with historical usage

- **GIVEN** an inactive tool with usage events in the selected period
- **WHEN** the usage-by-tool widget loads
- **THEN** the inactive tool appears in the breakdown

### Requirement: Usage by team widget

The system SHALL implement `GET /api/v1/dashboard/usage-by-team` with team comparison metrics.

#### Scenario: Organization-wide team ranking

- **GIVEN** a Super Admin and multiple teams with usage
- **WHEN** the usage-by-team widget loads
- **THEN** teams are returned with `total_tokens` and `estimated_cost` for comparison

#### Scenario: Deactivated team with period usage

- **GIVEN** a deactivated team with usage in the selected period
- **WHEN** the widget loads for authorized scope
- **THEN** the deactivated team appears in results

### Requirement: Top consumers widget

The system SHALL implement `GET /api/v1/dashboard/top-consumers` ranking teams or users by consumption descending.

#### Scenario: Top teams ranked by tokens

- **GIVEN** team usage data and `entity=teams`
- **WHEN** the widget is requested with default limit
- **THEN** teams are ordered descending by `total_tokens`

#### Scenario: Fewer entities than limit

- **GIVEN** only three teams with usage and limit 10
- **WHEN** the widget loads
- **THEN** all three teams are returned without error

### Requirement: Active alerts widget

The system SHALL implement `GET /api/v1/dashboard/alerts` returning active threshold breaches per OpenAPI `ActiveAlertSummary`.

#### Scenario: Active alerts listed

- **GIVEN** alerts with `status = active` in the authorized scope
- **WHEN** the alerts widget is requested
- **THEN** each alert includes severity, threshold type, current value, and limit value

#### Scenario: No active alerts empty state

- **GIVEN** no active alerts in scope
- **WHEN** the alerts widget is requested
- **THEN** the response returns an empty `data` array with 200 status

### Requirement: Trend analysis widget

The system SHALL implement `GET /api/v1/dashboard/trends` with daily, weekly, or monthly granularity.

#### Scenario: Granularity switch buckets correctly

- **GIVEN** daily aggregates across a date range
- **WHEN** `granularity=weekly` is requested
- **THEN** trend points are bucketed by calendar week with summed tokens

#### Scenario: Missing period shows zero

- **GIVEN** a date range with gaps in aggregate data
- **WHEN** trends are requested
- **THEN** missing buckets return `total_tokens` of zero explicitly

### Requirement: Personal usage widget

The system SHALL implement `GET /api/v1/dashboard/my-usage` for personal consumption summaries.

#### Scenario: Team Member sees own usage

- **GIVEN** a logged-in Team Member
- **WHEN** my-usage is requested without `user_id`
- **THEN** the response reflects only the caller's usage for the period

#### Scenario: Unauthorized user_id access denied

- **GIVEN** a Team Member
- **WHEN** my-usage is requested with another user's `user_id`
- **THEN** the response status is 403 Forbidden

#### Scenario: Super Admin views another user

- **GIVEN** a Super Admin
- **WHEN** my-usage is requested with a valid `user_id` in the organization
- **THEN** the response reflects that user's usage summary
