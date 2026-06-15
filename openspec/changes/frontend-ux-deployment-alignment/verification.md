# Verification: Frontend UX, Terminology, and Deployment Alignment

Documentation-only change. Evidence is file presence and cross-check against `frontend/src/` and `backend/app/`.

## Spec alignment checklist

| Spec | Verify |
|------|--------|
| ui-terminology-and-routes | `openspec/project.md` route table matches `App.tsx` |
| insights-usage-by-team | `DashboardService.get_usage_by_team` uses `Tool` model |
| alerts-scope | `AlertsPage.tsx` SCOPE_OPTIONS includes Group + Team |
| auth-session-persistence | `AuthProvider` + `sessionStorage` in `frontend/src/auth/` |
| docker-frontend-gateway | `frontend/Dockerfile`, `nginx.conf`, `docker-compose.prod.yml` |
| admin-groups-csv | `teams/service.py` imports; CSV sync guard in `tools/service.py` |

## Evidence log

| Date | Scenario | Result |
|------|----------|--------|
| 2026-06-15 | Route inventory vs App.tsx | Pass |
| 2026-06-15 | Production URL table vs README | Pass |
| 2026-06-15 | Usage-by-team backend uses tools | Pass |
