# Spec: Role Settings UI

## ADDED Requirements

### Requirement: Settings Roles Page

The system SHALL provide a Settings > Roles page accessible only to super_admin.
The page SHALL render a matrix table with resources as rows and roles as columns.
Each cell SHALL display read and write toggles. Changes SHALL be saved immediately
on toggle (auto-save via `PUT /api/v1/roles/{role_id}/permissions`).

#### Scenario: Super admin sees the full role matrix on page load

GIVEN a super_admin user navigates to `/settings/roles`
WHEN the page loads
THEN a table is displayed with 12 resource rows and one column per role
AND each cell shows the current `can_read` and `can_write` state as toggles

#### Scenario: System role column shows lock icon

GIVEN the role matrix table is displayed
WHEN a column corresponds to a system role (`is_system = true`)
THEN a lock icon is displayed in the column header
AND the role name cannot be edited inline

#### Scenario: Toggle triggers immediate save

GIVEN a super_admin is viewing the role matrix
WHEN they toggle `can_read` for resource `reports` on a custom role
THEN a `PUT /api/v1/roles/{role_id}/permissions` request is fired immediately
AND the toggle shows a saving indicator during the request
AND reverts to the previous state if the request fails

#### Scenario: Non-super-admin cannot access roles settings page

GIVEN a user with any role other than super_admin
WHEN they navigate to `/settings/roles`
THEN they are redirected to `/insights`

---

### Requirement: Create New Role

The system SHALL provide a "+ New Role" button on the Settings > Roles page
that opens a modal for naming and describing a new custom role. On confirmation,
`POST /api/v1/roles` is called and the new column appears in the matrix.

#### Scenario: Super admin creates a new role via UI

GIVEN the super_admin is on the Settings > Roles page
WHEN they click "+ New Role", enter "Billing Viewer" and click Save
THEN `POST /api/v1/roles` is called
AND a new column titled "Billing Viewer" appears in the matrix with all toggles off

#### Scenario: Empty role name is blocked

GIVEN the new role modal is open
WHEN the super_admin submits without entering a name
THEN the form shows a validation error and no API call is made

---

### Requirement: User Role Assignment

The system SHALL allow super_admin to assign a role to a user from the member
edit form. The role field SHALL be a dropdown populated from `GET /api/v1/roles`
showing both system and custom roles by name.

#### Scenario: Role dropdown shows all available roles

GIVEN a super_admin opens the edit form for a user
WHEN the role dropdown is rendered
THEN it shows all roles returned by `GET /api/v1/roles`

#### Scenario: Super admin reassigns a user to a custom role

GIVEN a user currently assigned to the `team_member` system role
WHEN the super_admin selects "Billing Viewer" from the role dropdown and saves
THEN `PATCH /api/v1/users/{user_id}` is called with the custom role's `role_id`
AND the user's role label in the member list updates to "Billing Viewer"

---

### Requirement: Frontend Route Guard Update

The system SHALL update `RoleGuard` and sidebar navigation to use permission
checks rather than hardcoded role name comparisons. Pages SHALL be shown or
hidden based on whether the current user's role has `can_read = true` for the
corresponding resource.

#### Scenario: Sidebar item is hidden when role lacks read permission

GIVEN a user whose role has `can_read = false` for resource `reports`
WHEN the sidebar renders
THEN no "Reports" nav item is visible

#### Scenario: Direct URL navigation is blocked without read permission

GIVEN a user whose role has `can_read = false` for resource `audit_logs`
WHEN they navigate directly to `/admin/audit-log`
THEN they are redirected to `/insights`
