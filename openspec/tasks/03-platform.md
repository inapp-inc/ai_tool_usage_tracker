# Platform Tasks

Authentication, RBAC, audit, and cross-cutting API behavior.

---

## TASK-PLT-001: JWT Authentication API

### Description

Implement `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` per OpenAPI with bcrypt/argon2 password hashing, JWT issuance, refresh token rotation, and rate limiting on login.

### Dependencies

TASK-DB-001, TASK-INF-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Login returns TokenResponse; invalid credentials return 401 Problem Details
- [ ] `/auth/me` returns UserProfile with role and team_ids
- [ ] Token TTL configurable via environment
- [ ] Integration tests cover login, expired token, refresh

**FR:** FR-PLT-001 · **NFR:** NFR-SEC-003 · **OpenAPI:** `/auth/*`

---

## TASK-PLT-002: RBAC Middleware and Policies

### Description

Implement JWT validation middleware and role-based permission checks for all protected routes. Map roles (SA, TA, FV, TM, AU) to action permissions and team scope.

### Dependencies

TASK-PLT-001

### Estimated Complexity

**L**

### Definition of Done

- [ ] Unauthorized roles receive 403 on admin write endpoints
- [ ] Team Admin scoped to administered teams only
- [ ] Finance Viewer and Auditor read-only enforced
- [ ] Automated RBAC matrix tests per OpenAPI tag

**FR:** FR-PLT-001 · **NFR:** NFR-SEC-004

---

## TASK-PLT-003: Audit Log Service

### Description

Append-only audit service recording actor, action, resource, outcome, IP, correlation_id for sensitive operations listed in NFR-AUD-001.

### Dependencies

TASK-DB-005, TASK-PLT-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Audit entries created on tool/team/credential/threshold/upload/report export actions
- [ ] Application cannot UPDATE/DELETE audit rows
- [ ] Audit writes fail open only with explicit logging (never silent drop of business action)

**FR:** FR-PLT-002 · **NFR:** NFR-AUD-001, NFR-AUD-002

---

## TASK-PLT-004: Audit Log Query and Export API

### Description

Implement `GET /audit-logs` and `POST /audit-logs/export` with filters (date, actor, action, resource) for Super Admin and Auditor roles.

### Dependencies

TASK-PLT-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] Paginated query returns within 10s at reference scale (seed data test)
- [ ] CSV export matches filtered results
- [ ] Auditor receives read-only access; Team Admin denied

**FR:** FR-RPT-006 · **OpenAPI:** `/audit-logs`

---

## TASK-PLT-005: Correlation ID and Problem Details

### Description

Add middleware for `X-Correlation-ID` propagation and RFC 7807 `application/problem+json` error responses with field-level validation errors (400/422).

### Dependencies

TASK-INF-002

### Estimated Complexity

**S**

### Definition of Done

- [ ] All responses echo correlation ID when provided
- [ ] Pydantic validation errors map to Problem Details with `errors[]`
- [ ] Celery tasks inherit correlation ID from enqueue context

**NFR:** NFR-AUD-004 · **ADR:** ADR-012

---

## TASK-PLT-006: Organization Settings and Timezone

### Description

Implement organization timezone and settings on `auth.organizations`; use UTC storage with org timezone for report/dashboard period boundaries (NFR-LOC-002).

### Dependencies

TASK-DB-001

### Estimated Complexity

**S**

### Definition of Done

- [ ] Super Admin can read/update organization timezone
- [ ] Date filter utilities convert org-local day boundaries to UTC queries
- [ ] Unit tests for DST edge cases (at least one timezone)

**NFR:** NFR-LOC-002

---

## TASK-PLT-007: Data Retention Enforcement Job

### Description

Celery Beat task `maintenance.enforce_retention` purging usage events, aggregates, audit logs, parsed_rows, and idempotency keys per org policy (min 24 months).

### Dependencies

TASK-DB-004, TASK-DB-005, TASK-INF-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] Cannot set retention below 24 months without rejection at API level
- [ ] Purge job audit-logged with row counts
- [ ] Integration test verifies data older than policy is removed

**FR:** FR-PLT-004 · **NFR:** NFR-CMP-001, NFR-BKP-001
