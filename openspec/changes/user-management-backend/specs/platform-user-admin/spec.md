# Platform User Admin — Delta Specification

## ADDED Requirements

### Requirement: List organization users

The system SHALL expose `GET /api/v1/users` returning paginated users scoped to the caller's organization.

#### Scenario: Super Admin lists users

- **GIVEN** an authenticated Super Admin
- **WHEN** `GET /api/v1/users` is called
- **THEN** the response status is 200
- **AND** each user includes `id`, `email`, `role`, `active`, and `display_name`

#### Scenario: Non-admin list denied

- **GIVEN** an authenticated Team Member
- **WHEN** `GET /api/v1/users` is called
- **THEN** the response status is 403 Forbidden

### Requirement: Create organization user

The system SHALL allow Super Admins to create users via `POST /api/v1/users` with email, role, optional display name, and initial password.

#### Scenario: Successful user creation

- **GIVEN** an authenticated Super Admin
- **WHEN** a valid user create request with unique email in the organization is submitted
- **THEN** the response status is 201
- **AND** the user is persisted in `auth.users` with hashed password
- **AND** the response body excludes the password

#### Scenario: Duplicate email rejected

- **GIVEN** an existing user email in the organization
- **WHEN** a create request uses the same email
- **THEN** the response status is 409 Conflict

### Requirement: Update organization user

The system SHALL allow Super Admins to update user role, display name, and active status via `PATCH /api/v1/users/{userId}`.

#### Scenario: Deactivate user

- **GIVEN** an active user
- **WHEN** Super Admin sets `active: false`
- **THEN** the user cannot authenticate
- **AND** historical records remain linked to the user id

#### Scenario: Role update

- **GIVEN** an active user with role `team_member`
- **WHEN** Super Admin updates role to `team_admin`
- **THEN** the new role is persisted
- **AND** subsequent JWT claims reflect the updated role on next login

### Requirement: Get user by id

The system SHALL expose `GET /api/v1/users/{userId}` for authorized administrators within the same organization.

#### Scenario: Super Admin retrieves user

- **GIVEN** a user in the same organization
- **WHEN** Super Admin calls `GET /api/v1/users/{userId}`
- **THEN** the response status is 200 with user details

#### Scenario: Cross-organization access denied

- **GIVEN** a user id belonging to another organization
- **WHEN** the request is made
- **THEN** the response status is 404 Not Found
