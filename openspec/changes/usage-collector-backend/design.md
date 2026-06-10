# Design: Usage Collector Backend

## Context

Phase 1 originally emphasized file upload ingestion (FR-ING-001). **FR-ING-004** adds automated vendor API collection with hourly/daily schedules and a frontend provider-connect flow. FR-USG-002 already describes API-based sync; this change implements it.

**Depends on:** authentication-backend, user-management-backend, TASK-ADM-003 (credentials), TASK-USG-001/002 (usage pipeline), TASK-ADM-001 (tools).

**Feeds:** dashboard-backend, reporting-backend, notifications-backend (post-aggregate evaluation).

## Goals / Non-Goals

### Goals

- Collector schema + repositories
- Provider connect REST API for frontend
- Vendor collector adapters (OpenAI, Anthropic, Azure AI, Cursor)
- Hourly/daily Celery Beat scheduling + on-demand run
- Idempotent ingest + aggregate refresh hook

### Non-Goals

- Frontend connect UI (TASK-UI-003 extension)
- File upload ingestion (existing ING-001–006)
- OAuth provider login (Phase 2)

## Decisions

### 1. Package layout

```
backend/app/ingestion/collector/
  router.py           # /collectors/*
  schemas.py
  service.py          # connect, CRUD, trigger run
  repository.py
  scheduler.py        # Beat schedule registration
  adapters/
    base.py           # CollectorAdapter protocol
    openai.py
    anthropic.py
    azure_ai.py
    cursor.py
  tasks.py            # ingestion.collect_usage
```

### 2. Connect API contract

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/collectors` | List configs (paginated) |
| POST | `/collectors` | Connect provider (token or credential_id + schedule) |
| GET | `/collectors/{id}` | Get config + last run summary |
| PATCH | `/collectors/{id}` | Update schedule, active, team_id |
| DELETE | `/collectors/{id}` | Remove config (credential retained) |
| POST | `/collectors/{id}/run` | On-demand collection |

**Connect body (POST):** `provider`, `tool_id`, optional `team_id`, `schedule` (`hourly`|`daily`), either `api_token` (write-only) OR `credential_id`.

### 3. Scheduling

**Decision:** Celery Beat with:
- Global hourly task scanning active `schedule=hourly` collectors
- Global daily task (00:15 UTC) for `schedule=daily` collectors
- Per-collector `last_run_at` guard prevents double-run in same window

### 4. Credential handling

Decrypt credential only inside worker task; never log. Connect API creates credential via existing ADM-003 service when `api_token` provided.

### 5. Adapter pattern

Follow ADR-011: `CollectorAdapter.fetch_usage(credential, since, until) -> list[UsageRecord]`.

### 6. Failure handling

Update `collector_configs.last_error`; create failed `collector_runs` row. Optional notification stub for 3 consecutive failures.

## Risks

| Risk | Mitigation |
|------|------------|
| Vendor API rate limits | Backoff; stagger hourly runs |
| Token in error messages | Sanitize exception strings |
| Beat duplicate runs | last_run_at window guard |
