# Design: Sync OpenSpec with Frontend Mock APIs

## Context

The frontend SPA (`frontend/`) implements:

- **11+ active routes** (login, insights, alerts, uploads, preview, admin pages) plus legacy redirects
- **13 API modules** in `src/api/` — **core modules use live HTTP** to `/api/v1` (auth, tools, teams, members, credentials, alerts, uploads, dashboard, usage) as of 2026-06-15; see `frontend-ux-deployment-alignment` change for details
- **TanStack Query v5** for server state; **Zustand** for auth/UI client state
- **MUI v6** + Recharts; shared components under `src/components/`
- **BRD 5.1** admin redesigns: tool pricing, team–tool mapping, team-scoped AI credentials, report subscriptions in Insights

OpenSpec currently documents Phase 1 tasks and OpenAPI from a backend-first perspective without reflecting what the UI already calls. This change produces **documentation as the contract bridge** between mock TypeScript APIs and future FastAPI endpoints (ADR-012).

### In-force ADRs (constraints)

| ADR | Relevance |
|-----|-----------|
| ADR-006 | React SPA architecture — honoured by current frontend |
| ADR-012 | API-first OpenAPI — mock catalog maps to canonical paths |
| ADR-019 | Frontend architecture (Vite, path alias, strict TS) — matches implementation |

No ADR supersession required — this is documentation alignment, not architectural change.

## Goals / Non-Goals

### Goals

- Single **Frontend Mock API Catalog** (`openspec/specifications/apis/frontend-mock-api-catalog.md`) derived from `frontend/src/api/index.ts` exports
- Updated **task status** reflecting mock-complete UI slices
- **Route map** documenting Insights hub and admin consolidation
- **OpenAPI mapping table** per module: mock function → HTTP method/path → schema refs
- Explicit **gap register** for mock features not yet in OpenAPI (subscriptions, credential environment, daily breakdown drill-down)

### Non-Goals

- Replacing mock implementations with live HTTP (separate backend changes)
- Full OpenAPI rewrite in one pass
- i18n migration or legacy page file deletion
- New ADRs

## Decisions

### 1. Catalog document vs inline OpenAPI only

**Decision:** Create standalone `frontend-mock-api-catalog.md` plus a slim `frontend-mock-mapping.md` table; update `apis/README.md` index.

**Rationale:** OpenAPI is backend-owned and large; TypeScript types include UI-specific fields (e.g. `teamName` denormalized on credentials). A catalog mirrors source-of-truth in `frontend/src/api/` without bloating `openapi.yaml`.

**Alternatives considered:** Auto-generate from TypeScript (rejected — no tooling in repo yet); embed everything in OpenAPI `x-*` extensions (rejected — harder to review).

### 2. Task status vocabulary

**Decision:** Use `Done (mock API)` in TASK-SUMMARY for UI tasks where pages work end-to-end against mocks.

**Rationale:** Distinguishes from live integration; backend teams know swap order.

### 3. Insights hub documentation

**Decision:** Document `/insights` as the primary analytics surface with three tabs (Overview, Usage, Reports); mark `/dashboard`, `/usage/*`, `/reports/*` as redirects.

**Rationale:** Matches `App.tsx`; prevents duplicate task tracking for removed routes.

### 4. OpenAPI gap handling

**Decision:** Gaps listed in mapping doc with target backend change IDs (e.g. `reporting-backend` for subscriptions, `user-management-backend` for members).

**Rationale:** Keeps this change doc-only while giving backend teams traceability.

### 5. Query key convention

**Decision:** Document canonical query keys from pages; note inconsistencies (`["tools-options"]` vs `["tool-options"]`) and recommend normalizing in a future frontend hygiene change.

**Rationale:** Accurate snapshot; normalization is out of scope.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Docs drift from code on future UI edits | Catalog header cites `frontend/src/api/` as source; verification includes grep diff check |
| OpenAPI mapping wrong path | Cross-check against `openapi.yaml` tags; mark unverified paths |
| Over-marking tasks Done | Use "Done (mock API)" only where page + CRUD flow exists in repo |
| Duplicate spec content | Catalog holds detail; specs hold SHALL requirements; tasks reference catalog sections |

## Migration Plan

1. Apply tasks in order: catalog → mapping → project/tasks → standards delta
2. Review with frontend owner (spot-check 3 modules against source)
3. No deployment — merge docs to main
4. **Rollback:** revert markdown files only

## Open Questions

- Normalize `tool-options` query key inconsistency in separate frontend change? (Recommended yes, not blocking)
- Add Redocly lint rule for mapping file structure? (Defer to OPS-004)
