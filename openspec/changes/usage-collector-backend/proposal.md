# Proposal: Usage Collector Backend

> **MVP path:** A minimal postgres + API implementation with in-process scheduling lives in [token-collector-mvp](../token-collector-mvp/proposal.md). This change describes the full Phase 1 Celery-based collector.

## Why

FR-ING-004 and FR-USG-002 require automated usage sync from vendor AI tool APIs — not only manual file uploads. Administrators need to connect providers with API tokens, choose **hourly** or **daily** collection schedules, and have the frontend support a **provider-managed connect** flow. Without a collector module, dashboards, reporting, and threshold evaluation lack timely data.

This change delivers the **usage collector backend**: collector configuration schema, provider connect API, vendor API adapters, scheduled Celery collection, and integration with the usage ingestion pipeline.

## What Changes

- Add Alembic migration extending `ingestion` schema: `collector_configs`, `collector_runs` per [database.md](../../specifications/database.md).
- Implement provider connect API (TASK-ING-008):
  - `GET/POST /api/v1/collectors` — list and create (token or existing credential + schedule)
  - `GET/PATCH/DELETE /api/v1/collectors/{collectorId}`
  - `POST /api/v1/collectors/{collectorId}/run` — on-demand collection
- Implement collector module (TASK-ING-007):
  - Vendor adapters: OpenAI, Anthropic, Azure AI, Cursor (ADR-011 pattern)
  - Celery task `ingestion.collect_usage` on `ingestion` queue
  - Beat schedules for hourly collectors; daily cron for daily collectors
  - Normalize to canonical usage events → FR-USG-002 idempotent ingest → aggregate refresh
- Extend OpenAPI with `Collectors` tag and schemas.
- RBAC: Super Admin org-wide; Team Admin scoped to administered teams (ADR-015).
- Audit log on connect, update, delete, and manual run.
- Integration tests for connect flow, schedules, dedupe, and failure handling.

## Capabilities

### New Capabilities

| Capability | Description |
|------------|-------------|
| `collector-schema` | `ingestion.collector_configs` and `collector_runs` migrations and repositories |
| `provider-connect-api` | Frontend provider-managed connect with API token and hourly/daily schedule |
| `vendor-collector-adapters` | Vendor API fetch adapters normalizing to usage events |
| `scheduled-collection` | Celery Beat + on-demand runs, run history, error reporting |

### Modified Capabilities

None — FR-ING-004 added to [06-usage-ingestion.md](../../requirements/06-usage-ingestion.md).

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New `backend/app/ingestion/collector/` package |
| **Database** | `collector_configs`, `collector_runs` |
| **Celery** | `ingestion.collect_usage` task; dynamic Beat entries per active collector |
| **API** | 5 collector endpoints under `/api/v1/collectors` |
| **Frontend (downstream)** | Connect-provider UI consumes connect API; masked credentials only |
| **Dependencies** | Auth, credentials (ADM-003), tools/teams, usage pipeline (USG-001/002) |
| **Downstream** | Unblocks near-real-time dashboards, reporting, threshold evaluation |

## Related Changes

This module **feeds data into** these OpenSpec changes:

| Change | Relationship |
|--------|--------------|
| [dashboard-backend](../dashboard-backend/proposal.md) | Widgets read aggregates populated by collector |
| [reporting-backend](../reporting-backend/proposal.md) | Reports depend on collected usage |
| [notifications-backend](../notifications-backend/proposal.md) | Threshold evaluation after aggregate refresh post-collection |
| [user-management-backend](../user-management-backend/proposal.md) | Team scope for collector config |
| [authentication-backend](../authentication-backend/proposal.md) | JWT/RBAC for connect API |

## Open Questions

1. **Credential create inline vs reference:** Connect API accepts new token (creates credential) or `credential_id`. **Assumption:** both supported.
2. **Hourly window:** Collect last 1 hour of usage. **Daily:** prior calendar day UTC.
3. **UI route:** Frontend route `/settings/integrations/connect` — out of scope for backend change; API only.
