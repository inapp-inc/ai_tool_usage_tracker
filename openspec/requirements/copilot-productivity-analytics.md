# GitHub Copilot — Seat-Based Productivity Analytics

**Status:** Approved for implementation  
**Change:** `copilot-schema`  
**Billing type:** `SEAT_BASED` (not token consumption)

## Objective

Implement GitHub Copilot Business / Enterprise as a **Seat-Based + Productivity Analytics** integration. Copilot does not expose token-level usage. Dashboards, reports, and insights MUST differ from token-based tools (OpenAI, Claude, Gemini, Cursor).

## Non-Goals

- Copilot MUST NOT surface `input_tokens`, `output_tokens`, `cache_tokens`, or `total_tokens` in dashboards or reports.
- Copilot MUST NOT be ingested into `usage.usage_events` as a token consumer.
- Usage-based billing API credits are out of scope for v1 (seat + productivity metrics only).

## GitHub APIs

| Logical API | GitHub REST path | Purpose |
| --- | --- | --- |
| User usage metrics | `GET /orgs/{org}/copilot/metrics/reports/users-1-day?day=` | Per-user daily productivity (NDJSON download) |
| Organization usage metrics | `GET /orgs/{org}/copilot/metrics/reports/organization-1-day?day=` | Org-level aggregates (active users, totals) |
| Seat information | `GET /orgs/{org}/copilot/billing/seats` | Assigned seats, last activity |

> User-facing docs may refer to `/copilot/usage/users`, `/copilot/usage`, and `/copilot/billing/seats`; these map to the metrics/billing REST paths above.

## Database

Schema: `copilot`

### `copilot_organizations`

Links a team to a GitHub org snapshot: subscription type, seat counts, monthly cost.

### `copilot_user_usage`

One row per `(team, organization, user_login, report_date, feature, editor, language)` aggregate from user metrics NDJSON.

Fields: `chat_turns`, `suggestions_count`, `acceptances_count`, `acceptance_rate`, `lines_suggested`, `lines_accepted`, `active_days`, `estimated_cost`, `raw_payload`.

### `copilot_seats`

Seat assignments from billing API: `user_login`, `seat_status`, `assigned_at`, `last_activity_at`, `monthly_cost`.

## Cost Calculation

GitHub does not provide per-user billed cost. Calculate from team package pricing:

| Package | Default monthly seat price |
| --- | --- |
| Business | $19 / user / month |
| Enterprise | $39 / user / month |

Formula: **assigned seat with activity in period** → `estimated_cost = seat_monthly_price`. Inactive assigned seats still count toward license cost in org overview.

## Dashboard — Overview

**Cards:** Total seats, Assigned seats, Active users, Inactive users, Monthly cost, Seat utilization %, Average acceptance rate.

**Charts:** Seat utilization (pie), Active users trend (line), Suggestions vs acceptances (bar), Top languages (bar), IDE distribution (pie).

## Dashboard — User

**Cards:** User name, Email, Active days, Chat sessions, Suggestions, Acceptances, Acceptance rate, Estimated cost.

**Charts:** Daily usage (chat/suggestions), Language distribution, IDE usage.

## Insights Engine

Rule-based insights generated from stored data:

- Adoption (% active in last 30 days)
- License waste (inactive assigned seats + potential savings)
- Power users (top 10 share of activity)
- Acceptance rate by team
- IDE and language concentration

## Reports

1. **Seat utilization** — User, Email, Assigned date, Last activity, Seat status, Monthly cost  
2. **User productivity** — User, Language, Editor, Suggestions, Acceptances, Acceptance rate, Chat sessions  
3. **Cost report** — User, Package, Estimated monthly cost, Activity status  

## Alerts

- Inactive license (no activity 30 days)
- Low adoption (acceptance rate below 20%)
- License expiry (subscription ending within 15 days — when subscription_end available on team_tools)

## Executive Dashboard

Same KPI cards as overview plus insights: unused licenses, cost optimization, most active/productive teams, top languages/IDEs.

## Acceptance Criteria

1. Copilot sync writes to `copilot_*` tables only; no new rows in `usage.usage_events` for provider `copilot`.
2. Insights page or dedicated Copilot view shows seat/productivity metrics, not tokens.
3. Overview API returns all card metrics for a team + date range.
4. User detail API returns per-user productivity for a date range.
5. Insights API returns at least adoption, license waste, and IDE/language insights when data exists.
6. Cost uses team package `monthly_price` when bound, else tool package default.
