# Token Collector MVP — Minimal Stack

**Status:** In progress (basic setup)  
**Date:** 2026-06-16  
**Branch baseline:** `develop`

## Why

AI **token usage** is the core metric for this product. We need a backend that **pulls usage from vendor APIs** on a schedule configured in the frontend, persists token events in PostgreSQL, and exposes read APIs for dashboards — without Redis, Celery, or extra worker containers for the first iteration.

## What ships in this MVP

| Component | Description |
|-----------|-------------|
| **Docker Compose** | `postgres` + `migrate` + `api` only |
| **Collector scheduler** | APScheduler inside the **API container** |
| **Pull interval** | `pull_interval_minutes` (5–1440) set via `POST/PATCH /collectors` |
| **Storage** | `ingestion.collector_configs`, `ingestion.collector_runs`, `usage.usage_events` |
| **Adapters** | OpenAI (real HTTP attempt + stub fallback), Anthropic (stub) |
| **Read API** | `GET /usage/events`, `GET /usage/summary` |

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/collectors` | List collector configs |
| POST | `/api/v1/collectors` | Connect provider + set pull interval |
| GET | `/api/v1/collectors/{id}` | Get config |
| PATCH | `/api/v1/collectors/{id}` | Update interval, token, active flag |
| DELETE | `/api/v1/collectors/{id}` | Remove config |
| POST | `/api/v1/collectors/{id}/run` | Manual pull |
| GET | `/api/v1/collectors/{id}/runs` | Run history |
| GET | `/api/v1/usage/events` | List ingested usage rows |
| GET | `/api/v1/usage/summary` | Aggregated token/cost totals |

## Frontend integration (next steps)

The frontend will configure collectors from Admin → Tools or a dedicated Integrations screen:

- `pull_interval_minutes` maps to the UI schedule picker (e.g. 15, 60, 1440).
- On save, call `POST` or `PATCH /collectors`; the API reloads scheduler jobs automatically.
- Dashboard/Insights will consume `GET /usage/summary` and `/usage/events` once wired.

## Out of scope (your follow-up work steps)

- JWT auth / RBAC on collector endpoints
- Full OpenAI/Anthropic/Azure/Cursor production adapters
- `organization_id`, `tool_id`, `team_id` FK wiring
- Usage aggregates table and dashboard widgets
- Credential vault separate from collector config
- Re-introducing Redis/Celery if horizontal scaling is needed

## Related

- [design.md](./design.md) — architecture decisions
- [tasks.md](./tasks.md) — implementation checklist
- [specs/collector-api/spec.md](./specs/collector-api/spec.md) — requirements
- [../usage-collector-backend/proposal.md](../usage-collector-backend/proposal.md) — full Phase 1 vision (Celery-based)
