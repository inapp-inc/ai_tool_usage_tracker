# Ingestion Tasks

Vendor file upload, parsing, and import commit.

---

## TASK-ING-001: Object Storage Adapter

### Description

Implement **local filesystem storage adapter** (Phase 1 — ADR-013). Storage port with `STORAGE_BACKEND=local`; read/write under `LOCAL_STORAGE_ROOT`. Key pattern `uploads/{org_id}/{upload_id}/{filename}`. Report downloads via authenticated API stream (no presigned S3 URLs in Phase 1).

### Dependencies

TASK-INF-001

### Estimated Complexity

**M**

### Definition of Done

- [ ] Upload bytes written to `storage_data` volume with org-scoped paths
- [ ] Adapter selected via `STORAGE_BACKEND=local`
- [ ] Integration test with Docker volume or temp directory fixture

**ADR:** ADR-013 (supersedes ADR-009 for Phase 1) · **NFR:** NFR-SEC-001

---

## TASK-ING-002: File Upload API

### Description

Implement `POST /uploads` (multipart), `GET /uploads`, `GET /uploads/{id}`, `DELETE /uploads/{id}` with 50 MB limit, RBAC, team_id validation, status tracking.

### Dependencies

TASK-ING-001, TASK-DB-003, TASK-ADM-002, TASK-PLT-002

### Estimated Complexity

**M**

### Definition of Done

- [ ] Files over 50 MB return 413 Problem Details
- [ ] Upload metadata persisted; file in object storage
- [ ] Delete removes staging data and audit-logged
- [ ] FR-ING-001 acceptance criteria met

**FR:** FR-ING-001

---

## TASK-ING-003: Vendor Parser Adapters

### Description

Implement ParserPort with OpenAI, Anthropic, Azure AI, Cursor parsers and ConfigurableParser (JSON mapping template). ParserFactory auto-detects format.

### Dependencies

TASK-INF-002

### Estimated Complexity

**L**

### Definition of Done

- [ ] Each parser has fixture-based unit tests
- [ ] All parsers emit canonical UsageRecord structure
- [ ] Unsupported format returns clear parse error
- [ ] ADR-011 adapter pattern implemented

**FR:** FR-ING-001 · **ADR:** ADR-011

---

## TASK-ING-004: Parse and Preview Pipeline

### Description

Celery task `ingestion.ingest_file`: fetch from storage, parse, stage `parsed_rows`, match users by email, set upload status `preview_ready`. Implement `GET /uploads/{id}/preview`.

### Dependencies

TASK-ING-002, TASK-ING-003, TASK-INF-003, TASK-DB-003

### Estimated Complexity

**L**

### Definition of Done

- [ ] Preview shows matched/unmatched counts and sample rows
- [ ] Unmatched emails flagged per FR-ING-002
- [ ] Parse failure sets status `failed` with error_message
- [ ] Task completes within 30s initiation SLA for 50 MB file (smoke test)

**FR:** FR-ING-002 · **NFR:** NFR-PER-004

---

## TASK-ING-005: Import Commit with Idempotency

### Description

Implement `POST /uploads/{id}/commit` with required `Idempotency-Key`, Celery task persisting usage events via usage service, duplicate detection, aggregate refresh trigger.

### Dependencies

TASK-ING-004, TASK-USG-001

### Estimated Complexity

**L**

### Definition of Done

- [ ] Duplicate vendor_event_id ignored on re-commit
- [ ] Idempotency-Key prevents double commit side effects
- [ ] Upload status transitions to `completed`
- [ ] Threshold evaluation task enqueued post-commit

**FR:** FR-ING-002, FR-USG-002

---

## TASK-ING-006: Reprocess Upload Flow

### Description

Implement `POST /uploads/{id}/reprocess` to rerun parse/match against stored file without re-upload.

### Dependencies

TASK-ING-004

### Estimated Complexity

**S**

### Definition of Done

- [ ] Reprocess clears prior staging rows and re-runs pipeline
- [ ] Action audit-logged
- [ ] Works after mapping template or user roster changes

**FR:** FR-ING-002

---

## TASK-ING-007: AI Usage Collector Module

### Description

Implement vendor API **usage collector** module: Celery tasks on `ingestion` queue, provider adapters (OpenAI, Anthropic, Azure AI, Cursor), normalize to canonical usage events, idempotent ingest via FR-USG-002. Scheduled **hourly** or **daily** per collector config (Beat + dynamic schedules).

### Dependencies

TASK-ADM-003, TASK-USG-001, TASK-USG-002, TASK-INF-003, TASK-ING-008

### Estimated Complexity

**L**

### Definition of Done

- [ ] Hourly and daily schedules run without duplicate vendor events
- [ ] Collection failures recorded with retrievable status; no secrets in logs
- [ ] Post-collection triggers aggregate refresh and threshold evaluation hook
- [ ] FR-ING-004 acceptance criteria pass

**FR:** FR-ING-004 · **ADR:** ADR-011, ADR-019

---

## TASK-ING-008: Provider Connect API (Frontend)

### Description

Implement collector configuration API for frontend **provider-managed connect** flow: `GET/POST/PATCH/DELETE /collectors`, optional `POST /collectors/{id}/run` (on-demand). Accept new API token or reference existing credential; persist schedule (`hourly`|`daily`), tool_id, team_id.

### Dependencies

TASK-DB-003 (extend with `ingestion.collector_configs`), TASK-ADM-003, TASK-PLT-002, TASK-ING-007

### Estimated Complexity

**M**

### Definition of Done

- [ ] Connect flow stores encrypted credential; UI receives masked reference only
- [ ] Team Admin scoped to administered teams; Super Admin org-wide
- [ ] OpenAPI Collectors tag documented
- [ ] FR-ING-004 AC-ING-004-01 and AC-ING-004-05 pass

**FR:** FR-ING-004 · **OpenSpec:** [usage-collector-backend](../changes/usage-collector-backend/proposal.md)
