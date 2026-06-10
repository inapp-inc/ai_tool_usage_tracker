# Tasks: User Management Backend

Reference [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md). Depends on change `authentication-backend`.

---

## 1. OpenAPI extension

- [ ] 1.1 Add `Users` tag and paths: `GET/POST /users`, `GET/PATCH /users/{userId}` to `openapi.yaml`
- [ ] 1.2 Add schemas: `User`, `UserCreateRequest`, `UserUpdateRequest`, `UserListResponse` to `components/schemas.yaml`
- [ ] 1.3 Add examples and document role requirements per endpoint
- [ ] 1.4 Run `@redocly/cli lint` on updated OpenAPI

## 2. Admin schema (admin-schema-teams spec)

- [ ] 2.1 Create Alembic revision `003_admin_teams`: `admin.teams`, `admin.team_memberships`
- [ ] 2.2 Add unique constraints: team name per org, active membership per user-team pair
- [ ] 2.3 Implement SQLAlchemy models in `backend/app/models/admin.py`
- [ ] 2.4 Implement `TeamRepository`, `TeamMembershipRepository`

## 3. RBAC policies (minimal PLT-002)

- [ ] 3.1 Create `backend/app/admin/policies.py`: `require_super_admin`, `require_auditor_or_super_admin`, `require_team_admin_for(team_id)`
- [ ] 3.2 Implement Team Admin scope per ADR-015 (active membership check)
- [ ] 3.3 Wire policies into user and team routers

## 4. Platform user admin (platform-user-admin spec)

- [ ] 4.1 Create Pydantic schemas mirroring OpenAPI user models
- [ ] 4.2 Implement `UserAdminService`: list, create, get, update (reuse auth password hashing)
- [ ] 4.3 Implement `GET/POST /api/v1/users` and `GET/PATCH /api/v1/users/{userId}`
- [ ] 4.4 Enforce organization scoping; cross-org returns 404
- [ ] 4.5 Emit audit hook events on user create/update

## 5. Team management (team-management spec)

- [ ] 5.1 Implement `TeamService`: list, create, get, update, deactivate guard helper
- [ ] 5.2 Implement `GET/POST /api/v1/teams`, `GET/PATCH /api/v1/teams/{teamId}` per OpenAPI
- [ ] 5.3 Implement `GET/POST /api/v1/teams/{teamId}/members`, `DELETE .../members/{userId}` with soft remove
- [ ] 5.4 Emit audit hook events on team and membership mutations

## 6. Auth integration

- [ ] 6.1 Update `/auth/me` to load active `team_ids` from `admin.team_memberships`
- [ ] 6.2 Verify JWT role claim refreshed on next login after user role PATCH

## 7. Tests — admin-schema-teams

- [ ] 7.1 `tests/integration/test_admin_teams_migration.py` — migration + constraints
- [ ] 7.2 `tests/integration/test_team_membership_repository.py` — soft removal
- [ ] 7.3 `tests/integration/test_team_members.py` — duplicate and re-add scenarios

## 8. Tests — platform-user-admin

- [ ] 8.1 `tests/integration/test_users_api.py` — list, create, get, update, 403, 409, cross-org 404, deactivate

## 9. Tests — team-management

- [ ] 9.1 `tests/integration/test_teams_api.py` — team CRUD and duplicate name
- [ ] 9.2 `tests/integration/test_team_members.py` — multi-team, TA add/forbidden, remove
- [ ] 9.3 `tests/unit/test_team_service.py` — deactivated team guard
- [ ] 9.4 `tests/integration/test_auth_me_teams.py` — team_ids on /auth/me

## 10. Documentation

- [ ] 10.1 Update README with user/team admin API examples
- [ ] 10.2 Document Team Admin scope model (ADR-015) in admin section

## 11. Verification & Evidence

- [ ] 11.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 11.2 Collect functional evidence for each scenario — populate verification.md § Evidence Log
- [ ] 11.3 Confirm Hallucination Risk mitigations in verification.md § Hallucination Risk Register
- [ ] 11.4 Confirm ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 11.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer)
- [ ] 11.6 Run `openspec validate user-management-backend --type change --strict` before archive
