# Spec: Permission Enforcement

## ADDED Requirements

### Requirement: Generic Permission Dependency Factory

The system SHALL provide a `require_permission(resource: str, action: str)`
factory function in `backend/app/core/permissions.py` that returns a FastAPI
`Depends`-compatible async callable. The factory SHALL be used in router
endpoint signatures to replace all existing role-specific guards from `rbac.py`.
Valid actions are `"read"` and `"write"`.

#### Scenario: Super admin always passes permission check

GIVEN a user with the super_admin system role
WHEN any API endpoint guarded by `require_permission(resource, action)` is called
THEN the check passes without a database lookup and the user object is returned

#### Scenario: User with read permission can call read-guarded endpoint

GIVEN a user whose role has `can_read = true` for resource `alerts`
WHEN they call a `GET /api/v1/alerts` endpoint guarded by
`require_permission("alerts", "read")`
THEN the response is 200

#### Scenario: User without read permission is denied

GIVEN a user whose role has `can_read = false` for resource `alerts`
WHEN they call a `GET /api/v1/alerts` endpoint guarded by
`require_permission("alerts", "read")`
THEN the response is 403 Forbidden

#### Scenario: Write permission implies read

GIVEN a user whose role has `can_write = true` and `can_read = false` for
resource `uploads` (misconfigured row)
WHEN the enforcement layer checks read access to `uploads`
THEN access is granted (can_write = true overrides can_read = false)

#### Scenario: User with write permission can call write-guarded endpoint

GIVEN a user whose role has `can_write = true` for resource `members`
WHEN they call `POST /api/v1/users` guarded by
`require_permission("members", "write")`
THEN the response is 201

#### Scenario: User without write permission is denied on write endpoint

GIVEN a user whose role has `can_read = true` but `can_write = false` for
resource `members`
WHEN they call `POST /api/v1/users` guarded by
`require_permission("members", "write")`
THEN the response is 403 Forbidden

---

### Requirement: Team Scoping via Permission Flag

For resources where `team_scoped = true` on the role's permission row, the
enforcement layer SHALL inject managed team IDs so that data is filtered to
the teams the user belongs to. Resources eligible for team scoping are:
`insights`, `alerts`, `uploads`, `members`, `collectors`.

#### Scenario: Team-scoped role receives filtered data

GIVEN a user whose role has `can_read = true` and `team_scoped = true`
for resource `alerts`, and the user is a member of Team A
WHEN they call `GET /api/v1/thresholds`
THEN only alerts belonging to Team A are returned

#### Scenario: Non-team-scoped role receives all data

GIVEN a user whose role has `can_read = true` and `team_scoped = false`
for resource `alerts`
WHEN they call `GET /api/v1/thresholds`
THEN alerts for all teams in the organisation are returned

---

### Requirement: Permission Cache

The system SHALL cache permission lookups in an in-process TTL cache keyed by
`role_id`, with a TTL of 60 seconds. The cache SHALL be invalidated for a
given `role_id` whenever its `role_permissions` rows are written (via
`PUT /api/v1/roles/{role_id}/permissions`). The cache SHALL NOT be shared
across API worker processes; each process maintains its own cache.

#### Scenario: Permission result is served from cache on repeated calls

GIVEN a user makes two consecutive requests within 60 seconds
WHEN the permission check runs on the second request
THEN only one database query is issued for that role_id across both requests

#### Scenario: Cache is invalidated after permission update

GIVEN a role's permissions are updated via
`PUT /api/v1/roles/{role_id}/permissions`
WHEN the next request arrives for a user with that role_id
THEN the enforcement layer performs a fresh database lookup (cache miss)
and returns the updated permission result
