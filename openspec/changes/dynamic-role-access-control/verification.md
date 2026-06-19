# Verification: Dynamic Role Access Control

---

## Spec Alignment

| Spec | Requirement | Scenario | Acceptance Criterion | Verification Artifact | Status |
|---|---|---|---|---|---|
| role-permission-schema | Roles Table | System roles seeded on migration | Given fresh DB after migration, SELECT COUNT(*) FROM auth.roles WHERE is_system=true equals 5 | Migration + SQL query | [ ] |
| role-permission-schema | Roles Table | System role cannot be deleted | Given super_admin, DELETE /roles/{system_role_id} returns 409 | API test | [ ] |
| role-permission-schema | Roles Table | Custom role can be created | Given super_admin, POST /roles returns 201 with is_system: false | API test | [ ] |
| role-permission-schema | Role Permissions Table | Seeded permissions match current RBAC matrix | super_admin role has can_read=true and can_write=true for all 12 resources; finance_viewer only has read on reports and my_usage | SQL query / API test | [ ] |
| role-permission-schema | Role Permissions Table | Permission row is unique per role and resource | Duplicate insert raises unique constraint violation | DB constraint test | [ ] |
| role-permission-schema | Role Permissions Table | Missing permission row treated as denied | Role with no row for credentials gets 403 on GET /credentials | API test | [ ] |
| role-permission-schema | Users Table Migration | All users retain correct role after migration | Every user's role_id FK points to matching system role; zero NULL role_id rows | SQL query post-migration | [ ] |
| role-permission-schema | Users Table Migration | New user creation requires role_id | POST /users with valid role_id returns 201 | API test | [ ] |
| role-permission-schema | Users Table Migration | Deleting role with active users is rejected | DELETE /roles/{id} where users assigned returns 409 | API test | [ ] |
| permission-enforcement | Generic Permission Dependency | Super admin always passes | super_admin user calls any guarded endpoint, passes without DB lookup | API test + query count log | [ ] |
| permission-enforcement | Generic Permission Dependency | User with read permission can call read-guarded endpoint | Role with can_read=true for alerts, GET /thresholds returns 200 | API test | [ ] |
| permission-enforcement | Generic Permission Dependency | User without read permission is denied | Role with can_read=false for alerts, GET /thresholds returns 403 | API test | [ ] |
| permission-enforcement | Generic Permission Dependency | Write permission implies read | Role with can_write=true, can_read=false for uploads; read check passes | Unit test on enforcement logic | [ ] |
| permission-enforcement | Generic Permission Dependency | User with write permission on write endpoint | Role with can_write=true for members, POST /users returns 201 | API test | [ ] |
| permission-enforcement | Generic Permission Dependency | User without write permission denied on write endpoint | Role with can_read=true, can_write=false for members, POST /users returns 403 | API test | [ ] |
| permission-enforcement | Team Scoping via Permission Flag | Team-scoped role receives filtered data | Role with team_scoped=true on alerts; user in Team A only sees Team A alerts | API test with multi-team seed data | [ ] |
| permission-enforcement | Team Scoping via Permission Flag | Non-team-scoped role receives all data | Role with team_scoped=false on alerts; user sees all org alerts | API test | [ ] |
| permission-enforcement | Permission Cache | Permission result served from cache on repeated calls | Two requests within 60s issue only one DB query for that role_id | Unit test with mock session | [ ] |
| permission-enforcement | Permission Cache | Cache invalidated after permission update | PUT /roles/{id}/permissions; next request triggers fresh DB lookup | Integration test | [ ] |
| role-management-api | List Roles | Super admin retrieves role list | GET /roles returns 200 with ≥5 roles including all system roles | API test | [ ] |
| role-management-api | List Roles | Non-super-admin denied role list | Non-super-admin GET /roles returns 403 | API test | [ ] |
| role-management-api | Create Custom Role | Super admin creates a custom role | POST /roles returns 201; GET /roles/{id}/permissions returns 12 rows all false | API test | [ ] |
| role-management-api | Create Custom Role | Duplicate role name rejected | Second POST /roles with same name returns 409 | API test | [ ] |
| role-management-api | Update Custom Role | Super admin renames custom role | PATCH /roles/{id} with new name returns 200 | API test | [ ] |
| role-management-api | Update Custom Role | System role name cannot be changed | PATCH /roles/{system_id} with new name returns 409 | API test | [ ] |
| role-management-api | Delete Custom Role | Custom role with no users deleted | DELETE /roles/{id} returns 204; role absent from GET /roles | API test | [ ] |
| role-management-api | Delete Custom Role | Custom role with active users cannot be deleted | DELETE /roles/{id} with users assigned returns 409 | API test | [ ] |
| role-management-api | Get Role Permission Matrix | Matrix complete for every role | GET /roles/{id}/permissions returns exactly 12 items | API test | [ ] |
| role-management-api | Replace Role Permission Matrix | Super admin updates permissions | PUT /roles/{id}/permissions; user with that role now gets 200 on guarded endpoint | Integration test | [ ] |
| role-management-api | Replace Role Permission Matrix | Invalid resource key rejected | PUT with nonexistent resource returns 422 | API test | [ ] |
| role-management-api | Assign Role to User | Super admin assigns custom role to user | PATCH /users/{id} with role_id; subsequent permission checks use new role | Integration test | [ ] |
| role-settings-ui | Settings Roles Page | Super admin sees full matrix on load | Navigate to /settings/roles; table shows 12 rows × N role columns | Browser test / screenshot | [ ] |
| role-settings-ui | Settings Roles Page | System role column shows lock icon | Lock icon visible on is_system=true column headers | Browser test / screenshot | [ ] |
| role-settings-ui | Settings Roles Page | Toggle triggers immediate save | Toggle a permission; network tab shows PUT /roles/{id}/permissions | Browser test | [ ] |
| role-settings-ui | Settings Roles Page | Non-super-admin cannot access roles settings | Navigate to /settings/roles as non-super-admin; redirected to /insights | Browser test | [ ] |
| role-settings-ui | Create New Role | Super admin creates role via UI | Click + New Role, enter name, save; new column appears in matrix | Browser test | [ ] |
| role-settings-ui | Create New Role | Empty role name is blocked | Submit with empty name; validation error shown, no API call | Browser test | [ ] |
| role-settings-ui | User Role Assignment | Role dropdown shows all available roles | Open user edit form; dropdown contains all roles from GET /roles | Browser test | [ ] |
| role-settings-ui | User Role Assignment | Super admin reassigns user to custom role | Select custom role, save; PATCH /users/{id} called; member list shows new role | Browser test | [ ] |
| role-settings-ui | Frontend Route Guard Update | Sidebar item hidden when role lacks read | User with can_read=false on reports; Reports nav item not visible | Browser test | [ ] |
| role-settings-ui | Frontend Route Guard Update | Direct URL blocked without read permission | Navigate to /admin/audit-log with role lacking read on audit_logs; redirect to /insights | Browser test | [ ] |

