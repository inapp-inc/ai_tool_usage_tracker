# Figma — CSV Import, Team Configuration & Billing Insights

**Status:** Implemented  
**Priority:** P0 (Figma delivery path)  
**Related:** [copilot-import-mechanism.md](./copilot-import-mechanism.md), [06-usage-ingestion.md](./06-usage-ingestion.md), change `team-pricing-configuration`, change `inapp-alert-notifications`

---

## 1. Objective

Deliver Figma seat and credit monitoring through **CSV billing import**, **team-level subscription configuration**, and a **Copilot-style billing insights** dashboard.

Administrators SHALL:

1. Configure Figma subscription package, seat credit amounts, credits-per-USD rate, budget, and cost alerts when assigning Figma to a team.
2. Import Figma billing CSV exports (one row per user per usage period).
3. View Figma billing insights (subscription + paid-credit overage, trends, top users, periods).

Token-based usage events (`usage.usage_events`) MUST NOT be used for Figma billing CSV data. Imported billing lives in `figma.billing_imports` and `figma.billing_import_users`.

---

## 2. Scope

### In scope

| Area | Description |
|------|-------------|
| Team create/edit | Figma-specific fields when Figma is among selected tools |
| Package catalogue | Figma packages (Starter, Professional, Organization, Enterprise) |
| CSV import | Tool + team required; column auto-mapping; one user row per period |
| Cost derivation | Subscription from team config; overage from paid credits only |
| Billing insights | `/figma/billing-insights` + `FigmaBillingInsightsPanel` |
| Alerts | Synced threshold rules; fire on import; deactivate → history |
| Team metrics | Figma import cost rolled into team list totals |

### Out of scope

| Area | Reason |
|------|--------|
| Live Figma Admin API billing sync | CSV is primary billing source for this delivery |
| Seat credits used as billable overage | Included in subscription package |
| Token dashboards for Figma | Figma excluded from token aggregations |

---

## 3. CSV format

### 3.1 Expected headers (Figma export)

| CSV column | Mapped field | Required |
|------------|--------------|----------|
| User ID | `user_id` | Yes (or email) |
| User name | `user_name` | No |
| User email | `user_email` | Yes (or user ID) |
| Seat type | `seat_type` | No (defaults `full`) |
| Seat credits used | `seat_credits_used` | No (tracked, not costed) |
| Paid credits used | `paid_credits_used` | No |
| Last activity | `last_activity` | No |
| Usage period start | `usage_period_start` | Recommended |
| Usage period end | `usage_period_end` | Recommended |

### 3.2 Seat type normalization

| CSV value | Stored value |
|-----------|--------------|
| `full`, `Full`, (default) | `full` |
| `view`, `viewer`, `collab`, `collaborator` | `view` |

### 3.3 Column auto-mapping

`GET /uploads/{id}/mapping` returns `suggested_mapping` from header aliases (`FIGMA_FIELD_ALIASES`). Frontend `buildInitialColumnMapping` merges all suggested fields into the mapping form (Copilot and Figma).

---

## 4. Team configuration — Figma tool

### 4.1 UI flow

When **Figma** is selected in team tools (`TeamToolPackageSelector`):

| Step | Control | Behaviour |
|------|---------|-----------|
| 1 | **Subscription package** | Required (aligned with Copilot). No “Custom pricing” empty option. |
| 2 | **Pricing type** | Read-only from package `billing_type` (`SEAT_BASED`) |
| 3 | **Full seat credit amount (USD)** | Monthly full-seat package amount (`cost_per_seat`) |
| 4 | **View seat credit amount (USD)** | Monthly view/collab package amount (`view_seat_cost_usd`) |
| 5 | **Credits per USD** | Divisor for paid-credit overage (`credits_per_usd` / `credit_amount`) |
| 6 | **Monthly budget (USD)** | Optional cap for alerts |
| 7 | **Alert threshold (USD)** | Syncs to admin threshold rule via `sync_team_tool_cost_alert` |

### 4.2 Persistence

Stored on `admin.team_tools`:

| Field | Storage |
|-------|---------|
| Full seat credit amount | `cost_per_seat`, `pricing_config.cost_per_seat`, `pricing_config.full_seat_cost_usd` |
| View seat credit amount | `pricing_config.view_seat_cost_usd` |
| Credits per USD | `pricing_config.credits_per_usd`, `pricing_config.credit_amount` |
| Alert rule link | `pricing_config.alert_threshold_rule_id` |

