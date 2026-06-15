# Tasks: Sync OpenSpec with Frontend Mock APIs

Reference [proposal.md](./proposal.md), [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md). **Documentation-only change** — no frontend/backend code edits.

---

## 1. Frontend Mock API Catalog (frontend-mock-api-catalog spec)

- [ ] 1.1 Create `openspec/specifications/apis/frontend-mock-api-catalog.md` with module index table (13 modules, mock latency, query keys)
- [ ] 1.2 Document `client.ts` — `apiRequest`, `ApiClientError`, auth retry, `API_BASE`
- [ ] 1.3 Document `auth.ts` — live vs mock paths, types, token storage notes
- [ ] 1.4 Document admin modules: `tools`, `teams`, `members`, `credentials` — full type and function reference
- [ ] 1.5 Document analytics modules: `dashboard`, `usage` — Insights query key patterns included
- [ ] 1.6 Document operational modules: `alerts`, `reports` (incl. subscriptions), `uploads`, `auditLog`
- [ ] 1.7 Document `notifications.ts` stub and SSE stream via `useNotifications` / `API_BASE/notifications/stream`
- [ ] 1.8 Fill verification.md § Spec Alignment artifacts for catalog scenarios (1.1–1.7)

## 2. OpenAPI Frontend Mapping (openapi-frontend-mapping spec)

- [ ] 2.1 Create `openspec/specifications/apis/frontend-mock-mapping.md` — function → HTTP method/path/schema table
- [ ] 2.2 Add **OpenAPI Gap Register** section: report subscriptions, credential environment, daily breakdown, alert webhook fields
- [ ] 2.3 Update `openspec/specifications/apis/README.md` — link catalog, mapping, mock vs live legend
- [ ] 2.4 Cross-check mapped paths against `openapi.yaml`; mark unverified as `GAP`
- [ ] 2.5 Fill verification.md artifacts for mapping scenarios (2.1–2.4)

## 3. Frontend Pages and Routing (frontend-pages-routing spec)

- [ ] 3.1 Update `openspec/project.md` — add **Frontend Application** section: stack, routes, Insights hub, admin pages
- [ ] 3.2 Add route table and legacy redirect table to project.md or linked routing doc section
- [ ] 3.3 Add page-to-API dependency matrix (Insights, Alerts, Uploads, Admin pages)
- [ ] 3.4 Document post-login redirect to `/insights`
- [ ] 3.5 Fill verification.md artifacts for routing scenarios (3.1–3.4)

## 4. Task status updates

- [ ] 4.1 Update `openspec/tasks/10-frontend.md` — mark TASK-UI-001 through UI-007 status; note mock API; describe Insights hub for UI-004/005/008
- [ ] 4.2 Update `openspec/tasks/TASK-SUMMARY.md` — UI tasks to `Done (mock API)` where applicable; INF-006 Done
- [ ] 4.3 Update `openspec/tasks/07-dashboards.md` header note — widgets consumed via Insights Overview tab
- [ ] 4.4 Update `openspec/tasks/09-reporting.md` header note — reports UI in Insights Reports tab + subscriptions
- [ ] 4.5 Update `openspec/tasks/04-administration.md` cross-ref — tools pricing, team toolIds, credentials BRD 5.1.3 UI complete (mock)

## 5. Frontend standards delta (openapi-frontend-mapping spec — MODIFIED)

- [ ] 5.1 Update `openspec/specifications/frontend-standards.md` — mock API layer, catalog reference, named page exports, current component paths
- [ ] 5.2 Document known gap: i18n (`t()`) not yet applied — hardcoded English in UI
- [ ] 5.3 Note query key inconsistency `tools-options` vs `tool-options` for future normalization
- [ ] 5.4 Fill verification.md artifacts for frontend-standards scenarios (5.1–5.2)

## 6. Consistency review

- [ ] 6.1 Grep catalog type/field names against `frontend/src/api/*.ts` — no invented fields
- [ ] 6.2 Verify route table against `frontend/src/App.tsx`
- [ ] 6.3 Verify TASK-SUMMARY status matches implemented pages in `frontend/src/pages/`

## 7. Verification & Evidence

- [ ] 7.1 Run all acceptance-criteria checks for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 7.2 Collect functional evidence (doc review notes / diff output) for each scenario — one entry per row in verification.md § Evidence Log
- [ ] 7.3 Confirm every Hallucination Risk mitigation step in verification.md § Hallucination Risk Register
- [ ] 7.4 Confirm all ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 7.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer required)
- [ ] 7.6 Run `openspec validate sync-openspec-frontend-mock-apis --type change --strict` before archive
