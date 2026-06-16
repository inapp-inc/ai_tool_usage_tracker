# Auth backend implementation status

Updated **2026-06-16** — first slice aligned with [frontend-mapping.md](../../specifications/apis/frontend-mapping.md).

## Completed

- [x] Alembic `002_auth` — `auth.organizations`, `auth.users`, `auth.refresh_tokens`
- [x] SQLAlchemy models (`app/models/auth.py`)
- [x] Repositories + `AuthService` (login, refresh with rotation, profile)
- [x] `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`
- [x] Argon2id passwords, JWT access tokens (HS256), hashed refresh tokens
- [x] Dev seed: `admin@example.com` / `DEV_SUPER_ADMIN_PASSWORD` on empty DB
- [x] Frontend `auth.ts` wired to backend (login → tokens → `/auth/me`)
- [x] Unit tests: `tests/test_security.py`

## Deferred

- [ ] Redis login rate limiting (`429`)
- [ ] `team_ids` on `/auth/me` (requires team membership schema)
- [ ] Protect collector/usage routes with `get_current_user`

## Default dev credentials

| Variable | Default |
|----------|---------|
| `DEV_SUPER_ADMIN_EMAIL` | `admin@example.com` |
| `DEV_SUPER_ADMIN_PASSWORD` | `change_me_dev_only` |

Password must be 8–128 characters (OpenAPI `LoginRequest`).
