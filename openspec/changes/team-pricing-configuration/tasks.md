# Tasks: Team Pricing Configuration

## 1. Backend

- [x] 1.1 Alembic migration — create `admin.team_tools` table
- [x] 1.2 SQLAlchemy model `TeamTool`
- [x] 1.3 `TeamToolRepository`: create, update, delete, list by team
- [x] 1.4 API endpoints: `GET/POST /teams/{teamId}/tools`, `PATCH/DELETE /teams/{teamId}/tools/{toolId}`
- [x] 1.5 RBAC: Super Admin full access; Team Admin scoped to administered teams
- [x] 1.6 Cost resolution helper: prefer team-tool pricing over tool default
- [x] 1.7 Update OpenAPI spec with `TeamToolAssignment`, `TeamToolAssignRequest`

## 2. Frontend

- [x] 2.1 Add "Tools & Pricing" accordion to TeamsPage slide-over
- [x] 2.2 Tool multi-select — load from `GET /api/v1/tools?active=true`
- [x] 2.3 Per-tool pricing row component (reuse ToolPricing form fields)
- [x] 2.4 Create `frontend/src/api/teamTools.ts` with `fetchTeamTools`, `upsertTeamTool`, `removeTeamTool`
- [x] 2.5 Wire team save to submit batch team–tool assignments

## 3. Tests

- [x] 3.1 Backend: create and retrieve team–tool assignment with pricing fields
- [x] 3.2 Backend: Team Admin denied for team they don't administer
- [x] 3.3 Backend: cost resolution falls back to tool default when team-tool pricing absent
