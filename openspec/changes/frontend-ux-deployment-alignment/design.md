# Design: Frontend UX, Terminology, and Deployment Alignment

## UI terminology vs API resources

| UI label | Route | Page component | Backend API | DB entity |
|----------|-------|----------------|-------------|-----------|
| **Teams** | `/admin/teams` | `ToolsPage` | `GET/POST /api/v1/tools` | `admin.tools` |
| **Groups** | `/admin/groups` | `TeamsPage` | `GET/POST /api/v1/teams` | `admin.teams` |
| **Members** | `/admin/members` | `MembersPage` | `/api/v1/members` | `auth.users` + memberships |
| **Credentials** | `/admin/credentials` | `CredentialsPage` | `/api/v1/credentials` | `admin.credentials` |

Legacy redirect: `/admin/tools` → `/admin/teams`.

Alert and dashboard copy uses the same vocabulary:

- Scope **Group** → `scope: "team"` + `team_id` = group UUID
- Scope **Team** → `scope: "tool"` + `team_id` = API team (tool) UUID
- Insights **Usage by Team** → `GET /dashboard/usage-by-team` returns rows from `admin.tools.pricing_config`

## Auth session persistence

```
Browser load → AuthProvider reads sessionStorage tokens
            → GET /auth/me if access token present
            → restore Zustand auth store OR clear invalid tokens
```

- Access and refresh tokens persisted in `sessionStorage` (tab-scoped)
- Root `/` and authenticated guest routes redirect to `/insights`
- Post-login default: `/insights` (all roles in current implementation)

## Production frontend gateway

```
Browser → :4501 (frontend container nginx)
          ├─ /aitool/           → SPA static (Vite build, basename /aitool)
          └─ /aitool/api/v1/    → reverse proxy → api:8000/api/v1/
```

Build args / env:

- `VITE_BASE_PATH=/aitool`
- `VITE_API_BASE_URL=/aitool/api/v1`
- `APP_PORT=4501` (host publish)

`docker-compose.prod.yml` hides direct API port exposure; CORS allows production origin.

## Dashboard usage-by-team

`DashboardService.get_usage_by_team` aggregates per **tool**:

1. Filter active tools (optional `tool_id` query param)
2. Sum `daily_usage` rows within `from`/`to` when present
3. Else fall back to `token_count` / `cost_total` in `pricing_config`

Response shape unchanged (`team_id`, `team_name`) for frontend compatibility.

## Groups (teams API) create flow

`POST /api/v1/teams` requires `Team` and `AuthenticatedUser` imports in `TeamService.create_team`. Assigned API teams (`settings.toolIds`) are optional on create.

## CSV-imported teams

Tools with `ingestion_source: "csv"`:

- Hide sync/refresh in UI
- Backend `sync_tool` rejects refresh

Uploads module supports `inspect` and `preview` with column mapping (shared `CsvColumnMappingFields` component).
