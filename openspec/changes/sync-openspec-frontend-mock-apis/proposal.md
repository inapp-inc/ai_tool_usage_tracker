# Proposal: Sync OpenSpec with Frontend Mock APIs

## Why

The React SPA under `frontend/` is substantially implemented with full page flows, shared components, and **13 domain API modules** (`src/api/*.ts`) backed by in-memory mock data and artificial latency. OpenSpec planning artifacts (`openspec/project.md`, `openspec/tasks/`, `openspec/specifications/apis/`, requirements cross-references) still describe the pre-UI scaffold state: separate Dashboard/Usage/Reports routes, incomplete frontend task status, and OpenAPI paths that do not reflect the **actual TypeScript contracts** the UI already consumes.

Backend teams need a single, authoritative mapping from **implemented frontend mock APIs → target REST endpoints** before replacing mocks with real HTTP. Product and QA need updated task status and route documentation reflecting the **Insights hub** consolidation and BRD 5.1 admin redesigns (tools pricing, team tool mapping, team-scoped credentials, report subscriptions).

## What Changes

- Add a **Frontend Mock API Catalog** document under `openspec/specifications/apis/` listing every exported function, TypeScript type, TanStack Query key, mock latency, and proposed REST mapping per module.
- Update **`openspec/specifications/apis/README.md`** with a frontend–backend contract index and notes on mock vs live endpoints (`auth` partially live; all other domain modules mock).
- Update **`openspec/project.md`** with implemented frontend architecture: routes, Insights hub, admin pages, mock API layer, and stack versions (React 18, MUI v6, TanStack Query v5, RHF + Zod).
- Update **`openspec/tasks/10-frontend.md`** and **`openspec/tasks/TASK-SUMMARY.md`** to reflect completed/partial UI work (TASK-UI-001 through UI-007 substantially done with mocks; UI-006 notification SSE stub only).
- Update **`openspec/tasks/07-dashboards.md`** and **`openspec/tasks/09-reporting.md`** cross-references to the consolidated **Insights** page (dashboard + usage + reports tabs).
- Update **`openspec/specifications/frontend-standards.md`** with current folder layout, named-export rule (pages use named exports), and mock API conventions.
- Add **OpenAPI companion mapping** (`frontend-mock-mapping.yaml` or README section) aligning mock types to existing/planned `openapi.yaml` paths — flag gaps (report subscriptions, credential environment model, alert threshold presets) for backend follow-up changes.
- **No application code changes** in this change — documentation and OpenSpec artifacts only.

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `frontend-mock-api-catalog` | Normative catalog of all `frontend/src/api/*` contracts, query keys, mock behaviour, and REST mapping targets |
| `frontend-pages-routing` | Implemented routes, page components, role guards, legacy redirects, and page-to-API dependencies |
| `openapi-frontend-mapping` | Alignment between mock TypeScript types and OpenAPI schemas/paths; documented gaps for backend implementation |

### Modified Capabilities

| Capability | Description |
|------------|-------------|
| `frontend-standards` | Delta to `openspec/specifications/frontend-standards.md` — current conventions matching implemented codebase |

## Impact

| Area | Impact |
|------|--------|
| **OpenSpec docs** | `project.md`, `tasks/*`, `specifications/frontend-standards.md`, `specifications/apis/*` |
| **Backend planning** | Mock API catalog becomes input for ADM/DSH/RPT/NTF/ING backend changes |
| **OpenAPI** | Companion mapping; optional additive schema fields (subscriptions, credential environment) flagged not merged until backend change |
| **Frontend code** | None — docs only |
| **Tests** | Doc review checklist in verification.md |
| **Downstream** | Unblocks mock-to-live API swap per module; informs E2E test plan |

## Open Questions

1. **OpenAPI merge timing:** Should report subscription and credential environment schemas be added to `openapi.yaml` in this doc-only change, or deferred to dedicated backend change proposals? **Assumption:** add as `x-frontend-implemented: true` annotations in companion mapping; full OpenAPI merge in backend changes.
2. **i18n compliance:** `frontend-standards.md` requires `t()` for all strings; current UI has hardcoded English. **Assumption:** document as known gap in frontend-standards delta; i18n remains future TASK-UI-009.
3. **Legacy page files:** `DashboardPage`, `ReportsListPage`, etc. remain on disk but unrouted. **Assumption:** document as deprecated; removal optional follow-up.
4. **TASK-UI status granularity:** Mark tasks "Done (mock)" vs "Done (live API)". **Assumption:** use "Done (mock API)" in TASK-SUMMARY for transparency.
