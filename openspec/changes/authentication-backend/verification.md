# Verification Plan: Authentication Backend

Gate artifact for change `authentication-backend`. Evidence Log and Audit Record are completed by a human reviewer during/after apply — do not pre-check.

---

## 1. Spec Alignment

### auth-schema

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Auth schema tables exist | Migration applies on empty database | Given empty PostgreSQL, when migration `002_auth` runs, then `auth` schema with three tables exists and constraints apply | `tests/integration/test_auth_migration.py` | ☐ |
| Auth schema tables exist | Refresh token record stores hash only | Given issued refresh token, when persisted, then DB contains hash only not plaintext | `tests/unit/test_refresh_token_repository.py` | ☐ |
| Organization tenant root | Organization retention constraints | Given retention < 24 months, when insert/update, then constraint violation | `tests/integration/test_auth_migration.py::test_retention_constraints` | ☐ |
| User account with RBAC role | User role enum validation | Given valid role enum, when insert, then succeeds | `tests/integration/test_auth_migration.py::test_valid_roles` | ☐ |
| User account with RBAC role | Invalid user role rejected | Given invalid role, when insert, then rejected | `tests/integration/test_auth_migration.py::test_invalid_role_rejected` | ☐ |
| Dev seed creates default Super Admin | Seed on empty auth tables | Given empty auth tables in dev, when seed runs, then org + Super Admin created from env password | `tests/integration/test_dev_seed.py` | ☐ |

### jwt-authentication

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| User login with JWT issuance | Successful login | Given active user + valid credentials, when POST login, then 200 with Bearer access token and expires_in | `tests/integration/test_auth_login.py::test_login_success` | ☐ |
| User login with JWT issuance | Invalid credentials | Given wrong password, when POST login, then 401 Problem Details | `tests/integration/test_auth_login.py::test_login_invalid_credentials` | ☐ |
| User login with JWT issuance | Inactive user login blocked | Given inactive user, when login, then 401 | `tests/integration/test_auth_login.py::test_login_inactive_user` | ☐ |
| Access token refresh with rotation | Successful token refresh | Given valid refresh token, when POST refresh, then 200 with new tokens and old token revoked | `tests/integration/test_auth_refresh.py::test_refresh_success` | ☐ |
| Access token refresh with rotation | Invalid refresh token | Given bad refresh token, when POST refresh, then 401 | `tests/integration/test_auth_refresh.py::test_refresh_invalid` | ☐ |
| Current user profile | Authenticated profile retrieval | Given valid JWT, when GET /auth/me, then 200 UserProfile with id, email, role, org_id, team_ids | `tests/integration/test_auth_me.py::test_me_success` | ☐ |
| Current user profile | Unauthenticated profile request | Given no/invalid token, when GET /auth/me, then 401 | `tests/integration/test_auth_me.py::test_me_unauthorized` | ☐ |
| Expired JWT rejected | Expired access token | Given expired JWT, when protected request, then 401 | `tests/integration/test_auth_jwt.py::test_expired_token` | ☐ |
| Login rate limiting | Login throttled after threshold | Given > threshold failed attempts, when another login, then 429 | `tests/integration/test_auth_rate_limit.py::test_login_throttled` | ☐ |
| JWT signing key from environment | Missing JWT secret prevents startup | Given missing JWT_SECRET_KEY in prod mode, when app starts, then startup fails | `tests/unit/test_settings.py::test_jwt_secret_required` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| OpenAPI path prefix | Implement `/auth/login` without `/api/v1` prefix | Contract test compares paths to `openapi.yaml`; manual review of router mount |
| Password field naming | Use `hashed_password` instead of `password_hash` column | Integration test inserts user and verifies column name via repository |
| Refresh token storage | Store plaintext or JWT instead of opaque hash | Unit test asserts DB value ≠ client token and matches SHA-256 |
| Role enum values | Use `SUPER_ADMIN` instead of `super_admin` | Migration test + login response role matches OpenAPI enum |
| Problem Details shape | Return plain JSON error without `type`/`title`/`status` | Assert response Content-Type and schema in 401 tests |
| Rate limit key scope | Rate limit success responses or use wrong Redis DB | Test only increments on 401; verify Redis key pattern in unit test |
| JWT claims | Omit `org` or `role` claims breaking downstream RBAC | Decode token in test and assert required claims present |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-001 | Auth as bounded context in modular monolith | Code review: `backend/app/auth/` package exists; no auth logic in unrelated modules |
| ADR-002 | FastAPI implementation | Integration tests hit FastAPI TestClient/httpx against running app |
| ADR-003 | PostgreSQL auth schema | Migration test on real Postgres (Compose service) |
| ADR-005 | JWT auth, no SSO Phase 1 | No SSO routes; login is email/password only |
| ADR-012 | OpenAPI contract | Schemathesis or manual contract test against `/auth/*` operations |
| ADR-013 | Secrets from `.env` / Compose | Review: no secrets in code; `.env.example` documents JWT vars |
| ADR-014 | Opaque refresh + hash + rotation | Refresh integration test verifies old token revoked after rotation |

---

## 4. Evidence Requirements

### Functional

- [ ] Migration applies on empty database — pytest output showing `002_auth` success
- [ ] Refresh token hash-only storage — unit test output showing hash ≠ plaintext
- [ ] Organization retention constraints — pytest constraint violation
- [ ] Valid role enum insert — pytest pass
- [ ] Invalid role rejected — pytest pass
- [ ] Dev seed creates Super Admin — pytest or script log with user id
- [ ] Successful login — HTTP 200 + TokenResponse fields in test output
- [ ] Invalid credentials — HTTP 401 Problem Details in test output
- [ ] Inactive user blocked — HTTP 401 in test output
- [ ] Successful refresh with rotation — HTTP 200 + old token revoked in DB
- [ ] Invalid refresh token — HTTP 401 in test output
- [ ] Authenticated /auth/me — HTTP 200 UserProfile in test output
- [ ] Unauthenticated /auth/me — HTTP 401 in test output
- [ ] Expired JWT — HTTP 401 in test output
- [ ] Login rate limit — HTTP 429 in test output
- [ ] Missing JWT secret startup failure — test or manual startup log

### Structural

- [ ] Code review confirms design.md module structure and decisions
- [ ] ADR-014 compliance verified in refresh token implementation

### Edge Case (Hallucination Risks)

- [ ] OpenAPI path prefix verified (`/api/v1/auth/*`)
- [ ] Problem Details format verified on auth errors
- [ ] JWT claims include `sub`, `org`, `role`, `exp`

---

## 5. Evidence Log

| Scenario | Evidence Type | Location / Link | Collected By | Date |
|----------|---------------|-----------------|--------------|------|
| _TBD_ | _TBD_ | _TBD_ | | |
| _TBD_ | _TBD_ | _TBD_ | | |

---

## 6. Audit Record

Human reviewer sign-off required before archive.

- [ ] All Spec Alignment rows marked pass with evidence
- [ ] Evidence Log populated for every scenario
- [ ] Hallucination Risk mitigations confirmed
- [ ] ADR compliance steps confirmed
- [ ] No scope creep beyond proposal (RBAC matrix deferred to PLT-002)

**Reviewer:** _______________  
**Date:** _______________
