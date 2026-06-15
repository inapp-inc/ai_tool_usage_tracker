# Delta Spec: Frontend Pages and Routing

Documents the implemented React application routes, navigation, and page-to-API dependencies.

## ADDED Requirements

### Requirement: Active route inventory

OpenSpec documentation SHALL list all routes registered in `frontend/src/App.tsx` with their page components and access guards.

#### Scenario: Primary routes documented

- **GIVEN** the implemented `App.tsx` router
- **WHEN** a reader opens the frontend routing section in `openspec/project.md` or companion doc
- **THEN** the following routes SHALL be listed: `/login`, `/insights`, `/alerts`, `/alerts/history`, `/uploads`, `/uploads/:uploadId/preview`, `/admin/teams`, `/admin/groups`, `/admin/providers`, `/admin/members`, `/admin/credentials`, `/admin/audit-log`

#### Scenario: Legacy redirects documented

- **GIVEN** deprecated standalone dashboard/usage/reports pages and old admin paths
- **WHEN** routing documentation is updated
- **THEN** redirects SHALL be recorded: `/` → `/insights` or `/login`, `/dashboard` → `/insights`, `/usage/teams` → `/insights`, `/usage/teams/:teamId` → `/insights`, `/reports` → `/insights`, `/reports/new` → `/insights`, `/admin/tools` → `/admin/teams`, `*` → `/insights`
- **AND** legacy page files (`DashboardPage`, `TeamUsagePage`, `ReportsListPage`, etc.) SHALL be marked as unrouted/deprecated

### Requirement: Admin terminology in routing docs

Documentation SHALL distinguish **Teams** (`/admin/teams` → `tools` API) from **Groups** (`/admin/groups` → `teams` API).

#### Scenario: Teams vs Groups routes

- **GIVEN** updated admin navigation
- **WHEN** routing documentation is read
- **THEN** `/admin/teams` SHALL be described as API team connections (ToolsPage)
- **AND** `/admin/groups` SHALL be described as member groups (TeamsPage)

### Requirement: Insights hub consolidation

Documentation SHALL describe `/insights` as the unified analytics hub replacing separate dashboard, usage, and reports pages.

#### Scenario: Insights tabs documented

- **GIVEN** `InsightsPage` implements tabbed UI
- **WHEN** frontend task docs are updated
- **THEN** documentation SHALL describe three tabs: Overview (stats, charts, alerts), By Team (API team usage table), Reports (generate, download, subscribe, delete)
- **AND** Usage by Team data SHALL be sourced from `/dashboard/usage-by-team` (tool metrics)

### Requirement: Role-based page access

Documentation SHALL record `RoleGuard` usage per admin and sensitive page.

#### Scenario: Super Admin pages documented

- **GIVEN** admin pages use `RoleGuard`
- **WHEN** routing documentation is updated
- **THEN** it SHALL record Super Admin requirement for: Teams, Groups, Members, Credentials, Audit Log, Providers pages
- **AND** Alerts page access requirements SHALL match implemented guards

### Requirement: Page-to-API dependency map

Documentation SHALL include a matrix mapping each active page to the API modules it imports.

#### Scenario: Insights page dependencies documented

- **GIVEN** `InsightsPage` imports from multiple API modules
- **WHEN** the dependency map is published
- **THEN** it SHALL list: `dashboard`, `usage`, `reports`, `teams`, `tools` (via `fetchToolOptions`)
- **AND** it SHALL note report subscription SlideOver uses `fetchSubscriptions`, `createSubscription`, `deleteSubscription`

#### Scenario: Admin page dependencies documented

- **GIVEN** admin pages under `/admin/*`
- **WHEN** the dependency map is published
- **THEN** Teams page (`/admin/teams`) SHALL be mapped to `tools` only
- **AND** Groups page (`/admin/groups`) SHALL be mapped to `teams`, `usage.fetchToolOptions`
- **AND** Credentials page SHALL be mapped to `credentials`, `teams`, `usage.fetchToolOptions`

#### Scenario: Live API integration

- **GIVEN** implemented frontend modules
- **WHEN** dependency documentation is updated
- **THEN** core modules (`auth`, `tools`, `teams`, `members`, `credentials`, `alerts`, `uploads`, `dashboard`, `usage`) SHALL be documented as calling live `/api/v1` endpoints

### Requirement: Post-login navigation

Documentation SHALL record default authenticated landing route.

#### Scenario: Login redirect documented

- **GIVEN** successful login or session restore
- **WHEN** routing documentation is updated
- **THEN** it SHALL record redirect target `/insights` (not legacy `/dashboard`)
- **AND** `VITE_BASE_PATH` basename SHALL be documented for production subpath hosting
