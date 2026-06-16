# Database Specification

PostgreSQL data model for the **AI Tool Usage Tracker** (Phase 1 MVP).

**Sources:** [project.md](../project.md) · [ADR-003](../decisions/ADR-003-postgresql-system-of-record.md) · [data flow](../architecture/05-data-flow.md) · [OpenAPI schemas](./apis/components/schemas.yaml) · [NFR.md](../requirements/NFR.md) · [local-development.md](./local-development.md)

---

## Overview

| Aspect | Decision |
|--------|----------|
| Engine | PostgreSQL 15+ |
| Hosting | **Docker container** (`postgres:15-alpine` or official `postgres:15` image) — **not Amazon RDS** |
| Persistence | Named Docker volume or bind mount (e.g. `postgres_data:/var/lib/postgresql/data`) |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Primary keys | UUID v4 (`gen_random_uuid()`) |
| Timestamps | `TIMESTAMPTZ` stored in UTC |
| Money | `NUMERIC(18, 6)` |
| Tokens | `BIGINT` (non-negative) |
| Multi-tenancy | `organization_id` on all tenant tables |
| Encryption | Volume/disk encryption at host level; credential secrets as `BYTEA` ciphertext |

### Schema Namespaces (Bounded Contexts)

| Schema | Purpose |
|--------|---------|
| `auth` | Organizations, users, sessions |
| `admin` | Tools, teams, credentials, thresholds |
| `ingestion` | Uploads, parsed staging rows, parser templates |
| `usage` | Usage events, aggregates, idempotency |
| `notifications` | Alerts, in-app notifications |
| `reporting` | Report jobs, schedules |
| `audit` | Append-only audit log |

Modules MUST NOT perform cross-schema joins from API routers; use application services or database views owned by the usage/analytics layer where read-optimized access is required.

---

## Docker Deployment

PostgreSQL runs as a **Docker service** alongside the application stack (Docker Compose for local/staging; same pattern on self-hosted or K8s with a PostgreSQL StatefulSet if needed). **Amazon RDS is not used.**

**Implemented stack (TASK-INF-001):** see [local-development.md](./local-development.md) for the full five-service Compose file (`postgres`, `redis`, `api`, `worker`, `beat`), environment variables, startup order, and validation tests. Repository file: `docker-compose.yml`.

### Compose Service — PostgreSQL (reference)

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: ai-tracker-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-aitracker}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_DB: ${POSTGRES_DB:-aitracker}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d:ro  # optional extensions
    ports:
      - "${POSTGRES_PORT:-5433}:5432"  # restrict bind address in production
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    restart: unless-stopped
    networks:
      - ai-tracker

networks:
  ai-tracker:
    name: ai-tracker-network

volumes:
  postgres_data:
    name: ai-tracker-postgres-data
```

### Connection from Application Containers

| Setting | Value |
|---------|--------|
| Host | `postgres` (Compose service name) or `localhost` from host |
| Port | `5432` |
| URL | `postgresql+asyncpg://user:pass@postgres:5432/aitracker` |
| Pool size | 10–20 per API worker (adjust for container CPU/memory) |
| Redis (cache) | `redis://redis:6379/0` |
| Celery broker | `redis://redis:6379/1` |
| Celery result backend | `redis://redis:6379/2` |

FastAPI and Celery containers MUST wait for `pg_isready` (depends_on + healthcheck) before running Alembic migrations. **TASK-INF-001** enforces this via `depends_on: condition: service_healthy`; Alembic startup is implemented in **TASK-INF-004**.

### Resource Sizing (Docker host)

Reference scale (NFR-SCL-001): allocate **4 vCPU, 8–16 GB RAM, 100–500 GB volume** for the PostgreSQL container at MVP scale. Monitor `pg_stat_activity`, disk usage, and connection count; scale host resources before row count exceeds ~10M on unpartitioned `usage_events`.

### Backups (no RDS)

| Method | Schedule | Notes |
|--------|----------|-------|
| `pg_dump -Fc` | Daily (cron or sidecar container) | Full logical backup to **`backups_data` Docker volume** |
| WAL archiving | Optional P1 | `archive_mode=on` + local volume for PITR (NFR-BKP-001) |
| Restore drill | Quarterly | Restore dump to fresh `postgres` container |

