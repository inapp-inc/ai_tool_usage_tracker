# Proposal: GitHub Copilot Productivity Schema & Dashboard

**Status:** Implemented

## Why

GitHub Copilot is seat-based, not token-based. The current integration maps Copilot activity into `usage.usage_events` with synthetic token counts, which produces misleading dashboards shared with OpenAI/Cursor token tools.

Administrators need seat utilization, productivity metrics (suggestions, acceptances, chat), language/IDE breakdowns, and package-based cost — not token charts.

## What Changes

### Data layer

- New PostgreSQL schema `copilot` with `copilot_organizations`, `copilot_user_usage`, `copilot_seats`.
- Collector sync persists Copilot data to dedicated tables; **stops writing** to `usage.usage_events`.

### Ingestion

- Extend Copilot adapter to fetch org-level metrics (`organization-1-day`) in addition to user metrics and seats.
- Map NDJSON fields to productivity columns (not tokens).
- Compute `estimated_cost` from team/tool package seat pricing.

### API

```
GET /api/v1/copilot/overview?team_id=&from=&to=
GET /api/v1/copilot/users?team_id=&from=&to=
GET /api/v1/copilot/users/{login}?team_id=&from=&to=
GET /api/v1/copilot/insights?team_id=&from=&to=
GET /api/v1/copilot/reports/seats?team_id=
GET /api/v1/copilot/reports/productivity?team_id=&from=&to=
GET /api/v1/copilot/reports/cost?team_id=
```

### Frontend

- New **Copilot Analytics** page (`/insights/copilot`) with seat/productivity dashboard distinct from token dashboard.
- Link from Insights when Copilot tool is selected or from team tool panel.

## Implementation Notes

- Backend implementation is in `backend/app/copilot/` with router registration under `/api/v1/copilot`.
- Collector sync uses `CopilotIngestService.sync_from_pull` for `copilot_*` persistence and skips generic `usage.usage_events` writes for Copilot runs.
- Pull-dump audit compatibility still builds parsed Copilot records for verification output, but those records are not persisted through the generic usage-event path.
- Frontend implementation includes `frontend/src/api/copilot.ts`, `/insights/copilot`, and the sidebar/topbar navigation entry.

## Out of Scope (this change)

- Copilot threshold alerts wired to notifications (schema hooks only)
- Executive multi-org rollup across enterprises
- Replacing verification Excel dump (kept for audit)

## Dependencies

- `030_tool_packages_billing` — package pricing for cost calculation
- Existing Copilot collector adapter and credential org ID
