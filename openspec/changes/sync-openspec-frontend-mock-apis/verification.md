# Verification Plan: Sync OpenSpec with Frontend Mock APIs

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### frontend-mock-api-catalog

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Mock API module inventory | Catalog lists all thirteen modules | Given index.ts exports, when catalog opened, then 13 modules listed with functions and types | Manual review: `frontend-mock-api-catalog.md` vs `frontend/src/api/index.ts` | ☐ |
| Mock API module inventory | Mock latency documented per module | Given delay() usage, when catalog read, then 400ms default and exceptions listed | Manual review: latency table in catalog | ☐ |
| Authentication API contract | Live auth endpoints identified | Given auth.ts, when catalog read, then login/refresh/me documented with live vs mock | Manual review: auth section + grep `apiRequest` in auth.ts | ☐ |
| Administration API contracts | Tools module includes pricing model | Given AiTool type, when catalog read, then ToolPricing fields present | Manual review: tools section vs tools.ts | ☐ |
| Administration API contracts | Teams module includes tool mapping | Given Team.toolIds, when catalog read, then toolIds in create/update requests | Manual review: teams section vs teams.ts | ☐ |
| Administration API contracts | Credentials module reflects team-scoped AI keys | Given Credential type, when catalog read, then environment, toolId, teamId, plainKey reveal documented | Manual review: credentials section vs credentials.ts | ☐ |
| Insights and usage API contracts | Dashboard stats and widgets documented | Given InsightsPage imports, when catalog read, then dashboard functions and insights query keys listed | Manual review + grep `fetchDashboard` in InsightsPage | ☐ |
| Insights and usage API contracts | Usage drill-down documented | Given usage.ts, when catalog read, then fetchDailyBreakdown and drilldown functions listed | Manual review: usage section | ☐ |
| Alerts API contract | Alert rule threshold types documented | Given AlertRule, when catalog read, then three threshold types and CRUD listed | Manual review: alerts section | ☐ |
| Reports and subscriptions API contract | Report entity includes subscription count | Given reports.ts, when catalog read, then subscription CRUD and subscriptionCount on Report | Manual review: reports section | ☐ |
| Uploads API contract | Upload preview and commit documented | Given uploads.ts, when catalog read, then preview/submit flow and query keys listed | Manual review: uploads section | ☐ |
| Audit log API contract | Audit filters documented | Given AuditLogFilters, when catalog read, then filter fields and query key pattern listed | Manual review: auditLog section | ☐ |
| Members API contract | Member CRUD documented | Given members.ts exports, when catalog read, then invite/update/remove listed | Manual review: members section | ☐ |

### frontend-pages-routing

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Active route inventory | Primary routes documented | Given App.tsx, when project.md read, then 11 active routes listed | Manual review: route table vs App.tsx | ☐ |
| Active route inventory | Legacy redirects documented | Given App.tsx redirects, when docs read, then all legacy paths redirect to insights/login | Manual review: redirect table vs App.tsx | ☐ |
| Insights hub consolidation | Insights tabs documented | Given InsightsPage, when task docs read, then three tabs described | Manual review: 10-frontend.md Insights section | ☐ |
| Role-based page access | Super Admin pages documented | Given RoleGuard usage, when routing doc read, then admin pages list Super Admin | Manual review: routing doc vs admin pages | ☐ |
| Page-to-API dependency map | Insights page dependencies documented | Given InsightsPage imports, when map read, then dashboard/usage/reports/teams listed | Manual review: dependency matrix | ☐ |
| Page-to-API dependency map | Admin page dependencies documented | Given admin pages, when map read, then credentials/teams/tools mappings correct | Manual review: dependency matrix | ☐ |
| Post-login navigation | Login redirect documented | Given LoginPage, when routing doc read, then post-login target is /insights | Manual review: grep navigate insights in LoginPage | ☐ |

### openapi-frontend-mapping

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Mock-to-REST mapping table | Mapping covers all mock domain modules | Given mock modules, when mapping.md opened, then each function has HTTP row | Manual review: mapping table completeness | ☐ |
| Mock-to-REST mapping table | Live auth endpoints mapped | Given auth.ts, when mapping read, then refresh/me marked live | Manual review: auth rows in mapping | ☐ |
| OpenAPI gap register | Report subscriptions flagged as gap | Given reports subscriptions, when gap register read, then missing subscription paths listed | Manual review: gap register section | ☐ |
| OpenAPI gap register | Credential environment model flagged | Given credentials redesign, when gap register read, then legacy OpenAPI credential note present | Manual review: gap register section | ☐ |
| OpenAPI gap register | Daily breakdown endpoint flagged | Given fetchDailyBreakdown, when gap register read, then breakdown path gap listed | Manual review: gap register section | ☐ |
| APIs README index update | README links catalog and mapping | Given apis/README.md, when opened, then links to new companion docs exist | Manual review: README links | ☐ |
| Frontend standards API access section | Mock layer documented in standards | Given frontend-standards.md, when API section read, then mock layer and catalog reference present | Manual review: frontend-standards delta | ☐ |
| Frontend standards API access section | Named exports for pages | Given frontend-standards.md, when export rules read, then pages documented as named exports | Manual review: export rules section | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| Invented API fields not in TypeScript | Add fields to catalog not in source | Diff catalog against `frontend/src/api/*.ts` exports |
| Wrong route paths | Document routes not in App.tsx | Line-by-line App.tsx comparison |
| Marking UI tasks Done without mock flows | Overstate completion | Only mark Done (mock API) where page file exists and imports API module |
| OpenAPI path invention | Map to non-existent openapi.yaml paths | Mark unverified paths as GAP; grep openapi.yaml |
| Missing subscription/credential gaps | Omit new frontend features from gap register | Explicit checklist against reports.ts and credentials.ts |
| Query key typos | Document wrong TanStack keys | Grep `queryKey` in pages referenced in catalog |
| Legacy CredentialScope as active | Document removed scope model | Verify credentials.ts commented legacy block noted |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-006 | React SPA frontend | project.md documents React 18 SPA architecture |
| ADR-012 | API-first OpenAPI contract | mapping doc links mock functions to OpenAPI paths or GAP |
| ADR-019 | Frontend architecture standards | frontend-standards.md matches Vite, @/ alias, strict TS |

---

## 4. Evidence Requirements

### Functional

- [ ] Evidence for each scenario in § Spec Alignment — doc review sign-off or diff output per row
- [ ] Catalog module count equals 13 (screenshot or grep count)
- [ ] Route table matches App.tsx (diff or checklist)
- [ ] Gap register includes subscriptions, credentials environment, daily breakdown
- [ ] TASK-SUMMARY shows Done (mock API) for completed UI tasks

### Structural

- [ ] Code review confirms design.md decisions reflected in catalog structure
- [ ] ADR compliance table reviewed — no new ADRs required

### Edge Case

- [ ] Hallucination risk: grep catalog field names against TypeScript interfaces (no invented fields)
- [ ] Hallucination risk: openapi.yaml cross-check for mapped paths that claim existing schema
- [ ] Hallucination risk: legacy CredentialScope not listed as active API

---

## 5. Evidence Log

| Scenario | Evidence | Reviewer | Date |
|----------|----------|----------|------|
| _Placeholder — fill during apply_ | | | |

---

## 6. Audit Record

- [ ] All Spec Alignment rows verified
- [ ] All Evidence Requirements checked
- [ ] Hallucination mitigations performed
- [ ] Human reviewer sign-off

**Reviewer:** _______________ **Date:** _______________
