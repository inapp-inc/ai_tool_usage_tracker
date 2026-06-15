# Delta Spec: Frontend Mock API Catalog

Documents the normative contract for `frontend/src/api/*` mock modules that backend implementations MUST satisfy when replacing mocks.

## ADDED Requirements

### Requirement: Mock API module inventory

The OpenSpec documentation SHALL include a catalog enumerating every domain API module exported from `frontend/src/api/index.ts` with its exported functions, primary TypeScript types, default mock latency, and TanStack Query keys used by pages.

#### Scenario: Catalog lists all thirteen modules

- **GIVEN** the frontend API barrel at `frontend/src/api/index.ts`
- **WHEN** a reader opens `openspec/specifications/apis/frontend-mock-api-catalog.md`
- **THEN** the catalog SHALL list modules: `auth`, `alerts`, `auditLog`, `credentials`, `dashboard`, `members`, `notifications`, `reports`, `teams`, `tools`, `uploads`, `usage`, and `client`
- **AND** each module entry SHALL document exported async functions and return types

#### Scenario: Mock latency documented per module

- **GIVEN** domain modules using the shared `delay()` helper
- **WHEN** the catalog documents mock behaviour
- **THEN** the default latency SHALL be recorded as 400 ms except where overridden (`auth.login` 600 ms, `reports.downloadReport` 300 ms, `uploads` background completion 1000 ms)

### Requirement: Authentication API contract

The catalog SHALL document `auth.ts` distinguishing live HTTP endpoints from mock login behaviour.

#### Scenario: Live auth endpoints identified

- **GIVEN** `auth.ts` implementation
- **WHEN** the catalog documents authentication
- **THEN** it SHALL record `POST /auth/login` (mock delay path), `POST /auth/refresh`, and `GET /auth/me` as live HTTP via `apiRequest`
- **AND** it SHALL document `LoginRequest`, `LoginResponse`, and `User` types from shared types

### Requirement: Administration API contracts

The catalog SHALL document admin domain modules: `tools`, `teams`, `members`, `credentials` with CRUD signatures matching implemented TypeScript interfaces.

#### Scenario: Tools module includes pricing model

- **GIVEN** `tools.ts` exports `AiTool` with `ToolPricing`
- **WHEN** the catalog documents tools
- **THEN** it SHALL include fields: `provider`, `pricingModel`, `inputCostPer1k`, `outputCostPer1k`, `monthlyAllowanceTokens`, `status`, `lastSyncedAt`
- **AND** it SHALL list `fetchTools`, `createTool`, `updateTool`, `deleteTool`, `syncTool`

#### Scenario: Teams module includes tool mapping

- **GIVEN** `teams.ts` exports `Team` with `toolIds: string[]`
- **WHEN** the catalog documents teams
- **THEN** it SHALL record team–tool assignment as part of `CreateTeamRequest` / `UpdateTeamRequest`

#### Scenario: Credentials module reflects team-scoped AI keys

- **GIVEN** `credentials.ts` BRD 5.1.3 redesign
- **WHEN** the catalog documents credentials
- **THEN** it SHALL document `CredentialEnvironment` (`production` | `sandbox`), `Credential` with `toolId`, `teamId`, `keyMasked`, `rotationReminderDays`, `expiresAt`
- **AND** it SHALL document `createCredential` returning `{ credential, plainKey }` one-time reveal semantics
- **AND** it SHALL NOT document legacy `CredentialScope` ingest keys as active (commented reserved for future use only)

### Requirement: Insights and usage API contracts

The catalog SHALL document `dashboard.ts` and `usage.ts` functions consumed by `InsightsPage`.

#### Scenario: Dashboard stats and widgets documented

- **GIVEN** `InsightsPage` queries dashboard functions with `["insights", …]` keys
- **WHEN** the catalog documents dashboard
- **THEN** it SHALL list `fetchDashboardStats`, `fetchDailyUsage`, `fetchTeamCost`, `fetchTopUsers`, `fetchRecentAlerts` with date-range parameters

#### Scenario: Usage drill-down documented

- **GIVEN** `usage.ts` supports team and daily breakdown
- **WHEN** the catalog documents usage
- **THEN** it SHALL include `fetchTeamUsage`, `fetchTeamDrilldown`, `fetchDailyBreakdown`, `fetchToolOptions`
- **AND** it SHALL document `DailyBreakdownTeam` nested user rows for chart date drill-down

### Requirement: Alerts API contract

The catalog SHALL document threshold alert rules and history matching `alerts.ts`.

#### Scenario: Alert rule threshold types documented

- **GIVEN** `AlertRule` uses `ThresholdType` and `ThresholdScope`
- **WHEN** the catalog documents alerts
- **THEN** it SHALL record threshold types: `token_count`, `cost_usd`, `budget_percent`
- **AND** it SHALL document CRUD functions and `fetchAlertHistory`, `acknowledgeAlert`

### Requirement: Reports and subscriptions API contract

The catalog SHALL document reports including subscription management added to Insights.

#### Scenario: Report entity includes subscription count

- **GIVEN** `Report` type includes `subscriptionCount: number`
- **WHEN** the catalog documents reports
- **THEN** it SHALL list `fetchReports`, `createReport`, `deleteReport`, `downloadReport`
- **AND** it SHALL list `fetchSubscriptions`, `createSubscription`, `deleteSubscription` with `ReportSubscription`, `SubscriptionChannel`, `SubscriptionCadence` types
- **AND** query key `["subscriptions", reportId]` SHALL be documented

### Requirement: Uploads API contract

The catalog SHALL document the upload wizard flow: list, upload, preview, submit, delete.

#### Scenario: Upload preview and commit documented

- **GIVEN** `uploads.ts` mock flow
- **WHEN** the catalog documents uploads
- **THEN** it SHALL document `UploadRecord` statuses, `fetchUploadPreview`, `submitUpload` with `SubmitUploadRequest`
- **AND** query keys `["uploads"]` and `["uploads", uploadId, "preview"]` SHALL be recorded

### Requirement: Audit log API contract

The catalog SHALL document filterable audit log fetch.

#### Scenario: Audit filters documented

- **GIVEN** `auditLog.ts` exports `AuditLogFilters`
- **WHEN** the catalog documents audit log
- **THEN** it SHALL record filter fields: `search`, `category`, `from`, `to`
- **AND** query key pattern `["audit-log", filters]` SHALL be documented

### Requirement: Members API contract

The catalog SHALL document member invite, update, remove, and team-scoped fetch.

#### Scenario: Member CRUD documented

- **GIVEN** `members.ts` exports
- **WHEN** the catalog documents members
- **THEN** it SHALL list `fetchMembers`, `fetchMembersByTeam`, `inviteMember`, `updateMember`, `removeMember`
- **AND** it SHALL document `Member` with `Role` from shared types
