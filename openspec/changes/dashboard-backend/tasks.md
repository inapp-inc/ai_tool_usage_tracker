# Tasks: Dashboard Backend

Reference [design.md](./design.md), [specs](./specs/), [verification.md](./verification.md). Depends on `authentication-backend`, `user-management-backend`, and read access to `usage.usage_aggregates`.

---

## 1. Dashboard package scaffold

- [ ] 1.1 Create `backend/app/dashboard/` package structure per design.md
- [ ] 1.2 Register dashboard router at `/api/v1/dashboard` on API v1 router
- [ ] 1.3 Add Pydantic response schemas mirroring OpenAPI widget models
- [ ] 1.4 Add settings: `DASHBOARD_CACHE_ENABLED`, `DASHBOARD_CACHE_TTL_SECONDS`

## 2. RBAC scope (dashboard-rbac-scope spec)

- [ ] 2.1 Implement `DashboardScopeResolver` in `scope.py`
- [ ] 2.2 Map roles to `ScopeFilter` predicates (org, team_ids, user_id)
- [ ] 2.3 Enforce Team Admin membership check per ADR-015
- [ ] 2.4 Return 403 when `team_id` param outside authorized scope
- [ ] 2.5 Wire scope resolver into all widget services

## 3. Cache layer (dashboard-cache spec)

- [ ] 3.1 Implement `DashboardCache` with Redis get/set/delete
- [ ] 3.2 Build cache keys per ADR-016 (org + endpoint + scope_hash + filter_hash)
- [ ] 3.3 Implement cache-aside wrapper used by widget services
- [ ] 3.4 Implement org-prefix invalidation `dash:{org_id}:*`
- [ ] 3.5 Hook invalidation into aggregate refresh and admin change events (stubs OK until USG-002)
- [ ] 3.6 Export Prometheus cache hit/miss counters

## 4. Query layer

- [ ] 4.1 Implement `queries/aggregates.py` — date-range rollups from `usage.usage_aggregates`
- [ ] 4.2 Join `admin.tools` for tool names and inactive tool inclusion
- [ ] 4.3 Join `admin.teams` for team names and deactivated team inclusion
- [ ] 4.4 Implement `queries/alerts.py` — active alerts with scope filter
- [ ] 4.5 Compute `last_updated_at` from max `refreshed_at` in queried aggregates

## 5. Widget services (dashboard-widgets spec)

- [ ] 5.1 `GET /api/v1/dashboard/tokens` — TokenUsageWidget
- [ ] 5.2 `GET /api/v1/dashboard/cost` — CostOverviewWidget
- [ ] 5.3 `GET /api/v1/dashboard/usage-by-tool` — UsageByToolItem list + share_pct
- [ ] 5.4 `GET /api/v1/dashboard/usage-by-team` — team comparison
- [ ] 5.5 `GET /api/v1/dashboard/top-consumers` — teams/users ranking
- [ ] 5.6 `GET /api/v1/dashboard/alerts` — ActiveAlertSummary list
- [ ] 5.7 `GET /api/v1/dashboard/trends` — TrendPoint series by granularity
- [ ] 5.8 `GET /api/v1/dashboard/my-usage` — personal summary with user_id param rules

## 6. Test fixtures

- [ ] 6.1 Create `tests/fixtures/dashboard_seed.sql` — org, teams, tools, aggregates, alerts
- [ ] 6.2 Add pytest factory helpers for role-scoped JWT clients

## 7. Tests — dashboard-cache

- [ ] 7.1 `tests/integration/test_dashboard_cache.py` — miss, hit, cross-tenant, invalidation

## 8. Tests — dashboard-rbac-scope

- [ ] 8.1 `tests/integration/test_dashboard_rbac.py` — all five role scenarios

## 9. Tests — dashboard-widgets

- [ ] 9.1 `tests/integration/test_dashboard_tokens.py`
- [ ] 9.2 `tests/integration/test_dashboard_cost.py`
- [ ] 9.3 `tests/integration/test_dashboard_usage_by_tool.py`
- [ ] 9.4 `tests/integration/test_dashboard_usage_by_team.py`
- [ ] 9.5 `tests/integration/test_dashboard_top_consumers.py`
- [ ] 9.6 `tests/integration/test_dashboard_alerts.py`
- [ ] 9.7 `tests/integration/test_dashboard_trends.py`
- [ ] 9.8 `tests/integration/test_dashboard_my_usage.py`

## 10. Performance and contract

- [ ] 10.1 `tests/performance/test_dashboard_perf.py` — p95 ≤ 3s smoke on reference fixture
- [ ] 10.2 OpenAPI schema validation for all dashboard response models
- [ ] 10.3 Update README with dashboard endpoint examples

## 11. Verification & Evidence

- [ ] 11.1 Run all acceptance-criteria tests for every scenario in verification.md § Spec Alignment and confirm all pass
- [ ] 11.2 Collect functional evidence for each scenario — populate verification.md § Evidence Log
- [ ] 11.3 Confirm Hallucination Risk mitigations in verification.md § Hallucination Risk Register
- [ ] 11.4 Confirm ADR compliance steps in verification.md § Pattern & ADR Compliance
- [ ] 11.5 Complete Audit Record sign-off in verification.md § Audit Record (human reviewer)
- [ ] 11.6 Run `openspec validate dashboard-backend --type change --strict` before archive
