# Tasks: Frontend UX, Terminology, and Deployment Alignment

Documentation sync for implemented behaviour (2026-06-15).

## 1. Terminology and routing

- [x] 1.1 Add UI/API terminology glossary to `openspec/project.md`
- [x] 1.2 Update `frontend-pages-routing` delta spec with current routes and redirects
- [x] 1.3 Document admin nav labels (Teams, Groups) vs REST paths

## 2. Auth and frontend standards

- [x] 2.1 Update `authentication.md` — session restore, `/insights` landing
- [x] 2.2 Update `frontend-standards.md` — sessionStorage tokens, `VITE_BASE_PATH`, live API modules

## 3. Deployment

- [x] 3.1 Update `local-development.md` — `frontend` and `frontend-dev` services
- [x] 3.2 Update `deployment.md` — foundry.inapp.com `/aitool/` layout

## 4. Dashboard and insights

- [x] 4.1 Update `FR-DSH-004` — Usage by Team = API team (tool) metrics
- [x] 4.2 Update `dashboard-widgets` delta spec — usage-by-team scenarios

## 5. Administration and alerts

- [x] 5.1 Update `01-administration.md` — Groups vs Teams glossary; optional group tool assignment
- [x] 5.2 Document alert scope values (`organization`, `team`=Group, `tool`=Team, `user`)
- [x] 5.3 Note CSV import and sync restrictions in admin specs

## 6. Backend fixes documented

- [x] 6.1 Document `TeamService.create_team` import requirement (groups POST 500 fix)
