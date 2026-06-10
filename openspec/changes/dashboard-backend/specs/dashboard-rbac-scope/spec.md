# Dashboard RBAC Scope — Delta Specification

## ADDED Requirements

### Requirement: Role-based query scope

The system SHALL constrain dashboard queries to data authorized for the caller's role per FR-PLT-001 and FR-DSH-001 business rules.

#### Scenario: Team Member personal scope

- **GIVEN** an authenticated Team Member
- **WHEN** any dashboard widget is requested without elevated scope
- **THEN** query filters restrict results to the caller's `user_id` only

#### Scenario: Team Admin team scope

- **GIVEN** an authenticated Team Admin with active memberships on teams T1 and T2
- **WHEN** a dashboard widget is requested
- **THEN** results include only data for T1 and T2 unless `team_id` filter narrows further
- **AND** filtering to a team outside membership returns 403 Forbidden

#### Scenario: Super Admin organization scope

- **GIVEN** an authenticated Super Admin
- **WHEN** a dashboard widget is requested with optional `team_id`
- **THEN** results include all organization data or the specified team within the organization

#### Scenario: Finance Viewer read-only org access

- **GIVEN** an authenticated Finance Viewer
- **WHEN** dashboard widgets are requested
- **THEN** read queries succeed for authorized org/team scope
- **AND** mutating operations are not exposed on dashboard endpoints

#### Scenario: Auditor read-only access

- **GIVEN** an authenticated Auditor
- **WHEN** dashboard widgets are requested
- **THEN** read queries succeed for organization-wide scope
- **AND** no write endpoints exist on dashboard routes
