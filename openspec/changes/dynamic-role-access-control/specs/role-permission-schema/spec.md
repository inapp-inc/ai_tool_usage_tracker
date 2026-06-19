# Spec: Role Permission Schema

## ADDED Requirements

### Requirement: Roles Table

The system SHALL maintain an `auth.roles` table storing named roles scoped to an
organisation. Each role carries an `is_system` flag that protects built-in roles
from deletion. All five existing roles (super_admin, team_admin, finance_viewer,
auditor, team_member) SHALL be seeded as system roles on first migration.

#### Scenario: System roles are seeded on migration

GIVEN a fresh database after migration runs
WHEN `SELECT COUNT(*) FROM auth.roles WHERE is_system = true` is executed
THEN the result is 5, corresponding to super_admin, team_admin, finance_viewer,
auditor, and team_member

#### Scenario: System role cannot be deleted

GIVEN a super_admin authenticated user
WHEN they call `DELETE /api/v1/roles/{role_id}` where the target role has `is_system = true`
THEN the API returns 409 Conflict with detail "System roles cannot be deleted"

#### Scenario: Custom role can be created

GIVEN a super_admin authenticated user
WHEN they call `POST /api/v1/roles` with `{"name": "Read-Only Viewer", "description": "..."}`
THEN the API returns 201 with the new role's id and `is_system: false`

---

### Requirement: Role Permissions Table

The system SHALL maintain an `auth.role_permissions` table with one row per
role × resource combination. Each row carries `can_read` (bool), `can_write`
(bool), and `team_scoped` (bool) columns. `can_write = true` SHALL imply
`can_read = true` at the enforcement layer. The valid resource keys are:
`insights`, `alerts`, `uploads`, `members`, `reports`, `audit_logs`, `tools`,
`teams`, `credentials`, `collectors`, `settings`, `my_usage`.

#### Scenario: Seeded system role permissions match current RBAC matrix

GIVEN a fresh database after migration runs
WHEN permissions for the `super_admin` system role are queried
THEN every resource row has `can_read = true` and `can_write = true`

GIVEN a fresh database after migration runs
WHEN permissions for the `finance_viewer` system role are queried
THEN only `reports` and `my_usage` rows have `can_read = true`; all other
resources have `can_read = false` and `can_write = false`

#### Scenario: Permission row is unique per role and resource

GIVEN an existing `role_permissions` row for role X and resource `alerts`
WHEN an insert is attempted with the same role_id and resource
THEN the database raises a unique constraint violation

#### Scenario: Role with no permission row for a resource is treated as denied

GIVEN a role that has no `role_permissions` row for resource `credentials`
WHEN the permission enforcement layer checks read access to `credentials`
THEN access is denied (403)

---

### Requirement: Users Table Migration

The system SHALL replace the `auth.users.role` VARCHAR column with a
`auth.users.role_id` UUID FK referencing `auth.roles.id`. The migration SHALL
backfill `role_id` for every existing user by matching the current `role` string
to the corresponding seeded system role. After backfill, the `role` column and
its CHECK constraint SHALL be dropped.

#### Scenario: All existing users retain correct role after migration

GIVEN users exist with various role strings before migration
WHEN the migration runs
THEN every user's `role_id` FK points to the system role whose name matches
the original `role` string, and no user has a NULL `role_id`

#### Scenario: New user creation requires role_id

GIVEN a valid role_id from an existing role
WHEN `POST /api/v1/users` is called with that role_id
THEN the user is created and `auth.users.role_id` stores the provided UUID

#### Scenario: Deleting a role with active users is rejected

GIVEN a custom role that has at least one active user assigned
WHEN `DELETE /api/v1/roles/{role_id}` is called
THEN the API returns 409 Conflict with detail "Role has active users assigned"