```bash
# Example backup
docker exec ai-tracker-postgres pg_dump -U aitracker -Fc aitracker > backup_$(date +%F).dump

# Example restore
docker exec -i ai-tracker-postgres pg_restore -U aitracker -d aitracker --clean < backup.dump
```

### High Availability (Phase 1)

Single PostgreSQL container with persistent volume is acceptable for Phase 1 MVP. Streaming replica in a second container is **Phase 2** if uptime requirements exceed single-node tolerance (NFR-AVL-002).

---

## Entity Relationship Diagram

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ TEAM : has
    ORGANIZATION ||--o{ TOOL : configures
    ORGANIZATION ||--o{ THRESHOLD : defines
    ORGANIZATION ||--o{ UPLOAD : receives
    ORGANIZATION ||--o{ USAGE_EVENT : records
    ORGANIZATION ||--o{ AUDIT_LOG : logs

    USER ||--o{ TEAM_MEMBERSHIP : belongs
    TEAM ||--o{ TEAM_MEMBERSHIP : contains
    USER ||--o{ NOTIFICATION : receives
    USER ||--o{ USAGE_EVENT : attributed

    TOOL ||--o{ CREDENTIAL : secures
    TEAM ||--o{ CREDENTIAL : scopes
    TOOL ||--o{ THRESHOLD : scopes
    TEAM ||--o{ THRESHOLD : scopes
    USER ||--o{ THRESHOLD : scopes

    UPLOAD ||--o{ PARSED_ROW : stages
    UPLOAD ||--o{ USAGE_EVENT : sources
    TOOL ||--o{ USAGE_EVENT : tracks
    TEAM ||--o{ USAGE_EVENT : attributes

    THRESHOLD ||--o{ ALERT : triggers
    ALERT ||--o{ NOTIFICATION : creates

    USAGE_EVENT }o..o{ USAGE_AGGREGATE : rolls_up
    USER ||--o{ REPORT_JOB : requests
    USER ||--o{ REPORT_SCHEDULE : owns
```

---

## Entities

### `auth.organizations`

Tenant root. All business data scoped by `organization_id`.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `name` | VARCHAR(200) | NO | Organization display name |
| `slug` | VARCHAR(100) | NO | URL-safe identifier |
| `timezone` | VARCHAR(64) | NO | IANA timezone (default `UTC`) |
| `retention_months` | INTEGER | NO | Usage retention; min 24 |
| `retention_audit_months` | INTEGER | NO | Audit retention; min 24 |
| `settings` | JSONB | NO | Org-level config (`{}` default) |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `auth.users`

Platform users with RBAC role.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `email` | VARCHAR(255) | NO | Login identifier |
| `password_hash` | VARCHAR(255) | NO | bcrypt/argon2 hash |
| `display_name` | VARCHAR(200) | YES | |
| `role` | VARCHAR(32) | NO | `super_admin`, `team_admin`, `finance_viewer`, `team_member`, `auditor` |
| `active` | BOOLEAN | NO | Default `true` |
| `last_login_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `auth.refresh_tokens`

Optional refresh token rotation (ADR-005).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `user_id` | UUID | NO | FK → `auth.users` |
| `token_hash` | VARCHAR(255) | NO | Hashed refresh token |
| `expires_at` | TIMESTAMPTZ | NO | |
| `revoked_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `admin.teams`

Business units for usage attribution (FR-ADM-002).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `name` | VARCHAR(100) | NO | Unique per org |
| `description` | VARCHAR(500) | YES | |
| `active` | BOOLEAN | NO | Default `true`; deactivated teams reject new attribution |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `admin.team_memberships`

Many-to-many users ↔ teams.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `team_id` | UUID | NO | FK → `admin.teams` |
| `user_id` | UUID | NO | FK → `auth.users` |
| `joined_at` | TIMESTAMPTZ | NO | |
| `removed_at` | TIMESTAMPTZ | YES | Soft removal; history preserved |

---

### `admin.tools`

AI tool configuration and pricing (FR-ADM-001).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `name` | VARCHAR(100) | NO | Unique per org among active+inactive |
| `vendor` | VARCHAR(100) | NO | e.g. OpenAI, Anthropic |
| `pricing_model` | VARCHAR(32) | NO | `flat_token`, `package_with_overage`, `custom` |
| `token_price` | NUMERIC(18,6) | NO | Price per 1K tokens (or unit) |
| `package_allowance` | BIGINT | YES | Token package size |
| `overage_price` | NUMERIC(18,6) | YES | Overage unit price |
| `pricing_config` | JSONB | NO | Extended pricing (`{}` default) |
| `active` | BOOLEAN | NO | Default `true` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `admin.credentials`

Encrypted vendor API credentials (FR-ADM-003).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `tool_id` | UUID | NO | FK → `admin.tools` |
| `team_id` | UUID | YES | FK → `admin.teams`; NULL = org-wide |
| `environment` | VARCHAR(16) | NO | `sandbox`, `production` |
| `secret_ciphertext` | BYTEA | NO | AES-256 encrypted secret |
| `secret_last_four` | VARCHAR(4) | NO | Display mask only |
| `expires_at` | TIMESTAMPTZ | YES | |
| `last_rotated_at` | TIMESTAMPTZ | YES | |
| `created_by` | UUID | NO | FK → `auth.users` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `deleted_at` | TIMESTAMPTZ | YES | Soft delete |

---

### `admin.thresholds`

Alert thresholds (FR-ADM-004).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `threshold_type` | VARCHAR(32) | NO | `token_count`, `package_utilization_pct`, `cost_amount` |
| `scope` | VARCHAR(16) | NO | `tool`, `team`, `user` |
| `tool_id` | UUID | YES | FK → `admin.tools` |
| `team_id` | UUID | YES | FK → `admin.teams` |
| `user_id` | UUID | YES | FK → `auth.users` |
| `limit_value` | NUMERIC(18,6) | NO | Threshold limit |
| `severity` | VARCHAR(16) | NO | `warning`, `critical` |
| `notify_email` | BOOLEAN | NO | Default `true` |
| `notify_in_app` | BOOLEAN | NO | Default `true` |
| `active` | BOOLEAN | NO | Default `true` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

Scope columns MUST match `scope` (enforced via CHECK constraints).

---

### `ingestion.uploads`

Vendor file upload metadata (FR-ING-001). Raw bytes on **local storage volume** (ADR-013).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `team_id` | UUID | NO | FK → `admin.teams` |
| `tool_id` | UUID | YES | FK → `admin.tools`; parser hint |
| `uploaded_by` | UUID | NO | FK → `auth.users` |
| `filename` | VARCHAR(255) | NO | Original filename |
| `content_type` | VARCHAR(128) | YES | MIME type |
| `size_bytes` | BIGINT | NO | Max 52,428,800 (50 MB) |
| `storage_key` | VARCHAR(512) | NO | Relative path under `LOCAL_STORAGE_ROOT` (e.g. `uploads/{org_id}/{upload_id}/{filename}`) |
| `s3_bucket` | VARCHAR(255) | YES | **Deprecated** — legacy alias; use `storage_key` |
| `s3_key` | VARCHAR(512) | YES | **Deprecated** — legacy alias; use `storage_key` |
| `status` | VARCHAR(32) | NO | See enum below |
| `detected_format` | VARCHAR(16) | YES | `csv`, `json`, `xlsx` |
| `detected_vendor` | VARCHAR(64) | YES | Parser used |
| `total_rows` | INTEGER | YES | After parse |
| `matched_rows` | INTEGER | YES | |
| `unmatched_rows` | INTEGER | YES | |
| `error_message` | TEXT | YES | Parse/commit failure |
| `committed_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |
| `deleted_at` | TIMESTAMPTZ | YES | Soft delete |

**`status` enum:** `pending`, `parsing`, `preview_ready`, `committing`, `completed`, `failed`, `deleted`

---

### `ingestion.parsed_rows`

Staging rows before commit (FR-ING-002).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `upload_id` | UUID | NO | FK → `ingestion.uploads` |
| `row_number` | INTEGER | NO | Source row index |
| `user_email` | VARCHAR(255) | YES | From vendor export |
| `matched_user_id` | UUID | YES | FK → `auth.users` |
| `occurred_at` | TIMESTAMPTZ | YES | |
| `input_tokens` | BIGINT | NO | Default 0 |
| `output_tokens` | BIGINT | NO | Default 0 |
| `vendor_event_id` | VARCHAR(255) | YES | Idempotency source |
| `raw_payload` | JSONB | YES | Original row snapshot |
| `match_status` | VARCHAR(16) | NO | `matched`, `unmatched`, `skipped` |
| `created_at` | TIMESTAMPTZ | NO | |

Purged when upload deleted or after successful commit (configurable grace period).

---

### `ingestion.collector_configs`

Vendor API usage collector configuration (FR-ING-004). Links tool, optional team, credential, and schedule.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `tool_id` | UUID | NO | FK → `admin.tools` |
| `team_id` | UUID | YES | FK → `admin.teams`; NULL = org-wide |
| `credential_id` | UUID | NO | FK → `admin.credentials` |
| `provider` | VARCHAR(64) | NO | e.g. `openai`, `anthropic`, `azure_ai`, `cursor` |
| `schedule` | VARCHAR(16) | NO | `hourly` or `daily` |
| `active` | BOOLEAN | NO | Default `true` |
| `last_run_at` | TIMESTAMPTZ | YES | |
| `last_success_at` | TIMESTAMPTZ | YES | |
| `last_error` | TEXT | YES | Last failure message (no secrets) |
| `created_by` | UUID | NO | FK → `auth.users` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `ingestion.collector_runs`

Execution history for collector jobs (FR-ING-004).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `collector_id` | UUID | NO | FK → `ingestion.collector_configs` |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `status` | VARCHAR(16) | NO | `queued`, `running`, `completed`, `failed` |
| `records_ingested` | INTEGER | NO | Default 0 |
| `error_message` | TEXT | YES | |
| `started_at` | TIMESTAMPTZ | YES | |
| `completed_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `ingestion.parser_templates`

Configurable vendor mappings (FR-ING-001 “other providers”).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `name` | VARCHAR(100) | NO | |
| `vendor_key` | VARCHAR(64) | NO | |
| `file_format` | VARCHAR(16) | NO | `csv`, `json`, `xlsx` |
| `mapping_config` | JSONB | NO | Column/JSON path mapping |
| `active` | BOOLEAN | NO | Default `true` |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `usage.usage_events`

Append-oriented usage facts (FR-USG-001). **Partitioned by month** on `occurred_at` when volume exceeds 10M rows.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `tool_id` | UUID | NO | FK → `admin.tools` |
| `team_id` | UUID | NO | FK → `admin.teams` |
| `user_id` | UUID | YES | FK → `auth.users` |
| `upload_id` | UUID | YES | FK → `ingestion.uploads` |
| `occurred_at` | TIMESTAMPTZ | NO | Event timestamp (UTC) |
| `input_tokens` | BIGINT | NO | ≥ 0 |
| `output_tokens` | BIGINT | NO | ≥ 0 |
| `total_tokens` | BIGINT | NO | Generated: input + output |
| `estimated_cost` | NUMERIC(18,6) | NO | At ingestion-time pricing |
| `overage_cost` | NUMERIC(18,6) | NO | Default 0 |
| `vendor_event_id` | VARCHAR(255) | YES | External idempotency key |
| `idempotency_hash` | VARCHAR(64) | YES | SHA-256 when no vendor ID |
| `pricing_snapshot` | JSONB | NO | Tool pricing at ingest time |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `usage.usage_aggregates`

Pre-computed rollups for dashboards/reports (ADR-008 CQRS-lite).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `granularity` | VARCHAR(16) | NO | `daily`, `weekly`, `monthly` |
| `period_start` | DATE | NO | Bucket start (UTC date) |
| `period_end` | DATE | NO | Bucket end inclusive |
| `tool_id` | UUID | YES | NULL = all tools in scope |
| `team_id` | UUID | YES | NULL = org-wide |
| `user_id` | UUID | YES | NULL = team/org rollup |
| `input_tokens` | BIGINT | NO | |
| `output_tokens` | BIGINT | NO | |
| `total_tokens` | BIGINT | NO | |
| `estimated_cost` | NUMERIC(18,6) | NO | |
| `overage_cost` | NUMERIC(18,6) | NO | |
| `package_utilization_pct` | NUMERIC(8,4) | YES | |
| `refreshed_at` | TIMESTAMPTZ | NO | Last aggregation run |

---

### `usage.ingest_idempotency`

Idempotency keys for API/batch ingestion (FR-USG-002).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | |
| `idempotency_key` | VARCHAR(128) | NO | Client or derived key |
| `usage_event_id` | UUID | YES | FK → `usage.usage_events` |
| `created_at` | TIMESTAMPTZ | NO | |
| `expires_at` | TIMESTAMPTZ | NO | TTL 7 days |

---

### `notifications.alerts`

Threshold breach records (FR-NTF-003).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `threshold_id` | UUID | NO | FK → `admin.thresholds` |
| `status` | VARCHAR(16) | NO | `active`, `resolved`, `acknowledged` |
| `severity` | VARCHAR(16) | NO | `warning`, `critical` |
| `current_value` | NUMERIC(18,6) | NO | Value at breach |
| `limit_value` | NUMERIC(18,6) | NO | Threshold limit |
| `period_start` | TIMESTAMPTZ | NO | Evaluation window start |
| `period_end` | TIMESTAMPTZ | NO | Evaluation window end |
| `triggered_at` | TIMESTAMPTZ | NO | |
| `resolved_at` | TIMESTAMPTZ | YES | |
| `acknowledged_at` | TIMESTAMPTZ | YES | |
| `acknowledged_by` | UUID | YES | FK → `auth.users` |

---

### `notifications.notifications`

In-app notification center (FR-NTF-001).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `user_id` | UUID | NO | FK → `auth.users` |
| `alert_id` | UUID | YES | FK → `notifications.alerts` |
| `notification_type` | VARCHAR(32) | NO | `threshold_breach`, `credential_expiry`, `report_ready`, etc. |
| `severity` | VARCHAR(16) | YES | |
| `title` | VARCHAR(255) | NO | |
| `body` | TEXT | YES | |
| `payload` | JSONB | NO | Tool, team, threshold, deep link |
| `read` | BOOLEAN | NO | Default `false` |
| `read_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `reporting.report_jobs`

Async/sync report generation (FR-RPT-007).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `requested_by` | UUID | NO | FK → `auth.users` |
| `report_type` | VARCHAR(32) | NO | See OpenAPI `ReportType` |
| `format` | VARCHAR(8) | NO | `json`, `csv`, `pdf` |
| `filters` | JSONB | NO | Period, team, tool, user filters |
| `status` | VARCHAR(16) | NO | `queued`, `processing`, `completed`, `failed` |
| `s3_bucket` | VARCHAR(255) | YES | |
| `s3_key` | VARCHAR(512) | YES | |
| `error_message` | TEXT | YES | |
| `started_at` | TIMESTAMPTZ | YES | |
| `completed_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |

---

### `reporting.report_schedules`

Scheduled report delivery (FR-RPT-007 P1).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `created_by` | UUID | NO | FK → `auth.users` |
| `report_type` | VARCHAR(32) | NO | |
| `format` | VARCHAR(8) | NO | |
| `filters` | JSONB | NO | |
| `cron_expression` | VARCHAR(64) | NO | Celery Beat schedule |
| `recipient_emails` | TEXT[] | NO | |
| `active` | BOOLEAN | NO | Default `true` |
| `last_run_at` | TIMESTAMPTZ | YES | |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

---

### `audit.audit_log`

Append-only audit trail (FR-PLT-002, NFR-AUD-001). **No UPDATE/DELETE** for application role.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | UUID | NO | PK |
| `organization_id` | UUID | NO | FK → `auth.organizations` |
| `actor_id` | UUID | YES | FK → `auth.users`; NULL for system |
| `actor_email` | VARCHAR(255) | YES | Denormalized for retention |
| `action` | VARCHAR(64) | NO | e.g. `tool.create`, `credential.rotate` |
| `resource_type` | VARCHAR(64) | NO | |
| `resource_id` | VARCHAR(64) | YES | |
| `outcome` | VARCHAR(16) | NO | `success`, `failure` |
| `metadata` | JSONB | NO | Request context (`{}` default) |
| `source_ip` | INET | YES | |
| `correlation_id` | UUID | YES | |
| `created_at` | TIMESTAMPTZ | NO | Insert time |

---

## Relationships

| Parent | Child | Cardinality | On Delete |
|--------|-------|-------------|-----------|
| `organizations` | `users`, `teams`, `tools`, … | 1:N | RESTRICT |
| `teams` | `team_memberships` | 1:N | CASCADE membership rows |
| `users` | `team_memberships` | 1:N | CASCADE membership rows |
| `tools` | `credentials`, `usage_events` | 1:N | RESTRICT (deactivate, don't delete) |
| `teams` | `usage_events` | 1:N | RESTRICT |
| `uploads` | `parsed_rows`, `usage_events` | 1:N | CASCADE parsed_rows on upload delete |
| `thresholds` | `alerts` | 1:N | RESTRICT |
| `alerts` | `notifications` | 1:N | SET NULL on alert archive |
| `users` | `notifications`, `report_jobs` | 1:N | RESTRICT |

**Referential integrity rules:**

- Deactivated tools/teams (`active = false`) remain referenced by historical `usage_events`.
- Credentials use soft delete (`deleted_at`); historical audit references preserved.
- `usage_events` are never updated for pricing retroactivity (FR-ADM-001); reprocess creates correction events or admin-triggered batch job (Phase 2).

---

## Indexes

### Primary & Unique

| Table | Index | Columns | Notes |
|-------|-------|---------|-------|
| `auth.users` | `uq_users_org_email` | `(organization_id, email)` | UNIQUE |
| `admin.teams` | `uq_teams_org_name` | `(organization_id, name)` | UNIQUE |
| `admin.tools` | `uq_tools_org_name` | `(organization_id, name)` | UNIQUE |
| `admin.team_memberships` | `uq_membership_active` | `(team_id, user_id)` | UNIQUE WHERE `removed_at IS NULL` |
| `usage.usage_events` | `uq_usage_vendor_event` | `(organization_id, tool_id, vendor_event_id)` | UNIQUE WHERE `vendor_event_id IS NOT NULL` |
| `usage.usage_events` | `uq_usage_idempotency_hash` | `(organization_id, idempotency_hash)` | UNIQUE WHERE `idempotency_hash IS NOT NULL` |
| `usage.usage_aggregates` | `uq_aggregate_bucket` | `(organization_id, granularity, period_start, tool_id, team_id, user_id)` | UNIQUE NULLS NOT DISTINCT (PG15+) |
| `usage.ingest_idempotency` | `uq_idempotency_key` | `(organization_id, idempotency_key)` | UNIQUE |
| `notifications.alerts` | `uq_active_alert_period` | `(threshold_id, period_start, period_end)` | UNIQUE WHERE `status = 'active'` |

### Query Performance

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `usage.usage_events` | `ix_usage_events_org_occurred` | `(organization_id, occurred_at DESC)` | Time-range reports |
| `usage.usage_events` | `ix_usage_events_team_tool` | `(organization_id, team_id, tool_id, occurred_at DESC)` | Team/tool drill-down |
| `usage.usage_events` | `ix_usage_events_user` | `(organization_id, user_id, occurred_at DESC)` | User usage report |
| `usage.usage_aggregates` | `ix_agg_org_period` | `(organization_id, granularity, period_start, period_end)` | Dashboard widgets |
| `usage.usage_aggregates` | `ix_agg_team` | `(organization_id, team_id, period_start)` | Team dashboard |
| `notifications.notifications` | `ix_notif_user_unread` | `(user_id, read, created_at DESC)` | Notification center |
| `notifications.alerts` | `ix_alerts_org_status` | `(organization_id, status, triggered_at DESC)` | Alert widget |
| `audit.audit_log` | `ix_audit_org_created` | `(organization_id, created_at DESC)` | Audit query |
| `audit.audit_log` | `ix_audit_actor` | `(organization_id, actor_id, created_at DESC)` | Actor filter |
| `ingestion.uploads` | `ix_uploads_team_status` | `(organization_id, team_id, status)` | Admin upload list |
| `admin.credentials` | `ix_credentials_expiry` | `(organization_id, expires_at)` | Expiration reminders |
| `reporting.report_jobs` | `ix_report_jobs_user` | `(organization_id, requested_by, created_at DESC)` | Job polling |

### Partitioning (usage_events)

When row count exceeds **10M**, convert to declarative partitioning:

```sql
-- Parent: usage.usage_events
-- Partitions: usage.usage_events_YYYY_MM ON RANGE (occurred_at)
CREATE INDEX ix_usage_events_part_org_time
  ON usage.usage_events (organization_id, occurred_at DESC);
-- Created on each partition
```

---

## Constraints

### Check Constraints

| Table | Constraint | Rule |
|-------|------------|------|
| `auth.organizations` | `chk_retention_months` | `retention_months >= 24` |
| `auth.organizations` | `chk_retention_audit_months` | `retention_audit_months >= 24` |
| `auth.users` | `chk_user_role` | `role IN ('super_admin','team_admin','finance_viewer','team_member','auditor')` |
| `admin.tools` | `chk_token_price_nonneg` | `token_price >= 0` |
| `admin.tools` | `chk_package_pricing` | If `pricing_model = 'package_with_overage'` then `package_allowance IS NOT NULL AND overage_price IS NOT NULL` |
| `admin.thresholds` | `chk_threshold_scope` | Scope-specific FK columns populated per `scope` value |
| `admin.thresholds` | `chk_limit_value_nonneg` | `limit_value >= 0` |
| `admin.thresholds` | `chk_utilization_pct` | If type = `package_utilization_pct` then `limit_value BETWEEN 0 AND 100` |
| `ingestion.uploads` | `chk_upload_size` | `size_bytes <= 52428800` |
| `usage.usage_events` | `chk_tokens_nonneg` | `input_tokens >= 0 AND output_tokens >= 0` |
| `usage.usage_events` | `chk_costs_nonneg` | `estimated_cost >= 0 AND overage_cost >= 0` |

### Threshold Scope CHECK (example)

```sql
ALTER TABLE admin.thresholds ADD CONSTRAINT chk_threshold_scope_refs CHECK (
  (scope = 'tool'  AND tool_id IS NOT NULL AND team_id IS NULL AND user_id IS NULL) OR
  (scope = 'team'  AND team_id IS NOT NULL AND user_id IS NULL) OR
  (scope = 'user'  AND user_id IS NOT NULL)
);
```

### Row-Level Security (Optional P1)

Enable RLS on tenant tables filtering `organization_id = current_setting('app.organization_id')::uuid` set by FastAPI middleware. Application-layer RBAC remains mandatory (NFR-SEC-004).

### Audit Immutability

```sql
REVOKE UPDATE, DELETE ON audit.audit_log FROM app_role;
-- Inserts only via SECURITY DEFINER function or dedicated audit service account
```

---

## Migration Strategy

### Tooling

| Tool | Purpose |
|------|---------|
| **Alembic** | Version-controlled schema migrations |
| **SQLAlchemy 2** | ORM models mirroring this specification |
| **GitHub Actions** | Run migrations in CI against ephemeral PostgreSQL |

### Migration Principles (OpenSpec)

1. **Backward-compatible evolution** — expand schema first; contract in later release.
2. **Zero-downtime deploys** — additive columns with defaults; avoid blocking `NOT NULL` without default on large tables.
3. **Reversible migrations** — each Alembic revision includes `upgrade()` and `downgrade()` where safe.
4. **No destructive changes in single release** — deprecate → stop writing → drop in later migration.

### Revision Sequence (Phase 1)

| Revision | Description |
|----------|-------------|
| `001_initial_schemas` | Create schemas: `auth`, `admin`, `ingestion`, `usage`, `notifications`, `reporting`, `audit` |
| `002_auth_org_users` | Organizations, users, refresh_tokens |
| `003_admin_core` | Teams, memberships, tools, credentials, thresholds |
| `004_ingestion` | Uploads, parsed_rows, parser_templates |
| `005_usage_core` | usage_events, usage_aggregates, idempotency |
| `006_notifications` | alerts, notifications |
| `007_reporting` | report_jobs, report_schedules |
| `008_audit` | audit_log + immutability grants |
| `009_indexes` | Performance indexes (CONCURRENTLY in production) |
| `010_partition_usage_events` | Monthly partitions when threshold reached |

### Production Migration Procedure

```mermaid
flowchart LR
    A["CI: alembic upgrade head on staging"] --> B["Integration tests pass"]
    B --> C["Deploy API init Job: alembic upgrade head"]
    C --> D["Readiness probe OK"]
    D --> E["Rolling pod update"]
```

- Run `CREATE INDEX CONCURRENTLY` outside transaction for large tables.
- Partition migration: create new partitioned table → backfill → swap names in maintenance window.
- Seed data: default organization + super admin via idempotent seed script (non-production or first boot only).

### Rollback

- Application rollback: `kubectl rollout undo` — schema remains at new version if migration is additive-only.
- Schema rollback: `alembic downgrade -1` only when downgrade script tested; never downgrade past data-destructive revisions without backup restore (NFR-BKP-002).

---

## Retention Policies

Derived from [project.md](../project.md), FR-PLT-004, NFR-CMP-001, NFR-PLT-004, NFR-AUD-003.

### Policy Summary

| Data Class | Default Retention | Minimum | Configurable | Purge Method |
|------------|-------------------|---------|--------------|--------------|
| `usage.usage_events` | 24 months | 24 months | Yes (`organizations.retention_months`) | Hard delete + optional local archive tarball |
| `usage.usage_aggregates` | Match usage events | 24 months | Yes | Recompute or delete orphaned buckets |
| `audit.audit_log` | 24 months | 24 months | Yes (`retention_audit_months`) | Hard delete (after archive export) |
| `ingestion.parsed_rows` | 30 days post-commit | — | No | Hard delete |
| `ingestion.uploads` metadata | 24 months | 12 months | Yes | Soft delete; purge files from local storage |
| `notifications.*` | 12 months | 6 months | Yes | Hard delete |
| `reporting.report_jobs` | 90 days | 30 days | Yes | Hard delete; remove report files from local storage |
| `usage.ingest_idempotency` | 7 days | 7 days | No | TTL job |
| `auth.refresh_tokens` | Until expiry + 7 days | — | No | Hard delete |

### Retention Enforcement Job

Celery Beat task `maintenance.enforce_retention` runs **daily at 02:00 org timezone**:

```mermaid
flowchart TD
    A["For each organization"] --> B["Load retention_months, retention_audit_months"]
    B --> C["DELETE usage_events WHERE occurred_at < cutoff"]
    C --> D["DELETE orphaned aggregates"]
    D --> E["DELETE audit_log WHERE created_at < audit_cutoff"]
    E --> F["DELETE expired parsed_rows, idempotency, refresh_tokens"]
    F --> G["INSERT audit_log retention.enforced"]
    G --> H["Optional: export archive tarball to backups volume before delete"]
```

### Validation Rules

- Super Admin CANNOT set `retention_months` or `retention_audit_months` below **24** without documented regulatory exception (FR-PLT-004 AC).
- Purge operations MUST be audit-logged with counts of deleted rows.
- Pre-purge **optional archive** to `/backups/storage/` on the host (Phase 2 formal cold storage).

### Local Storage Alignment (ADR-013)

| Path under `LOCAL_STORAGE_ROOT` | Retention |
|-----------------------------------|-----------|
| `uploads/` | Delete when upload metadata purged |
| `reports/` | Delete when `report_jobs` retention expires |
| `temp/` | Delete after successful commit or 7 days |
| Archive exports in `backups_data/storage/` | Operator-defined; recommend 24 months |

---

## Capacity Planning

Reference scale from project.md and NFR-SCL-001:

| Metric | Target |
|--------|--------|
| Organizations | 1 (Phase 1 single-tenant deploy; schema multi-tenant ready) |
| Tools | 50 |
| Teams | 200 |
| Users | 5,000 |
| Usage events (24 mo) | ~50M |
| Daily aggregate rows | ~500K–2M (depends on rollup cardinality) |

**Docker sizing (starting point):** PostgreSQL container on a host with 4 vCPU, 8–16 GB RAM, and 100–500 GB persistent volume (`postgres_data`). Tune shared_buffers (~25% RAM) and max_connections after load test. Partition `usage_events` before exceeding ~10M rows.

---

## Related Documents

- [OpenAPI specification](./apis/openapi.yaml)
- [Data flow architecture](../architecture/05-data-flow.md)
- [ADR-003 PostgreSQL](../decisions/ADR-003-postgresql-system-of-record.md)
- [ADR-008 CQRS-lite caching](../decisions/ADR-008-cqrs-lite-redis-caching.md)
- [NFR — Data retention](../requirements/NFR.md#nfr-cmp-001-data-retention-and-minimization)
