# Teams Backend — Implementation Status

**Status:** ✅ **Completed** (2026-06-16)

Aligned with [frontend-mapping.md](../../specifications/apis/frontend-mapping.md) — Teams section.

## Completed

- [x] OpenSpec change: [proposal](./proposal.md), [design](./design.md), [tasks](./tasks.md)
- [x] Migrations `004_admin_teams`, `005_team_form_fields`
- [x] SQLAlchemy `Team` model (`app/models/admin.py`)
- [x] `app/teams/` — repository, service, schemas, router
- [x] `GET/POST /api/v1/teams`, `GET/PATCH/DELETE /api/v1/teams/{teamId}`
- [x] JWT auth; writes restricted to `super_admin`
- [x] Duplicate team name → 409
- [x] Persist form fields: `token_budget`, `cost_budget`, `tool_ids`
- [x] Frontend `teams.ts` + `adapters/teams.ts` wired
- [x] Admin → Teams page (create, edit, delete)
- [x] Unit tests: `tests/test_teams_schemas.py`

## Out of scope (future slices)

- [ ] `admin.team_memberships` and `/teams/{id}/members` (Members module)
- [ ] `member_count` from DB (returns `0` until memberships)
- [ ] `tokenUsedThisMonth` / `costUsedThisMonth` (usage aggregates)
- [ ] `team_ids` on `/auth/me`
- [ ] Team Admin scoped writes
- [ ] Cursor pagination on list endpoint
- [ ] FK validation for `tool_ids` against `admin.tools`

## Verify

```bash
docker compose up --build postgres migrate api
# Login as super admin, then:
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/teams
```