---

## 5. Cost calculation

### 5.1 Principles

1. **Seat credits used** (CSV column) are **included in the subscription package** configured at team creation. They are stored for reporting but **never converted to USD** from CSV.
2. **Paid credits used** are **overage** beyond the package. They are converted using the team **Credits per USD** rate.
3. **Subscription cost** comes from team configuration × seat counts from the import (not re-priced per CSV row).

### 5.2 Per-row import cost (stored in `figma.billing_import_users`)

```
paid_cost_usd   = paid_credits_used / credits_per_usd
seat_cost_usd   = 0
total_cost_usd  = paid_cost_usd
```

If `credits_per_usd` is missing or ≤ 0, `paid_cost_usd = 0`.

### 5.3 Period / insights totals

For a usage period with `full_seat_count`, `view_seat_count`, and summed paid credits:

```
configured_subscription = (full_seat_credit_amount × full_seat_count)
                        + (view_seat_credit_amount × view_seat_count)

paid_overage_usd        = Σ(paid_credits_used) / credits_per_usd

display_total_usd       = configured_subscription + paid_overage_usd
```

Insights API returns:

| Field | Meaning |
|-------|---------|
| `configured_seat_cost` | Subscription component |
| `paid_cost` | Paid-credit overage from CSV |
| `total_cost` | Subscription + overage |
| `credits.total_seat_credits_used` | Sum of seat credits (informational) |
| `credits.total_paid_credits_used` | Sum of paid credits (informational) |

---

## 6. Database schema

Migration: `034_figma_billing_import`

### 6.1 `figma.billing_imports`

One row per team/tool/usage period per import commit.

| Column | Type | Description |
|--------|------|-------------|
| `usage_period_start` / `usage_period_end` | date | From CSV |
| `total_seat_cost` | numeric | Always 0 at import (subscription computed in insights) |
| `total_paid_cost` | numeric | Sum of row paid costs |
| `total_cost` | numeric | Same as `total_paid_cost` |
| `full_seat_count`, `view_seat_count`, `user_count` | int | Aggregates |
| `raw_summary` | jsonb | `credits_per_usd`, `row_count` |

Unique constraint: `(team_id, tool_id, usage_period_start, usage_period_end)` per active import.

### 6.2 `figma.billing_import_users`

One row per CSV user line.

| Column | Description |
|--------|-------------|
| `seat_type` | `full` or `view` |
| `seat_credits_used`, `paid_credits_used` | Raw credit counts |
| `seat_cost_usd`, `paid_cost_usd`, `total_cost_usd` | Computed at import |
| `matched_user_id` | Platform user when email matches |

---

## 7. Upload pipeline

### 7.1 Flow

1. **Uploads** → select Team + Figma tool + CSV
2. **Map columns** (auto-filled from headers)
3. **Preview** → `figma_summary` with seat counts, paid overage, conflicts
4. **Commit** → persist imports + users; evaluate cost alert threshold

### 7.2 API hooks (`UploadService`)

| Step | Figma branch |
|------|--------------|
| Mapping | `suggest_figma_column_mapping`, `FIGMA_MAPPING_FIELD_LABELS` |
| Parse | `_parse_figma_rows` → one `ParsedRow` per CSV user |
| Preview | `figma_summary` via `summarize_figma_aggregates` |
| Commit | `FigmaBillingImportService.commit_from_upload` |
| Delete | `FigmaBillingImportService.delete_by_upload_id` |

Team and tool are **required** for Figma uploads.

---

## 8. Billing insights API

### 8.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/figma/billing-insights?team_id&tool_id&from&to` | Main insights payload |
| GET | `/figma/billing-period-users?team_id&tool_id&period_start&period_end` | Users for a period |
| GET | `/figma/billing-day-users?team_id&tool_id&on_date` | Users for a chart day |

### 8.2 Frontend

| Component | Role |
|-----------|------|
| `InsightsPage` | Switches to `FigmaBillingInsightsPanel` when tool provider is `figma` |
| `FigmaBillingInsightsPanel` | Stats, trend, breakdown, top users, periods |
| `TeamToolDetailSlideOver` | `FigmaTeamToolSummary` for team tool chip |
| `frontend/src/api/figma.ts` | API client types |

---

## 9. Alerts

### 9.1 Team tool alert sync

