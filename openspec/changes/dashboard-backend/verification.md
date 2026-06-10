# Verification Plan: Dashboard Backend

Gate artifact — Evidence Log and Audit Record completed by human reviewer after apply.

---

## 1. Spec Alignment

### dashboard-cache

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Cache-aside for dashboard reads | Cache miss loads from database | Given no cache entry, when widget called, then computed from aggregates and stored in Redis | `tests/integration/test_dashboard_cache.py::test_cache_miss` | ☐ |
| Cache-aside for dashboard reads | Cache hit returns stored response | Given valid cache entry, when same request within TTL, then served from Redis | `tests/integration/test_dashboard_cache.py::test_cache_hit` | ☐ |
| Tenant-safe cache keys | Cross-tenant cache isolation | Given org A cache, when org B same filters, then org B data only | `tests/integration/test_dashboard_cache.py::test_cross_tenant_isolation` | ☐ |
| Cache invalidation on data changes | Invalidation after aggregate refresh | Given cached widget, when aggregates refresh, then cache cleared and next request recomputes | `tests/integration/test_dashboard_cache.py::test_invalidation` | ☐ |

### dashboard-rbac-scope

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Role-based query scope | Team Member personal scope | Given Team Member, when widget requested, then only caller user_id data | `tests/integration/test_dashboard_rbac.py::test_team_member_scope` | ☐ |
| Role-based query scope | Team Admin team scope | Given TA on T1 T2, when widget requested, then only T1 T2 data; outside team_id → 403 | `tests/integration/test_dashboard_rbac.py::test_team_admin_scope` | ☐ |
| Role-based query scope | Super Admin organization scope | Given Super Admin, when widget with optional team_id, then org or team data | `tests/integration/test_dashboard_rbac.py::test_super_admin_scope` | ☐ |
| Role-based query scope | Finance Viewer read-only org access | Given Finance Viewer, when widgets requested, then read succeeds for org scope | `tests/integration/test_dashboard_rbac.py::test_finance_viewer_scope` | ☐ |
| Role-based query scope | Auditor read-only access | Given Auditor, when widgets requested, then org read succeeds | `tests/integration/test_dashboard_rbac.py::test_auditor_scope` | ☐ |

### dashboard-widgets

| Req ID | Scenario | Acceptance Criterion | Verification Artifact | Status |
|--------|----------|----------------------|----------------------|--------|
| Token usage widget | Token totals for date range | Given aggregates in range, when GET /tokens, then input/output/total + last_updated_at | `tests/integration/test_dashboard_tokens.py::test_token_totals` | ☐ |
| Token usage widget | Date filter changes totals | Given Jan+Feb data, when Feb filter, then Feb totals only | `tests/integration/test_dashboard_tokens.py::test_date_filter` | ☐ |
| Cost overview widget | Cost breakdown displayed | Given cost aggregates, when GET /cost, then spend/allowance/overage returned | `tests/integration/test_dashboard_cost.py::test_cost_breakdown` | ☐ |
| Cost overview widget | Tool without package allowance | Given no package tools, when GET /cost, then overage zero and spend correct | `tests/integration/test_dashboard_cost.py::test_no_package_overage` | ☐ |
| Usage by tool widget | Multi-tool breakdown with share percentages | Given multi-tool usage, when GET /usage-by-tool, then share_pct ~ 100% | `tests/integration/test_dashboard_usage_by_tool.py::test_share_pct` | ☐ |
| Usage by tool widget | Inactive tool with historical usage | Given inactive tool with period usage, when widget loads, then tool appears | `tests/integration/test_dashboard_usage_by_tool.py::test_inactive_tool` | ☐ |
| Usage by team widget | Organization-wide team ranking | Given SA + multi-team usage, when GET /usage-by-team, then teams with tokens/cost | `tests/integration/test_dashboard_usage_by_team.py::test_team_ranking` | ☐ |
| Usage by team widget | Deactivated team with period usage | Given deactivated team with usage, when widget loads, then team appears | `tests/integration/test_dashboard_usage_by_team.py::test_deactivated_team` | ☐ |
| Top consumers widget | Top teams ranked by tokens | Given entity=teams, when GET /top-consumers, then descending by tokens | `tests/integration/test_dashboard_top_consumers.py::test_top_teams` | ☐ |
| Top consumers widget | Fewer entities than limit | Given 3 teams limit 10, when widget loads, then 3 returned no error | `tests/integration/test_dashboard_top_consumers.py::test_fewer_than_limit` | ☐ |
| Active alerts widget | Active alerts listed | Given active alerts in scope, when GET /alerts, then severity/type/values returned | `tests/integration/test_dashboard_alerts.py::test_active_alerts` | ☐ |
| Active alerts widget | No active alerts empty state | Given no active alerts, when GET /alerts, then empty data array 200 | `tests/integration/test_dashboard_alerts.py::test_empty_alerts` | ☐ |
| Trend analysis widget | Granularity switch buckets correctly | Given daily aggregates, when granularity=weekly, then weekly buckets summed | `tests/integration/test_dashboard_trends.py::test_weekly_granularity` | ☐ |
| Trend analysis widget | Missing period shows zero | Given gap in data, when trends requested, then zero tokens for missing bucket | `tests/integration/test_dashboard_trends.py::test_missing_zero` | ☐ |
| Personal usage widget | Team Member sees own usage | Given TM, when GET /my-usage, then caller usage only | `tests/integration/test_dashboard_my_usage.py::test_own_usage` | ☐ |
| Personal usage widget | Unauthorized user_id access denied | Given TM + other user_id, when GET /my-usage, then 403 | `tests/integration/test_dashboard_my_usage.py::test_forbidden_user_id` | ☐ |
| Personal usage widget | Super Admin views another user | Given SA + valid user_id, when GET /my-usage, then that user summary | `tests/integration/test_dashboard_my_usage.py::test_admin_user_scope` | ☐ |

