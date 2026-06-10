# Verification Plan: User Management Backend

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### admin-schema-teams

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Admin teams schema migration | Migration applies after auth schema | Given auth schema applied, when 003_admin_teams runs, then admin.teams and admin.team_memberships exist with unique team name per org | `tests/integration/test_admin_teams_migration.py` | ☐ |
| Admin teams schema migration | Soft membership removal column | Given active membership, when removed, then row kept with removed_at set | `tests/integration/test_team_membership_repository.py` | ☐ |
| Multi-team membership uniqueness | Duplicate active membership rejected | Given active membership U on T, when add U to T again, then conflict | `tests/integration/test_team_members.py::test_duplicate_member` | ☐ |
| Multi-team membership uniqueness | Re-add after soft removal | Given removed membership, when re-add U to T, then active membership restored | `tests/integration/test_team_members.py::test_readd_member` | ☐ |

### platform-user-admin

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| List organization users | Super Admin lists users | Given Super Admin, when GET /users, then 200 with id/email/role/active | `tests/integration/test_users_api.py::test_list_users` | ☐ |
| List organization users | Non-admin list denied | Given Team Member, when GET /users, then 403 | `tests/integration/test_users_api.py::test_list_users_forbidden` | ☐ |
| Create organization user | Successful user creation | Given Super Admin + unique email, when POST /users, then 201 and hashed password in DB | `tests/integration/test_users_api.py::test_create_user` | ☐ |
| Create organization user | Duplicate email rejected | Given existing email, when POST /users, then 409 | `tests/integration/test_users_api.py::test_create_duplicate` | ☐ |
| Update organization user | Deactivate user | Given active user, when PATCH active false, then login fails and history preserved | `tests/integration/test_users_api.py::test_deactivate_user` | ☐ |
| Update organization user | Role update | Given team_member, when PATCH role team_admin, then role persisted | `tests/integration/test_users_api.py::test_update_role` | ☐ |
| Get user by id | Super Admin retrieves user | Given same-org user, when GET /users/{id}, then 200 | `tests/integration/test_users_api.py::test_get_user` | ☐ |
| Get user by id | Cross-organization access denied | Given other-org user id, when GET, then 404 | `tests/integration/test_users_api.py::test_get_user_cross_org` | ☐ |

### team-management

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Team CRUD for Super Admin | Create team with unique name | Given Super Admin, when POST /teams unique name, then 201 and listed | `tests/integration/test_teams_api.py::test_create_team` | ☐ |
| Team CRUD for Super Admin | Duplicate team name rejected | Given existing name, when POST duplicate, then 409 | `tests/integration/test_teams_api.py::test_duplicate_team` | ☐ |
| Team CRUD for Super Admin | Deactivate team | Given active team, when PATCH active false, then attribution guard returns false | `tests/unit/test_team_service.py::test_deactivated_team` | ☐ |
| Team member assignment | Assign user to multiple teams | Given user U and teams T1 T2, when add to both, then both memberships active | `tests/integration/test_team_members.py::test_multi_team` | ☐ |
| Team member assignment | Team Admin adds member to administered team | Given TA member of T, when add user, then 201 | `tests/integration/test_team_members.py::test_ta_add_member` | ☐ |
| Team member assignment | Team Admin denied on non-member team | Given TA not member of T, when add member, then 403 | `tests/integration/test_team_members.py::test_ta_forbidden` | ☐ |
| Soft remove team member | Remove member preserves history | Given member with history, when DELETE member, then 204 and removed_at set | `tests/integration/test_team_members.py::test_remove_member` | ☐ |
| Auth profile reflects team membership | Me endpoint team ids | Given memberships T1 T2, when GET /auth/me, then team_ids contains both | `tests/integration/test_auth_me_teams.py` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| OpenAPI paths | Omit `/api/v1` prefix on users/teams | Contract test path list vs openapi.yaml |
| Team Admin scope | Allow TA to manage any org team | Integration test TA forbidden on non-member team |
| Soft delete | Hard DELETE membership row | Assert row exists with removed_at after DELETE |
| Tenant isolation | Return 403 for cross-org id | Test expects 404 for other-org user/team |
| User password in response | Return password_hash in API | Assert response schema excludes password fields |
| Role enum | Wrong casing vs OpenAPI Role enum | Assert stored and returned values match schema |
| /auth/me team_ids | Leave empty after membership add | Dedicated me+teams integration test |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-001 | Admin bounded context | Code review: `backend/app/admin/` structure |
| ADR-005 | Server-side RBAC | 403 tests for unauthorized roles |
| ADR-012 | OpenAPI contract | Redocly lint + team endpoint contract tests |
| ADR-015 | TA scope via membership | `test_ta_add_member` and `test_ta_forbidden` pass |

---

## 4. Evidence Requirements

### Functional

- [ ] All 20 Spec Alignment scenarios — pytest output attached per row
- [ ] OpenAPI updated with Users tag and schemas — Redocly lint clean

### Structural

- [ ] Code review confirms design.md package layout and tenant isolation
- [ ] ADR-015 compliance verified in `admin/policies.py`

### Edge Case

- [ ] Cross-org 404 behavior verified
- [ ] Soft removal preserves membership row
- [ ] Deactivated team attribution guard verified

---

## 5. Evidence Log

| Scenario | Evidence Type | Location / Link | Collected By | Date |
|----------|---------------|-----------------|--------------|------|
| _TBD_ | _TBD_ | _TBD_ | | |

---

## 6. Audit Record

- [ ] All Spec Alignment rows pass with evidence
- [ ] Evidence Log complete
- [ ] Hallucination mitigations confirmed
- [ ] ADR compliance confirmed
- [ ] Scope limited to user/team admin (no tools/credentials)

**Reviewer:** _______________  
**Date:** _______________