`sync_team_tool_cost_alert` creates/updates an `admin.thresholds` cost rule when `alert_threshold_usd` is set on the team tool assignment.

### 9.2 Evaluation on import

After Copilot or Figma CSV commit, `evaluate_import_cost_alert` runs the synced threshold evaluator.

### 9.3 Threshold evaluator behaviour

When breach detected:

1. Create `notifications.threshold_events` record (appears in **Alerts → History**)
2. Send in-app notifications (`/alerts/history` deep link)
3. Set `threshold.active = false` (rule moves off **Active** tab until re-enabled)

### 9.4 Cost value for evaluation

`DashboardService._current_value_for_threshold` includes **import billing cost** (Copilot + Figma) for tool-scoped cost thresholds via `sum_import_billing_cost`.

---

## 10. Package catalogue (seed)

| Package | billing_type | Notes |
|---------|--------------|-------|
| Starter | SEAT_BASED | seat_limit 3 |
| Professional | SEAT_BASED | $15/mo reference |
| Organization | SEAT_BASED | |
| Enterprise | SEAT_BASED | |

---

## 11. Key files

### Backend

| Path | Purpose |
|------|---------|
| `app/figma/billing_import.py` | CSV parser, mapping, aggregates |
| `app/figma/pricing.py` | `calculate_figma_row_costs`, `figma_pricing_from_assignment` |
| `app/figma/billing_import_service.py` | Persist imports, period conflicts |
| `app/figma/service.py` | Billing insights analytics |
| `app/figma/router.py` | REST API |
| `app/figma/schemas.py` | Response models |
| `app/billing/import_cost_metrics.py` | Import cost for threshold evaluation |
| `app/notifications/import_cost_alert.py` | Post-import alert evaluation |
| `app/teams/figma_billing_metrics.py` | Team list cost rollup |
| `app/teams/team_tool_alert_sync.py` | Team tool → threshold rule sync |
| `app/thresholds/evaluator.py` | Breach detection + deactivate rule |
| `alembic/versions/034_figma_billing_import.py` | Schema migration |

### Frontend

| Path | Purpose |
|------|---------|
| `components/teams/TeamToolPackageSelector.tsx` | Figma team pricing UI |
| `components/insights/FigmaBillingInsightsPanel.tsx` | Insights dashboard |
| `components/teams/TeamToolDetailSlideOver.tsx` | Team tool summary |
| `pages/uploads/UploadPreviewPage.tsx` | Figma preview summary |
| `pages/uploads/UploadColumnMappingForm.tsx` | Auto-fill all mapping fields |
| `api/figma.ts`, `api/adapters/uploads.ts` | API adapters |

### Tests

| Path | Coverage |
|------|----------|
| `tests/test_figma_billing_import.py` | Parser, pricing, aggregates |

---

## 12. Acceptance criteria

- **AC-FIG-001:** Given Figma CSV with N users in one usage period, when imported, then N rows exist in `figma.billing_import_users` (not collapsed to one row).
- **AC-FIG-002:** Given team credits per USD = 100 and user paid credits = 50, when imported, then `paid_cost_usd = 0.50` and `seat_cost_usd = 0`.
- **AC-FIG-003:** Given seat credits used > 0 on CSV rows, when cost calculated, then seat credits do not add to USD total.
- **AC-FIG-004:** Given full seat amount $20 × 2 full seats and paid overage $5, when insights loaded, then `configured_seat_cost = 40`, `paid_cost = 5`, `total_cost = 45`.
- **AC-FIG-005:** Given Figma selected on team, when package dropdown shown, then subscription package is required and helper text matches Figma (aligned with Copilot pattern).
- **AC-FIG-006:** Given Figma CSV headers match export, when mapping page opens, then all columns are pre-mapped.
- **AC-FIG-007:** Given alert threshold exceeded on import, when evaluation runs, then notification sent, threshold rule inactive, event in alert history.
- **AC-FIG-008:** Given duplicate usage period already imported, when preview/commit, then period conflict warning blocks commit.

---

## 13. Demo checklist

1. Assign Figma to team → select **Subscription package** → set seat credit amounts + credits per USD + alert threshold.
2. Upload Figma CSV with team + tool → verify auto-mapped columns → import.
3. Open **Insights** with Figma tool → verify subscription + paid overage + total.
4. Open **Alerts → History** after threshold breach.
5. Re-import requires deleting prior upload for same usage period.
