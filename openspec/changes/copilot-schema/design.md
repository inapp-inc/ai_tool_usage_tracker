# Design: GitHub Copilot Productivity Module

## Architecture

```mermaid
flowchart LR
  GH[GitHub Copilot APIs] --> Adapter[CopilotUsageAdapter]
  Adapter --> Ingest[CopilotIngestService]
  Ingest --> OrgT[(copilot_organizations)]
  Ingest --> UserT[(copilot_user_usage)]
  Ingest --> SeatT[(copilot_seats)]
  OrgT --> Analytics[CopilotAnalyticsService]
  UserT --> Analytics
  SeatT --> Analytics
  Analytics --> API[/api/v1/copilot/*]
  API --> UI[CopilotDashboardPage]
```

## API mapping

| User spec | GitHub REST | Storage |
| --- | --- | --- |
| `/copilot/usage/users` | `GET .../metrics/reports/users-1-day?day=` | `copilot_user_usage` |
| `/copilot/usage` | `GET .../metrics/reports/organization-1-day?day=` | `copilot_organizations` (daily snapshot fields) |
| `/copilot/billing/seats` | `GET .../copilot/billing/seats` | `copilot_seats` |

## NDJSON → `copilot_user_usage`

Per user-day row from metrics API:

| API field | DB column |
| --- | --- |
| `user_login` | `user_login`, `user_email` |
| `day` | `report_date` |
| `used_chat` / chat counters | `chat_turns`, `feature` |
| `code_generation_activity_count` | `suggestions_count` |
| `code_acceptance_activity_count` | `acceptances_count` |
| derived | `acceptance_rate` |
| `loc_suggested_to_add_sum` | `lines_suggested` |
| `loc_added_sum` | `lines_accepted` |
| `totals_by_ide[].editor` | `editor` |
| `totals_by_language_feature[].language` | `language` |
| full row | `raw_payload` |

Rows are upserted on `(team_id, organization_id, user_login, report_date, feature, editor, language)`.

## Cost

```python
seat_price = team_tool.package.monthly_price or tool_package.monthly_price or DEFAULT_BY_PLAN
estimated_cost = seat_price if seat_assigned else 0
```

Active user in period: `last_activity_at` within range OR any `copilot_user_usage` row in range.

## Collector change

In `CollectorService.run_collector`:

```python
if config.provider == "copilot":
    sync_result = await copilot_ingest.sync(...)
    ingested = sync_result.user_rows + sync_result.seat_rows
    # skip _persist_records for usage_events
else:
    ingested = await self._persist_records(...)
```

The implemented collector also builds merged Copilot records for pull-dump verification output. Those records feed the local audit files only; Copilot persistence goes through `CopilotIngestService` and not the generic usage-event writer.

## Dashboard routing

- Token dashboard (`/dashboard`, `/insights`) excludes Copilot from token aggregations when `tool.billing_type == SEAT_BASED` and vendor is copilot.
- Copilot-specific UI at `/insights/copilot?team_id=`.

## Security

- All endpoints scoped by organization + team RBAC (same as dashboard).
- `raw_payload` stored for audit; not returned in list APIs by default.

## Implemented API surface

- `GET /api/v1/copilot/overview`
- `GET /api/v1/copilot/users`
- `GET /api/v1/copilot/users/{user_login}`
- `GET /api/v1/copilot/insights`
- `GET /api/v1/copilot/reports/seats`
- `GET /api/v1/copilot/reports/productivity`
- `GET /api/v1/copilot/reports/cost`
