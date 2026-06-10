# Proposal: Dashboard Backend

## Why

Dashboards are the primary visibility surface for token consumption, cost, alerts, and trends (Module 2, FR-DSH-001 – FR-DSH-008). Stakeholders require **p95 ≤ 3s** widget load times (NFR-PER-001) with role-scoped data. OpenAPI defines eight `/dashboard/*` endpoints; none are implemented.

This change delivers the **dashboard backend**: Redis cache-aside read path (ADR-008), aggregate queries against `usage.usage_aggregates`, RBAC-scoped widget services, and all dashboard REST APIs — unblocking TASK-UI-004 and E2E-003.

## What Changes

- Implement Redis cache-aside layer for dashboard aggregates (TASK-DSH-001) with org + scope + filter keying and TTL 1–5 minutes.
- Add `backend/app/dashboard/` bounded context: query services, RBAC scope resolver, widget handlers.
- Implement OpenAPI dashboard endpoints under `/api/v1/dashboard/*`:
  - `GET /tokens`, `/cost`, `/usage-by-tool`, `/usage-by-team`
  - `GET /top-consumers`, `/alerts`, `/trends`, `/my-usage`
- Read from pre-computed `usage.usage_aggregates` (CQRS-lite read model); include `last_updated_at` on responses.
- Apply role-based data scope: Team Member (personal), Team Admin (administered teams), Super Admin / Finance Viewer (org), Auditor (read-only org).
- Query active alerts from `notifications.alerts` for alerts widget (read-only; assumes threshold engine populates data).
- Add integration tests with seeded aggregates; performance smoke for p95 budget on reference dataset.
- Export cache hit/miss metrics (Prometheus counters hook).

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `dashboard-cache` | Redis cache-aside for dashboard reads, invalidation hooks, tenant-safe keys |
| `dashboard-rbac-scope` | Resolves authorized org/team/user filter scope per role for dashboard queries |
| `dashboard-widgets` | Eight OpenAPI dashboard widget endpoints backed by aggregate queries |

### Modified Capabilities

None — FR-DSH-* requirements exist in `openspec/requirements/02-dashboards.md`. Implementation only.

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/dashboard/` package |
| **Database** | Read-only queries on `usage.usage_aggregates`, `admin.tools`, `admin.teams`, `notifications.alerts` |
| **Redis** | Cache keys for dashboard widgets; invalidation subscribers |
| **API** | 8 new GET endpoints under `/api/v1/dashboard` |
| **Dependencies** | Requires auth (JWT/RBAC), **usage aggregates populated by [usage-collector-backend](../usage-collector-backend/proposal.md) or file ingest (USG-002)**, teams (user-management), alerts data (TASK-NTF-002 read path) |
| **Tests** | RBAC matrix, widget correctness, cache behaviour, perf smoke |
| **Downstream** | Unblocks TASK-UI-004, E2E-003, TASK-DSH-006 (export) |

## Usage collector dependency (FR-ING-004)

Dashboard widgets read `usage.usage_aggregates`. The **usage collector module** (hourly/daily vendor API sync) is the primary automated path to populate those aggregates alongside file upload ingestion. Cache invalidation hooks MUST include post-collection aggregate refresh events from the collector pipeline.

## Open Questions

1. **Usage aggregation job:** TASK-USG-002 may not be complete. **Assumption:** this change implements read path + test fixtures; production depends on aggregation Celery job populating `usage_aggregates`.
2. **Alerts widget:** Full threshold engine (TASK-NTF-001) may not exist. **Assumption:** read `notifications.alerts` where `status = 'active'`; integration tests seed alert rows.
3. **Export (FR-DSH-009):** **Out of scope** — TASK-DSH-006 separate change.
4. **Organization timezone (TASK-PLT-006):** **Assumption:** date filters use UTC boundaries in Phase 1; org timezone bucketing deferred.
5. **Drill-down navigation (FR-DSH-009):** UI concern; API returns sufficient ids for frontend routing only.
