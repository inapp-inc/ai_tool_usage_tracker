# Spec: Role Management API

## ADDED Requirements

### Requirement: List Roles

The system SHALL expose `GET /api/v1/roles` returning all roles for the
organisation, including system and custom roles. This endpoint SHALL be
accessible to super_admin only.

#### Scenario: Super admin retrieves role list

GIVEN a super_admin authenticated user
WHEN they call `GET /api/v1/roles`
THEN the response is 200 with a list containing at least the 5 system roles,
each with `id`, `name`, `description`, `is_system`, and `created_at`

#### Scenario: Non-super-admin is denied role list

GIVEN a user with any role other than super_admin
WHEN they call `GET /api/v1/roles`
THEN the response is 403 Forbidden

---

### Requirement: Create Custom Role

The system SHALL expose `POST /api/v1/roles` allowing super_admin to create a
new custom role. The created role SHALL have `is_system = false` and an empty
permission set (all resources default to `can_read = false`, `can_write = false`,
`team_scoped = false`).

#### Scenario: Super admin creates a custom role

GIVEN a super_admin authenticated user
WHEN they call `POST /api/v1/roles` with `{"name": "Billing Viewer", "description": "Read-only billing access"}`
THEN the response is 201 with the new role's `id` and `is_system: false`
AND `GET /api/v1/roles/{id}/permissions` returns 12 rows all with `can_read: false`

#### Scenario: Duplicate role name within org is rejected

GIVEN a role named "Billing Viewer" already exists
WHEN `POST /api/v1/roles` is called with the same name
THEN the response is 409 Conflict

---

### Requirement: Update Custom Role

The system SHALL expose `PATCH /api/v1/roles/{role_id}` allowing super_admin
to rename or update the description of a non-system role. System roles MAY have
their description updated but their name is immutable.

#### Scenario: Super admin renames a custom role

GIVEN a custom role with `is_system = false`
WHEN `PATCH /api/v1/roles/{role_id}` is called with `{"name": "Finance Viewer Extended"}`
THEN the response is 200 with the updated name

#### Scenario: System role name cannot be changed

GIVEN a role with `is_system = true`
WHEN `PATCH /api/v1/roles/{role_id}` is called with `{"name": "new name"}`
THEN the response is 409 Conflict with detail "System role names are immutable"

---

### Requirement: Delete Custom Role

The system SHALL expose `DELETE /api/v1/roles/{role_id}` allowing super_admin
to delete a custom role. Deletion SHALL be rejected if the role has active users
assigned or if the role is a system role.

#### Scenario: Custom role with no users is deleted

GIVEN a custom role with no users assigned
WHEN `DELETE /api/v1/roles/{role_id}` is called
THEN the response is 204 No Content and the role no longer appears in `GET /roles`

#### Scenario: Custom role with active users cannot be deleted

GIVEN a custom role with one or more active users assigned
WHEN `DELETE /api/v1/roles/{role_id}` is called
THEN the response is 409 Conflict with detail "Role has active users assigned"

---

### Requirement: Get Role Permission Matrix

The system SHALL expose `GET /api/v1/roles/{role_id}/permissions` returning
one row per resource (all 12 defined resources), each with `resource`,
`can_read`, `can_write`, and `team_scoped`. Missing rows SHALL be returned
as `can_read: false, can_write: false, team_scoped: false`.

#### Scenario: Permission matrix is complete for every role

GIVEN any existing role_id
WHEN `GET /api/v1/roles/{role_id}/permissions` is called by super_admin
THEN the response is 200 with exactly 12 items, one per resource key

---

### Requirement: Replace Role Permission Matrix

The system SHALL expose `PUT /api/v1/roles/{role_id}/permissions` accepting
a list of permission objects and atomically replacing the full permission
matrix for that role. After write, the permission cache for that role_id
SHALL be invalidated.

#### Scenario: Super admin updates a role's permissions

GIVEN a custom role with all permissions denied
WHEN `PUT /api/v1/roles/{role_id}/permissions` is called with
`[{"resource": "reports", "can_read": true, "can_write": false, "team_scoped": false}]`
THEN the response is 200
AND subsequent calls to `GET /api/v1/reports` by a user with that role return 200

#### Scenario: Invalid resource key is rejected

GIVEN a super_admin authenticated user
WHEN `PUT /api/v1/roles/{role_id}/permissions` is called with
`[{"resource": "nonexistent_page", "can_read": true}]`
THEN the response is 422 Unprocessable Entity

---

### Requirement: Assign Role to User

The system SHALL allow super_admin to assign any existing role_id to a user
via `PATCH /api/v1/users/{user_id}`. The `role_id` field SHALL replace the
legacy `role` string field in the request body.

#### Scenario: Super admin assigns a custom role to a user

GIVEN a custom role and an existing user
WHEN `PATCH /api/v1/users/{user_id}` is called with `{"role_id": "<custom_role_id>"}`
THEN the response is 200 and subsequent permission checks for that user
use the new role's permission matrix
