# Auth Schema — Delta Specification

## ADDED Requirements

### Requirement: Auth schema tables exist

The system SHALL persist authentication data in PostgreSQL schema `auth` with tables `organizations`, `users`, and `refresh_tokens` matching [database.md](../../../specifications/database.md) column definitions and constraints.

#### Scenario: Migration applies on empty database

- **GIVEN** an empty PostgreSQL database
- **WHEN** Alembic migration `002_auth` is applied
- **THEN** schema `auth` exists with tables `organizations`, `users`, and `refresh_tokens`
- **AND** constraint `uq_users_org_email` enforces unique email per organization
- **AND** constraint `chk_user_role` restricts role to allowed enum values

#### Scenario: Refresh token record stores hash only

- **GIVEN** a user with an issued refresh token
- **WHEN** the refresh token is persisted
- **THEN** only a hashed token value is stored in `auth.refresh_tokens.token_hash`
- **AND** the plaintext refresh token is never written to the database

### Requirement: Organization tenant root

The system SHALL treat `auth.organizations` as the tenant root with retention constraints enforced at the database level.

#### Scenario: Organization retention constraints

- **GIVEN** an organization insert or update
- **WHEN** `retention_months` or `retention_audit_months` is less than 24
- **THEN** the database rejects the operation with a constraint violation

### Requirement: User account with RBAC role

The system SHALL store platform users in `auth.users` with a non-null `role`, `password_hash`, and `organization_id` foreign key.

#### Scenario: User role enum validation

- **GIVEN** a user record with role `super_admin`, `team_admin`, `finance_viewer`, `team_member`, or `auditor`
- **WHEN** the record is inserted
- **THEN** the insert succeeds

#### Scenario: Invalid user role rejected

- **GIVEN** a user record with role `invalid_role`
- **WHEN** the insert is attempted
- **THEN** the database rejects the operation

### Requirement: Dev seed creates default Super Admin

The system SHALL provide a development-only seed script that creates a default organization and Super Admin user when no users exist.

#### Scenario: Seed on empty auth tables

- **GIVEN** empty `auth.organizations` and `auth.users` tables in a development environment
- **WHEN** the dev seed script runs
- **THEN** one organization and one Super Admin user are created
- **AND** the Super Admin password is read from environment variable `DEV_SUPER_ADMIN_PASSWORD`
