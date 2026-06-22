# Copilot Productivity Specification

## Purpose

Define seat-based GitHub Copilot analytics storage, ingestion, API, reporting, and dashboard behavior separate from token-based usage tracking.

## ADDED Requirements

### Requirement: Dedicated Copilot storage

The system MUST persist GitHub Copilot sync data in dedicated `copilot` schema tables: `copilot_organizations`, `copilot_user_usage`, and `copilot_seats`.

The system MUST NOT insert Copilot provider rows into `usage.usage_events` during collector sync.

#### Scenario: Copilot collector run completes

- **Given** a collector configured with provider `copilot`
- **When** sync completes successfully
- **Then** organization snapshots, user productivity rows, and seat rows are stored in `copilot_*` tables
- **And** no new `usage.usage_events` rows are created for that run

#### Scenario: Copilot pull verification is enabled

- **Given** Copilot pull-dump verification is enabled for a collector run
- **When** sync completes successfully
- **Then** parsed Copilot records MAY be written to local verification output
- **And** those records MUST NOT be persisted through the generic usage-event writer

### Requirement: GitHub API mapping

The collector MUST map GitHub Copilot user metrics, organization metrics, and seat billing APIs to the dedicated Copilot domain model.

#### Scenario: User metrics payload is parsed

- **Given** a GitHub user metrics row from `/orgs/{org}/copilot/metrics/reports/users-1-day`
- **When** the row is ingested
- **Then** the system stores report date, user identity, feature, editor, language, active days, chat turns, suggestions, acceptances, acceptance rate, suggested lines, accepted lines, and raw payload

#### Scenario: Seat billing payload is parsed

- **Given** a GitHub seat row from `/orgs/{org}/copilot/billing/seats`
- **When** the row is ingested
- **Then** the system stores user login, seat status, assignment timestamp, last activity timestamp, and monthly seat cost

#### Scenario: Organization metrics payload is parsed

- **Given** a GitHub organization metrics row from `/orgs/{org}/copilot/metrics/reports/organization-1-day`
- **When** the row is ingested
- **Then** the system stores organization identity, report date, total seats, assigned seats, active users, subscription type when known, and monthly cost

### Requirement: Copilot upsert identity

The system MUST upsert Copilot user productivity by `(team_id, organization_id, user_login, report_date, feature, editor, language)`.

The system MUST upsert Copilot organization snapshots by `(team_id, organization_id, report_date)` and seats by `(organization_id, user_login)`.

#### Scenario: Same user metric is synced twice

- **Given** a Copilot user metric row already exists for the same team, organization, user, date, feature, editor, and language
- **When** the same logical row is ingested again with updated counters
- **Then** the existing row is updated instead of duplicating the metric

### Requirement: Package-based cost

The system MUST calculate Copilot seat and user estimated cost using team assignment pricing, tool pricing, or Copilot default seat prices when GitHub does not provide user-level cost.

The default monthly seat prices MUST include Business at `$19`, Enterprise at `$39`, and Individual at `$10`.

#### Scenario: Business package assigned

- **Given** a team tool assignment with Copilot Business package pricing
- **When** a seat is assigned to a user
- **Then** that seat monthly cost is `$19`
- **And** user productivity rows for assigned users use `$19` as estimated cost

#### Scenario: Unassigned user has activity

- **Given** a user metrics row exists for a login that is not in the assigned seat set
- **When** the row is ingested
- **Then** that user's estimated cost is `$0`

### Requirement: Analytics API surface

The system MUST expose Copilot analytics endpoints under `/api/v1/copilot` for overview, users, user detail, insights, and reports.

The endpoints MUST require `insights:read` permission and team access for the requested `team_id`.

#### Scenario: Overview is requested

- **Given** Copilot data exists for a team and date range
- **When** `GET /api/v1/copilot/overview?team_id=&from=&to=` is requested by an authorized user
- **Then** the response includes total seats, assigned seats, active users, inactive users, monthly cost, seat utilization percentage, average acceptance rate, seat utilization chart data, active users trend, suggestions vs acceptances, top languages, and IDE distribution

