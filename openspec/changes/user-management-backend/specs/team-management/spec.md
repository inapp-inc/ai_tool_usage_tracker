# Team Management — Delta Specification

## ADDED Requirements

### Requirement: Team CRUD for Super Admin

The system SHALL implement team list, create, get, and update per OpenAPI `/teams` paths and FR-ADM-002.

#### Scenario: Create team with unique name

- **GIVEN** an authenticated Super Admin
- **WHEN** `POST /api/v1/teams` is submitted with a unique team name in the organization
- **THEN** the response status is 201
- **AND** the team appears in `GET /api/v1/teams`

#### Scenario: Duplicate team name rejected

- **GIVEN** an existing team name in the organization
- **WHEN** creating another team with the same name
- **THEN** the response status is 409 Conflict

#### Scenario: Deactivate team

- **GIVEN** an active team
- **WHEN** Super Admin patches `active: false`
- **THEN** the team remains in the database with `active = false`
- **AND** new usage attribution to that team is rejected by domain validation helpers

### Requirement: Team member assignment

The system SHALL support adding and listing team members via `/teams/{teamId}/members` with multi-team membership.

#### Scenario: Assign user to multiple teams

- **GIVEN** user U and teams T1 and T2
- **WHEN** U is added to both teams
- **THEN** both active memberships exist
- **AND** `GET /auth/me` for user U includes both team ids

#### Scenario: Team Admin adds member to administered team

- **GIVEN** a Team Admin with active membership on team T
- **WHEN** they add a valid user to team T
- **THEN** the response status is 201

#### Scenario: Team Admin denied on non-member team

- **GIVEN** a Team Admin not a member of team T
- **WHEN** they attempt to add a member to team T
- **THEN** the response status is 403 Forbidden

### Requirement: Soft remove team member

The system SHALL remove team members via `DELETE /teams/{teamId}/members/{userId}` without deleting historical usage.

#### Scenario: Remove member preserves history

- **GIVEN** a team member with historical usage attributed to the team
- **WHEN** the member is removed
- **THEN** the response status is 204
- **AND** the membership has `removed_at` set
- **AND** historical usage records remain unchanged

### Requirement: Auth profile reflects team membership

The system SHALL populate `team_ids` on `GET /api/v1/auth/me` from active team memberships.

#### Scenario: Me endpoint team ids

- **GIVEN** a user with active memberships on teams T1 and T2
- **WHEN** `GET /api/v1/auth/me` is called
- **THEN** `team_ids` contains T1 and T2
- **AND** removed memberships are excluded
