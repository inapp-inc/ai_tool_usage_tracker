# Administration Tasks

Tools, teams, credentials, and thresholds.

---

## TASK-ADM-001: AI Tool Management API

### Description

Implement `GET/POST /tools`, `GET/PATCH /tools/{toolId}` with pricing validation, unique name per org, deactivate via `active: false`, Super Admin only for writes.

### Dependencies

TASK-DB-002, TASK-PLT-002, TASK-PLT-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] Create/update tool persists pricing_model, token_price, package/overage fields
- [ ] Deactivated tool excluded from new ingestion mappings
- [ ] Audit log on create/update/deactivate
- [ ] Matches OpenAPI schemas and FR-ADM-001 acceptance criteria

**FR:** FR-ADM-001

---

## TASK-ADM-002: Team Management API

### Description

Implement teams CRUD and `GET/POST/DELETE /teams/{teamId}/members` with multi-team membership, soft removal (`removed_at`), Super Admin and scoped Team Admin permissions.

### Dependencies

TASK-DB-002, TASK-PLT-002, TASK-PLT-003

### Estimated Complexity

**M**

### Definition of Done

- [ ] User can belong to multiple teams
- [ ] Remove member preserves historical usage attribution
- [ ] Deactivated team rejects new usage attribution
- [ ] FR-ADM-002 acceptance criteria covered by tests

**FR:** FR-ADM-002

---

## TASK-ADM-003: API Credential Management API

### Description

Implement credentials CRUD, rotate, and delete with AES-256 encryption adapter, masked display, expiration tracking, org/team scope, sandbox/production environment.

### Dependencies

TASK-DB-002, TASK-PLT-002, TASK-PLT-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] Full secret never returned after create; only masked_secret shown
- [ ] Encryption key from host `.env` / Compose secrets (NFR-SEC-008)
- [ ] Rotate and delete audit-logged
- [ ] No credentials in application logs

**FR:** FR-ADM-003 · **NFR:** NFR-SEC-001, NFR-SEC-005

---

## TASK-ADM-004: Threshold Management API

### Description

Implement thresholds CRUD with types (token, utilization %, cost), scopes (tool/team/user), severity (warning/critical), notification flags, scoped Team Admin permissions.

### Dependencies

TASK-DB-002, TASK-ADM-001, TASK-ADM-002, TASK-PLT-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Scope CHECK constraints enforced at API and DB
- [ ] Team Admin cannot modify other teams' thresholds
- [ ] Validation rejects utilization limit outside 0–100
- [ ] FR-ADM-004 acceptance criteria tested

**FR:** FR-ADM-004