#### Scenario: Users are requested

- **Given** Copilot user usage exists for a team and date range
- **When** `GET /api/v1/copilot/users?team_id=&from=&to=` is requested by an authorized user
- **Then** the response includes user login, email, active days, chat turns, suggestions, acceptances, acceptance rate, estimated cost, and last activity timestamp for each user

#### Scenario: User detail is requested

- **Given** Copilot user usage exists for a login in a team and date range
- **When** `GET /api/v1/copilot/users/{user_login}?team_id=&from=&to=` is requested by an authorized user
- **Then** the response includes the user summary plus daily usage, language distribution, and IDE usage

#### Scenario: User detail is missing

- **Given** no Copilot user usage exists for a login in the requested team and date range
- **When** `GET /api/v1/copilot/users/{user_login}?team_id=&from=&to=` is requested
- **Then** the API returns `404`

### Requirement: Productivity metrics only

Copilot dashboards and APIs MUST expose seat and productivity fields including seats, suggestions, acceptances, languages, editors, chat turns, acceptance rate, activity status, and costs.

Copilot dashboards and APIs MUST NOT expose `input_tokens`, `output_tokens`, `cache_tokens`, or `total_tokens` as Copilot analytics fields.

#### Scenario: User views Copilot overview

- **Given** Copilot data exists for a team
- **When** the user opens the Copilot analytics overview
- **Then** cards show seat utilization, active users, inactive users, monthly cost, and acceptance rate
- **And** no token usage widgets are displayed

#### Scenario: Token dashboard queries run

- **Given** Copilot is configured as a seat-based provider
- **When** token dashboard aggregations are queried
- **Then** Copilot usage is excluded from token totals

### Requirement: Insights generation

The system MUST generate rule-based insights from stored Copilot data including adoption, license waste, power users, low acceptance rate, IDE concentration, and language concentration when sufficient data exists.

#### Scenario: Active seats exist

- **Given** assigned seats and activity exist in the selected period
- **When** insights are requested
- **Then** an adoption insight is returned with the active-user percentage

#### Scenario: Inactive seats detected

- **Given** assigned seats exist with no activity in the selected period
- **When** insights are requested
- **Then** a license waste insight is returned with inactive seat count and potential monthly savings

#### Scenario: Usage concentration exists

- **Given** user activity, language data, and IDE data exist in Copilot usage payloads
- **When** insights are requested
- **Then** the response includes power-user, language, and IDE insights

### Requirement: Copilot reports

The system MUST expose Copilot report endpoints for seat utilization, productivity, and cost.

#### Scenario: Seat report is requested

- **Given** Copilot seat data exists for a team
- **When** `GET /api/v1/copilot/reports/seats?team_id=` is requested by an authorized user
- **Then** each row includes user login, email, assigned timestamp, last activity timestamp, seat status, and monthly cost

#### Scenario: Productivity report is requested

- **Given** Copilot productivity data exists for a team and date range
- **When** `GET /api/v1/copilot/reports/productivity?team_id=&from=&to=` is requested by an authorized user
- **Then** each row includes user login, language, editor, suggestions, acceptances, acceptance rate, and chat turns

#### Scenario: Cost report is requested

- **Given** Copilot seat data exists for a team
- **When** `GET /api/v1/copilot/reports/cost?team_id=` is requested by an authorized user
- **Then** each row includes user login, package, estimated monthly cost, and activity status

### Requirement: Copilot dashboard route

The frontend MUST provide a dedicated Copilot analytics page at `/insights/copilot` backed by the Copilot analytics API client.

#### Scenario: User navigates to Copilot analytics

- **Given** the frontend application is loaded
- **When** the user opens `/insights/copilot`
- **Then** the Copilot dashboard fetches overview, users, and insights for the selected team and date range
- **And** the navigation identifies the page as Copilot Analytics
