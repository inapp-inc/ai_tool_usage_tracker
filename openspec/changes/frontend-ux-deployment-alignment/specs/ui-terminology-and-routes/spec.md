# Delta Spec: UI Terminology and Routes

## ADDED Requirements

### Requirement: Admin UI terminology glossary

OpenSpec SHALL document the mapping between user-facing labels, SPA routes, and REST API paths so readers do not confuse **Teams** (API connections) with **Groups** (member org units).

#### Scenario: Teams admin page documented

- **GIVEN** the implemented admin navigation
- **WHEN** a reader opens terminology documentation
- **THEN** **Teams** SHALL map to route `/admin/teams`, page `ToolsPage`, API `/api/v1/tools`, entity `admin.tools`

#### Scenario: Groups admin page documented

- **GIVEN** the implemented admin navigation
- **WHEN** a reader opens terminology documentation
- **THEN** **Groups** SHALL map to route `/admin/groups`, page `TeamsPage`, API `/api/v1/teams`, entity `admin.teams`

## MODIFIED Requirements

### Requirement: Active route inventory

OpenSpec documentation SHALL list all routes registered in `frontend/src/App.tsx` with their page components and access guards.

#### Scenario: Primary routes documented

- **GIVEN** the implemented `App.tsx` router
- **WHEN** a reader opens the frontend routing section
- **THEN** the following routes SHALL be listed: `/login`, `/insights`, `/alerts`, `/alerts/history`, `/uploads`, `/uploads/:uploadId/preview`, `/admin/teams`, `/admin/groups`, `/admin/providers`, `/admin/members`, `/admin/credentials`, `/admin/audit-log`

#### Scenario: Legacy redirects documented

- **GIVEN** deprecated standalone dashboard/usage/reports pages and old admin paths
- **WHEN** routing documentation is updated
- **THEN** redirects SHALL be recorded: `/` → `/insights` (authenticated) or `/login` (guest), `/dashboard` → `/insights`, `/usage/teams` → `/insights`, `/reports` → `/insights`, `/admin/tools` → `/admin/teams`, `*` → `/insights`

### Requirement: Post-login navigation

Documentation SHALL record default authenticated landing route.

#### Scenario: Login redirect documented

- **GIVEN** successful login or session restore
- **WHEN** routing documentation is updated
- **THEN** it SHALL record redirect target `/insights`
- **AND** `BrowserRouter` basename SHALL follow `VITE_BASE_PATH` (e.g. `/aitool` in production)

### Requirement: Page-to-API dependency map

Documentation SHALL include a matrix mapping each active page to the API modules it imports.

#### Scenario: Admin page dependencies documented

- **GIVEN** admin pages under `/admin/*`
- **WHEN** the dependency map is published
- **THEN** **Teams** page (`/admin/teams`) SHALL be mapped to `tools` API
- **AND** **Groups** page (`/admin/groups`) SHALL be mapped to `teams` API and `usage.fetchToolOptions`
- **AND** Credentials page SHALL be mapped to `credentials`, `teams`, `usage.fetchToolOptions`

#### Scenario: Live HTTP documented

- **GIVEN** implemented frontend API modules
- **WHEN** the dependency map is updated
- **THEN** documentation SHALL state that `auth`, `tools`, `teams`, `members`, `credentials`, `alerts`, `uploads`, `dashboard`, and `usage` call live `/api/v1` endpoints (not in-memory mocks)
