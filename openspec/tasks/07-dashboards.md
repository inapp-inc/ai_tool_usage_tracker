# Dashboard Tasks

Read-optimized dashboard APIs with Redis caching.

---

## TASK-DSH-001: Redis Cache-Aside Layer

### Description

Implement cache adapter for dashboard aggregates with keys scoped by org + RBAC hash, TTL 1–5 minutes, invalidation on usage commit and pricing/team changes.

### Dependencies

TASK-INF-001, TASK-USG-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Cache hit/miss metrics exported
- [ ] Invalidation on tool pricing update clears affected keys
- [ ] No cross-tenant cache leakage in tests

**ADR:** ADR-008 · **NFR:** NFR-PER-006

---

## TASK-DSH-002: Token and Cost Widget APIs

### Description

Implement `GET /dashboard/tokens` and `GET /dashboard/cost` with `from`/`to`/`team_id` filters, RBAC scoping, `last_updated_at` in response.

### Dependencies

TASK-DSH-001, TASK-PLT-002, TASK-USG-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] p95 ≤3s on seeded reference data (integration perf smoke)
- [ ] Team Member sees personal scope; Finance Viewer read-only org/team scope
- [ ] FR-DSH-001 and FR-DSH-002 acceptance criteria pass

**FR:** FR-DSH-001, FR-DSH-002 · **NFR:** NFR-PER-001

---

## TASK-DSH-003: Usage by Tool and Team Widget APIs

### Description

Implement `GET /dashboard/usage-by-tool` and `GET /dashboard/usage-by-team` with comparative share percentages.

### Dependencies

TASK-DSH-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Inactive tools with historical usage appear in period
- [ ] Team comparison respects RBAC team scope
- [ ] FR-DSH-003 and FR-DSH-004 acceptance criteria pass

**FR:** FR-DSH-003, FR-DSH-004

---

## TASK-DSH-004: Top Consumers and Alert Widget APIs

### Description

Implement `GET /dashboard/top-consumers` (teams/users) and `GET /dashboard/alerts` (active threshold breaches).

### Dependencies

TASK-DSH-002, TASK-NTF-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Top consumers ranked descending by tokens
- [ ] Active alerts show severity, current vs limit values
- [ ] FR-DSH-005 and FR-DSH-006 acceptance criteria pass

**FR:** FR-DSH-005, FR-DSH-006

---

## TASK-DSH-005: Trends and My Usage Widget APIs

### Description

Implement `GET /dashboard/trends` (daily/weekly/monthly) and `GET /dashboard/my-usage` with team average comparison.

### Dependencies

TASK-DSH-002, TASK-PLT-006

### Estimated Complexity

**M**

### Definition of Done

- [ ] Granularity switch returns correctly bucketed series
- [ ] Team Member restricted to own user_id unless elevated
- [ ] FR-DSH-007, FR-DSH-008 acceptance criteria pass

**FR:** FR-DSH-007, FR-DSH-008

---

## TASK-DSH-006: Dashboard Export Support

### Description

Add server-side CSV/PDF export for dashboard filtered datasets (supports FR-DSH-009); reuse report rendering utilities where possible.

### Dependencies

TASK-DSH-002, TASK-RPT-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Export respects active date filters and RBAC scope
- [ ] CSV/PDF downloads complete for standard dataset within performance budget
- [ ] FR-DSH-009 export acceptance criteria pass

**FR:** FR-DSH-009
