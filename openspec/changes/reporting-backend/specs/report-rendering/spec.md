# Report Rendering — Delta Specification

## ADDED Requirements

### Requirement: Aggregate-based report queries

The system SHALL query pre-computed `usage.usage_aggregates` for standard reports per ADR-008 rather than scanning raw events for sync generation.

#### Scenario: Standard report uses aggregates

- **GIVEN** daily aggregates exist for the requested period
- **WHEN** a tool usage summary report is generated synchronously
- **THEN** query execution reads from `usage.usage_aggregates`
- **AND** results include `last_updated_at` or equivalent freshness metadata

### Requirement: RBAC-scoped report data

The system SHALL filter report results to data authorized for the requester's role, matching dashboard scope rules.

#### Scenario: Team Admin team filter

- **GIVEN** a Team Admin authorized for teams T1 and T2
- **WHEN** a team usage report is generated without team filter
- **THEN** results include only T1 and T2 data

#### Scenario: Team Member user usage personal scope

- **GIVEN** a Team Member
- **WHEN** a user usage report is requested without `user_id`
- **THEN** only the caller's personal usage rows are returned

#### Scenario: Finance Viewer read-only

- **GIVEN** a Finance Viewer
- **WHEN** any report is generated
- **THEN** the operation succeeds with read-only data and no mutating side effects

### Requirement: Tool usage summary report

The system SHALL implement report type `tool_usage_summary` per FR-RPT-001 with token counts and share per tool.

#### Scenario: Tool usage summary for period

- **GIVEN** usage across multiple tools in the filter period
- **WHEN** `tool_usage_summary` is generated
- **THEN** each tool row includes input, output, total tokens, and usage share

### Requirement: Team usage report

The system SHALL implement report type `team_usage` per FR-RPT-002.

#### Scenario: Team usage rows include cost metrics

- **GIVEN** team aggregates for the period
- **WHEN** `team_usage` is generated
- **THEN** each team row includes token totals, utilization, and estimated cost

### Requirement: Cost report

The system SHALL implement report type `cost` per FR-RPT-003 separating spend, allowance, and overage.

#### Scenario: Cost columns populated

- **GIVEN** cost aggregate data for the period
- **WHEN** `cost` report is generated
- **THEN** rows include actual spend, package allowance consumed, and overage cost separately

### Requirement: User usage report

The system SHALL implement report type `user_usage` per FR-RPT-004.

#### Scenario: User rows for authorized scope

- **GIVEN** period and team filters within RBAC scope
- **WHEN** `user_usage` is generated
- **THEN** each authorized user row shows tokens and estimated cost

### Requirement: Alert history report

The system SHALL implement report type `alert_history` per FR-RPT-005.

#### Scenario: Alerts listed chronologically

- **GIVEN** threshold alert records in the filter period
- **WHEN** `alert_history` is generated
- **THEN** matching alerts are ordered by trigger time with severity and resolution status

### Requirement: API key activity report

The system SHALL implement report type `api_key_activity` per FR-RPT-006 without exposing credential secrets.

#### Scenario: No secret values in output

- **GIVEN** credential lifecycle audit events in the period
- **WHEN** `api_key_activity` is generated
- **THEN** the output contains masked credential identifiers and event metadata only
- **AND** full secret values never appear in JSON, CSV, or PDF output

### Requirement: Multi-format rendering

The system SHALL render reports in `json`, `csv`, and `pdf` formats per OpenAPI `ReportFormat`.

#### Scenario: Valid CSV export

- **GIVEN** a completed sync report with format `csv`
- **WHEN** the response is returned
- **THEN** the content type is `text/csv`
- **AND** the CSV is parseable with header row matching report columns

#### Scenario: Valid PDF export

- **GIVEN** a completed sync report with format `pdf`
- **WHEN** the response is returned
- **THEN** the content type is `application/pdf`
- **AND** the PDF is a valid binary document
