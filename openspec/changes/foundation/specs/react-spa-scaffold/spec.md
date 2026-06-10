# React SPA Scaffold — Delta Specification

## ADDED Requirements

### Requirement: Frontend application shell

The system SHALL provide a React TypeScript SPA built with Vite per ADR-006.

#### Scenario: Dev server starts

- **GIVEN** frontend dependencies installed
- **WHEN** `npm run dev` is executed
- **THEN** the application serves on the configured dev port

#### Scenario: Production build succeeds

- **GIVEN** the frontend project
- **WHEN** `npm run build` runs
- **THEN** static assets are produced without errors

### Requirement: API client with auth headers

The system SHALL provide an API client targeting `/api/v1` with JWT and correlation ID header support.

#### Scenario: API client attaches headers

- **GIVEN** a stored JWT in auth context
- **WHEN** the API client makes a request
- **THEN** `Authorization: Bearer` and `X-Correlation-ID` headers are sent

### Requirement: Internationalization structure

The system SHALL externalize user-facing strings to i18n resource files per NFR-LOC-001.

#### Scenario: Login page uses i18n keys

- **GIVEN** the login placeholder route
- **WHEN** rendered in en-US locale
- **THEN** visible strings resolve from i18n resources not hardcoded literals

### Requirement: Placeholder routes

The system SHALL define placeholder routes for login, dashboard, and admin sections.

#### Scenario: Router navigates to placeholders

- **GIVEN** the SPA router configuration
- **WHEN** user navigates to `/login`, `/dashboard`, and `/admin`
- **THEN** placeholder pages render without error
