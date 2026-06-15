# Delta Spec: Frontend Pages and Routing

Documents the implemented React application routes, navigation, and page-to-API dependencies.

## ADDED Requirements

### Requirement: Active route inventory

OpenSpec documentation SHALL list all routes registered in `frontend/src/App.tsx` with their page components and access guards.

#### Scenario: Primary routes documented

- **GIVEN** the implemented `App.tsx` router
- **WHEN** a reader opens the frontend routing section in `openspec/project.md` or companion doc
- **THEN** the following routes SHALL be listed: `/login`, `/insights`, `/alerts`, `/alerts/history`, `/uploads`, `/uploads/:uploadId/preview`, `/admin/tools`, `/admin/teams`, `/admin/members`, `/admin/credentials`, `/admin/audit-log`

#### Scenario: Legacy redirects documented

- **GIVEN** deprecated standalone dashboard/usage/reports pages
- **WHEN** routing documentation is updated
- **THEN** redirects SHALL be recorded: `/` → `/login`, `/dashboard` → `/insights`, `/usage/teams` → `/insights`, `/usage/teams/:teamId` → `/insights`, `/reports` → `/insights`, `/reports/new` → `/insights`, `*` → `/insights`
- **AND** legacy page files (`DashboardPage`, `TeamUsagePage`, `ReportsListPage`, etc.) SHALL be marked as unrouted/deprecated

### Requirement: Insights hub consolidation

Documentation SHALL describe `/insights` as the unified analytics hub replacing separate dashboard, usage, and reports pages.

#### Scenario: Insights tabs documented

- **GIVEN** `InsightsPage` implements tabbed UI
- **WHEN** frontend task docs are updated
- **THEN** documentation SHALL describe three tabs: Overview (stats, charts, alerts), Usage (team table, drill-downs), Reports (DataTable with generate, download, subscribe, delete)
- **AND** TASK-UI-004, TASK-UI-005, and TASK-UI-008 SHALL reference Insights hub rather than separate page tasks where applicable

### Requirement: Role-based page access

Documentation SHALL record `RoleGuard` usage per admin and sensitive page.

#### Scenario: Super Admin pages documented

- **GIVEN** admin pages use `RoleGuard`
- **WHEN** routing documentation is updated
- **THEN** it SHALL record Super Admin requirement for: Tools, Teams, Members, Credentials, Audit Log pages
- **AND** Alerts page access requirements SHALL match implemented guards

### Requirement: Page-to-API dependency map

Documentation SHALL include a matrix mapping each active page to the API modules it imports.

#### Scenario: Insights page dependencies documented

- **GIVEN** `InsightsPage` imports from multiple API modules
- **WHEN** the dependency map is published
- **THEN** it SHALL list: `dashboard`, `usage`, `reports`, `teams` modules
- **AND** it SHALL note report subscription SlideOver uses `fetchSubscriptions`, `createSubscription`, `deleteSubscription`

#### Scenario: Admin page dependencies documented

- **GIVEN** admin pages under `/admin/*`
- **WHEN** the dependency map is published
- **THEN** Credentials page SHALL be mapped to `credentials`, `teams`, `usage.fetchToolOptions`
- **AND** Teams page SHALL be mapped to `teams`, `usage.fetchToolOptions`
- **AND** Tools page SHALL be mapped to `tools` only

### Requirement: Post-login navigation

Documentation SHALL record default authenticated landing route.

#### Scenario: Login redirect documented

- **GIVEN** successful login flow
- **WHEN** routing documentation is updated
- **THEN** it SHALL record redirect target `/insights` (not legacy `/dashboard`)
