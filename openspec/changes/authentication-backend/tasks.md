# Tasks: Authentication Backend

Implementation checklist for change `authentication-backend`. Reference [design.md](./design.md), [specs](./specs/), and [verification.md](./verification.md).

---

## 1. Foundation prerequisites (minimal INF-002 / INF-004)

- [ ] 1.1 Add Alembic configuration (`alembic.ini`, `backend/alembic/env.py`) with async SQLAlchemy engine from settings
- [ ] 1.2 Add `backend/app/db/session.py` and `backend/app/db/base.py` for async session factory
- [ ] 1.3 Create `backend/app/api/v1/router.py` mounting sub-routers; register on FastAPI app
- [ ] 1.4 Move health endpoint to `GET /api/v1/health`; keep root redirect or deprecation note if needed
- [ ] 1.5 Extend `Settings` with JWT, rate-limit, and dev seed variables per design.md
- [ ] 1.6 Update `.env.example` and README with new auth/JWT environment variables

## 2. Auth schema (auth-schema spec)

- [ ] 2.1 Create Alembic revision `002_auth`: schema `auth`, tables `organizations`, `users`, `refresh_tokens`
- [ ] 2.2 Add CHECK constraints: `chk_retention_months`, `chk_retention_audit_months`, `chk_user_role`, `uq_users_org_email`
- [ ] 2.3 Implement SQLAlchemy models in `backend/app/models/auth.py`
- [ ] 2.4 Implement repositories: `OrganizationRepository`, `UserRepository`, `RefreshTokenRepository`
- [ ] 2.5 Add dev seed script `backend/app/scripts/seed_dev_admin.py` (guarded by `ENVIRONMENT=development`)
- [ ] 2.6 Wire migration run in Docker Compose (one-shot `migrate` service or API startup in dev)

## 3. Security core

- [ ] 3.1 Implement `backend/app/core/security.py`: Argon2id hash/verify, JWT encode/decode (PyJWT HS256)
- [ ] 3.2 Implement `backend/app/core/rate_limit.py`: Redis sliding window for login failures
- [ ] 3.3 Implement `backend/app/core/exceptions.py`: Problem Details handlers for 401/429
- [ ] 3.4 Add startup validation: fail if `JWT_SECRET_KEY` missing in non-dev environments

## 4. Auth service and API (jwt-authentication spec)

- [ ] 4.1 Create Pydantic schemas mirroring OpenAPI: `LoginRequest`, `TokenResponse`, `RefreshRequest`, `UserProfile`
- [ ] 4.2 Implement `AuthService`: authenticate, issue tokens, refresh with rotation, get profile
- [ ] 4.3 Implement `backend/app/auth/dependencies.py`: `get_current_user` JWT dependency
- [ ] 4.4 Implement `POST /api/v1/auth/login` with rate limiting and Problem Details errors
- [ ] 4.5 Implement `POST /api/v1/auth/refresh` with token rotation per ADR-014
- [ ] 4.6 Implement `GET /api/v1/auth/me` returning UserProfile (`team_ids` empty until DB-002)
- [ ] 4.7 Register auth router under `/api/v1/auth` in OpenAPI tags

## 5. Docker and compose integration

- [ ] 5.1 Update `backend/Dockerfile` / `requirements.txt` with new dependencies (PyJWT, argon2-cffi, alembic, sqlalchemy, asyncpg)
- [ ] 5.2 Add Compose migration step or document `docker compose run --rm api alembic upgrade head`
- [ ] 5.3 Verify full stack: migrate → seed → login → me via curl against running Compose

## 6. Tests — auth-schema scenarios

- [ ] 6.1 `tests/integration/test_auth_migration.py` — migration applies on empty DB (Spec: Migration applies)
- [ ] 6.2 `tests/unit/test_refresh_token_repository.py` — hash-only storage (Spec: Refresh token hash only)
- [ ] 6.3 `tests/integration/test_auth_migration.py` — retention constraints (Spec: Organization retention)
- [ ] 6.4 `tests/integration/test_auth_migration.py` — valid/invalid roles (Spec: Role enum / invalid rejected)
- [ ] 6.5 `tests/integration/test_dev_seed.py` — dev seed creates Super Admin (Spec: Seed on empty)

## 7. Tests — jwt-authentication scenarios

- [ ] 7.1 `tests/integration/test_auth_login.py` — success, invalid credentials, inactive user
- [ ] 7.2 `tests/integration/test_auth_refresh.py` — success with rotation, invalid token
- [ ] 7.3 `tests/integration/test_auth_me.py` — authenticated profile, unauthorized
- [ ] 7.4 `tests/integration/test_auth_jwt.py` — expired token returns 401
- [ ] 7.5 `tests/integration/test_auth_rate_limit.py` — 429 after threshold
- [ ] 7.6 `tests/unit/test_settings.py` — missing JWT secret fails startup

## 8. Verification & Evidence

- [ ] 8.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 8.2 Collect functional evidence (test output) for each scenario — one entry per row in verification.md § Evidence Log
- [ ] 8.3 Confirm every Hallucination Risk mitigation step in verification.md § Hallucination Risk Register
- [ ] 8.4 Confirm all ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 8.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer required)
- [ ] 8.6 Run `openspec validate authentication-backend --type change --strict` before archive
