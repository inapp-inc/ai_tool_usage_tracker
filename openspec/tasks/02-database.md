# Database Tasks

Schema migrations and data access layer.

---

## TASK-DB-001: Auth Schema Migrations

### Description

Alembic revision creating `auth` schema: `organizations`, `users`, `refresh_tokens` with constraints from [database.md](../specifications/database.md) (`chk_retention_months`, `chk_user_role`, unique email per org).

### Dependencies

TASK-INF-004

### Estimated Complexity

**M**

### Definition of Done

- [ ] Migration `002_auth` applies cleanly on empty database
- [ ] Seed script creates default organization and super admin (dev only)
- [ ] SQLAlchemy models and repositories for Organization, User

**FR:** FR-PLT-001, FR-PLT-004

---

## TASK-DB-002: Admin Schema Migrations

### Description

Migrations for `admin.teams`, `admin.team_memberships`, `admin.tools`, `admin.credentials`, `admin.thresholds` including CHECK constraints for pricing and threshold scope.

### Dependencies

TASK-DB-001

### Estimated Complexity

**L**

### Definition of Done

- [ ] All admin tables match database.md column specs
- [ ] Unique constraints on team name, tool name per org enforced
- [ ] Credential table stores `secret_ciphertext` BYTEA only

**FR:** FR-ADM-001 – FR-ADM-004

---

## TASK-DB-003: Ingestion Schema Migrations

### Description

Migrations for `ingestion.uploads`, `ingestion.parsed_rows`, `ingestion.parser_templates` with upload size CHECK (50 MB).

### Dependencies

TASK-DB-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Upload status enum matches OpenAPI `UploadStatus`
- [ ] FK from parsed_rows to uploads with CASCADE on staging purge
- [ ] Models + repositories implemented

**FR:** FR-ING-001, FR-ING-002

---

## TASK-DB-004: Usage Schema Migrations

### Description

Migrations for `usage.usage_events`, `usage.usage_aggregates`, `usage.ingest_idempotency` with token/cost CHECK constraints and unique idempotency indexes.

### Dependencies

TASK-DB-002

### Estimated Complexity

**L**

### Definition of Done

- [ ] `usage_events.total_tokens` generated or enforced as input + output
- [ ] Unique partial indexes on `vendor_event_id` and `idempotency_hash`
- [ ] Aggregate unique bucket index defined

**FR:** FR-USG-001, FR-USG-002

---

## TASK-DB-005: Notifications, Reporting, and Audit Schemas

### Description

Migrations for `notifications.alerts`, `notifications.notifications`, `reporting.report_jobs`, `reporting.report_schedules`, `audit.audit_log` with append-only grants on audit table.

### Dependencies

TASK-DB-002, TASK-DB-004

### Estimated Complexity

**M**

### Definition of Done

- [ ] Audit table REVOKE UPDATE/DELETE from app role
- [ ] Active alert unique constraint per threshold period
- [ ] All models and repositories scaffolded

**FR:** FR-PLT-002, FR-NTF-001 – 003, FR-RPT-007

---

## TASK-DB-006: Performance Indexes Migration

### Description

Add indexes from database.md (usage time-range, aggregates, notifications unread, audit queries). Use `CREATE INDEX CONCURRENTLY` pattern documented for production.

### Dependencies

TASK-DB-004, TASK-DB-005

### Estimated Complexity

**S**

### Definition of Done

- [ ] All indexes from database.md Index section created
- [ ] EXPLAIN on sample dashboard query uses index scan
- [ ] Migration documented for concurrent apply in prod

**NFR:** NFR-SCL-003, NFR-PER-001

---

## TASK-DB-007: Repository Layer and Unit of Work

### Description

Implement repository pattern with tenant-scoped queries (`organization_id` filter on all reads/writes) and Unit of Work for transactional commits across services.

### Dependencies

TASK-DB-001 through TASK-DB-005

### Estimated Complexity

**L**

### Definition of Done

- [ ] No raw SQL in routers; repositories inject via DI
- [ ] Cross-module access only through application services
- [ ] Repository tests verify tenant isolation

**ADR:** ADR-001, ADR-003, NFR-SCL-005
