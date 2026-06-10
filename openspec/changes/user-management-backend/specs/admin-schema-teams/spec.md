# Admin Schema (Teams) — Delta Specification

## ADDED Requirements

### Requirement: Admin teams schema migration

The system SHALL persist team data in PostgreSQL schema `admin` with tables `teams` and `team_memberships` matching [database.md](../../../specifications/database.md).

#### Scenario: Migration applies after auth schema

- **GIVEN** auth schema migration already applied
- **WHEN** Alembic migration `003_admin_teams` runs
- **THEN** tables `admin.teams` and `admin.team_memberships` exist
- **AND** unique constraint on team name per organization is enforced

#### Scenario: Soft membership removal column

- **GIVEN** an active team membership
- **WHEN** a member is removed
- **THEN** the membership row remains with `removed_at` set
- **AND** no row is hard-deleted

### Requirement: Multi-team membership uniqueness

The system SHALL allow a user to belong to multiple teams with at most one active membership per user-team pair.

#### Scenario: Duplicate active membership rejected

- **GIVEN** an active membership for user U on team T
- **WHEN** adding user U to team T again
- **THEN** the operation fails with a conflict response

#### Scenario: Re-add after soft removal

- **GIVEN** a membership with `removed_at` set for user U on team T
- **WHEN** user U is added to team T again
- **THEN** a new active membership is created or the existing row is reactivated per repository logic