---

## 2. Hallucination Risk Register

| Risk Area | What AI Might Get Wrong | Mitigation |
|-----------|-------------------------|------------|
| Cache key missing scope hash | Cache by org+dates only | Unit test asserts scope_hash in key; cross-role isolation test |
| Query raw events not aggregates | SELECT from usage_events | Code review + SQL assertion in integration tests |
| share_pct calculation | Wrong denominator or >100% | Unit test with known fixture sums to ~100% |
| RBAC scope | Team Admin sees all org teams | Dedicated TA scope integration test with 403 |
| OpenAPI field names | `total_tokens` vs `token_total` | Contract test against TokenUsageWidget schema |
| Alerts query | Wrong status filter | Test seeds active vs resolved alerts |
| Trends granularity | Off-by-one week buckets | Fixture with known daily rows → assert weekly sum |
| last_updated_at | Omitted from responses | Assert field present on all widget responses |

---

## 3. Pattern & ADR Compliance

| ADR | Constraint | Verification Step |
|-----|------------|-------------------|
| ADR-001 | Dashboard bounded context | Code review: `backend/app/dashboard/` |
| ADR-005 | Server-side RBAC | RBAC integration test suite passes |
| ADR-008 | Aggregates + cache-aside + last_updated_at | Cache tests + last_updated_at assertions |
| ADR-012 | OpenAPI contract | Schemathesis or schema validation tests |
| ADR-015 | TA scope via membership | `test_team_admin_scope` passes |
| ADR-016 | Scope hash in cache keys | `test_cross_tenant_isolation` + key unit test |

---

## 4. Evidence Requirements

### Functional

- [ ] All 26 Spec Alignment scenarios — pytest output per row
- [ ] Performance smoke: p95 ≤ 3s on reference fixture — `tests/performance/test_dashboard_perf.py`

### Structural

- [ ] Code review confirms design.md read path uses `usage_aggregates`
- [ ] ADR-016 cache key format verified in `dashboard/cache.py`

### Edge Case

- [ ] Cross-tenant cache isolation verified
- [ ] Inactive/deactivated entities appear in historical widgets
- [ ] Empty alerts returns 200 with empty array

---

## 5. Evidence Log

| Scenario | Evidence Type | Location / Link | Collected By | Date |
|----------|---------------|-----------------|--------------|------|
| _TBD_ | _TBD_ | _TBD_ | | |

---

## 6. Audit Record

- [ ] All Spec Alignment rows pass with evidence
- [ ] Evidence Log complete
- [ ] Hallucination mitigations confirmed
- [ ] ADR compliance confirmed
- [ ] Scope excludes export (DSH-006) and aggregation job (USG-002)

**Reviewer:** _______________  
**Date:** _______________