---

## Hallucination Risk Register

| Risk | What an AI agent might get wrong | Mitigation |
|---|---|---|
| Column name drift | Agent invents `permission_read` / `permission_write` instead of `can_read` / `can_write` from spec | Verify migration SQL and ORM model column names match spec exactly before marking migration task complete |
| Cache not invalidated | Agent implements cache load but omits `invalidate()` call in the `PUT /permissions` endpoint | Explicitly test: update permissions, verify next request hits DB (mock session call count) |
| team_scoped flag ignored | Agent wires `require_permission` but drops `get_scoped_team_ids` and always returns unscoped data | Multi-team seed test: confirm team_admin role with team_scoped=true only returns own-team data |
| system role backfill mismatch | Agent seeds system roles with different name strings than the existing `USER_ROLES` tuple in `models/auth.py` | Run post-migration SQL: `SELECT r.name, COUNT(u.id) FROM auth.roles r LEFT JOIN auth.users u ON u.role_id=r.id GROUP BY r.name` — all users must be accounted for |
| Write implies read not enforced | Agent checks only `can_write` for write action but forgets the implication for read | Unit test: role with can_read=false, can_write=true; read-guarded endpoint must pass |
| Super admin DB lookup not skipped | Agent queries DB for super_admin permissions, defeating the bypass | Log DB query count for super_admin request; must be zero permission-table queries |
| Missing resource keys | Agent hardcodes fewer than 12 resource keys in the VALID_RESOURCES registry | `GET /roles/{id}/permissions` must return exactly 12 rows; add assertion in test |

---

## Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|---|---|---|
| ADR-001 | New `roles/` module must be a bounded context; no cross-context DB joins from routers | Code review: roles router imports only from `roles/`, `core/`, `models/`; no direct imports from other modules' repos |
| ADR-002 | FastAPI + Python only; no new frameworks | Code review: `permissions.py` uses only FastAPI `Depends`, SQLAlchemy, stdlib |
| ADR-003 | New tables in `auth` schema; UUID PKs; TIMESTAMPTZ | Inspect migration: `schema="auth"`, `UUID(as_uuid=True)` PKs, `DateTime(timezone=True)` columns |
| ADR-005 (superseded by ADR-020) | JWT-based auth preserved; RBAC moves to DB layer | JWT validation unchanged; permission check is DB lookup after JWT decode, not inside token |
| ADR-012 | OpenAPI spec updated alongside implementation | `openapi.yaml` must include `/roles` paths before `apply` is marked complete |
| ADR-013 | No new secrets or external dependencies for Phase 1 cache | `PermissionCache` uses stdlib `time.monotonic()`; no Redis connection added |

---

## Evidence Requirements

- [ ] SQL query result showing 5 system roles with is_system=true after migration
- [ ] SQL query result showing zero users with NULL role_id after migration backfill
- [ ] API test output: POST /roles → 201, GET /roles/{id}/permissions → 12 rows all false
- [ ] API test output: DELETE /roles/{system_role_id} → 409
- [ ] API test output: DELETE /roles/{custom_role_with_users} → 409
- [ ] API test output: role with can_read=false on alerts → GET /thresholds → 403
- [ ] API test output: role with can_read=true on alerts → GET /thresholds → 200
- [ ] API test output: role with team_scoped=true; only own-team data returned
- [ ] Unit test output: write-implies-read enforcement passes
- [ ] Unit test output: cache hit on second request (DB call count = 1 across 2 requests)
- [ ] Integration test output: PUT /permissions invalidates cache; next request hits DB
- [ ] Browser screenshot: /settings/roles matrix table with lock icons on system columns
- [ ] Browser screenshot: non-super-admin redirected from /settings/roles to /insights
- [ ] Browser screenshot: user edit form showing role dropdown with all roles
- [ ] Code review confirmation: all 12 router guard replacements applied per design table
- [ ] openapi.yaml diff showing new /roles paths

---

## Evidence Log

| Evidence Item | Artifact | Collected By | Date |
|---|---|---|---|
| (to be filled by reviewer) | | | |

---

## Audit Record

- [ ] All spec scenarios have passing verification artifacts
- [ ] All hallucination risks have been checked
- [ ] All ADR compliance steps confirmed
- [ ] Evidence Log populated with real evidence (no placeholder entries)
- [ ] OpenAPI spec updated and validated
- [ ] Human reviewer sign-off: _____________________ Date: ____________
