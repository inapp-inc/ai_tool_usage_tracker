# Cursor Implementation — Functional Requirements

**Module:** Cursor-specific usage, cost, package, and Insights UX  
**Status:** Draft  
**Priority:** P0 (Phase 1 — Cursor only)  
**Related:** [02-dashboards.md](./02-dashboards.md) · [03-usage-tracking.md](./03-usage-tracking.md) · [team-pricing-configuration](../changes/team-pricing-configuration/proposal.md)

---

## 1. Purpose

InApp tracks Cursor usage via the filtered `usageEvents` API. Today the platform:

- Stores **total tokens** and sets **`estimated_cost = $0`** when Cursor `kind` contains `"include"` (e.g. *Included in Business*).
- Does **not** persist whether usage was plan-included vs billable.
- Shows Insights with **“All teams / All tools”** defaults and org-wide aggregates.
- Opens a **user drill-down** SlideOver when a team row is clicked (not team + package detail like the Admin → Teams tool chip flow).

This document defines requirements to:

1. Surface **package / pricing details** for team–tool assignments.
2. Track and display **included vs billable** Cursor usage and cost **separately**.
3. Open a **team detail side panel** (consistent with tool detail on Teams page).
4. Default Insights filters to **first team** and **first tool** on that team.
5. Show **hover tooltips** on Total Tokens and Total Cost stat cards with included vs billable breakdown (Cursor data only in Phase 1).

Other providers are **out of scope** until Cursor Phase 1 is complete.

---

## 2. Current State (baseline)

| Area | Current behaviour |
|------|-------------------|
| Cursor ingest | `usage_parsing.py` maps `kind` containing `"include"` → `estimated_cost = 0`; tokens still stored. |
| `usage_events` | No column for `kind`, `included_in_plan`, or split token/cost buckets. |
| Insights filters | `teamId = all`, `toolId = all` on load (`createDefaultFilters`). |
| Team row click | Opens SlideOver with user breakdown only; no package/pricing section. |
| Tool click (Teams admin) | Opens `TeamToolDetailSlideOver` with pricing + usage — **reference UX**. |
| Total Tokens / Cost cards | Single aggregate number; no tooltip breakdown. |
| Package allowance | Shown in cost widget via org tool config; not tied to Cursor included usage. |

---

## 3. Scope

### In scope (Phase 1 — Cursor)

- Backend schema + ingest changes for Cursor events only.
- Dashboard / Insights API extensions for included vs billable aggregates.
- Insights UI: default filters, team side panel, stat card tooltips.
- Package details in team side panel (from `team_tools` / tool pricing resolution).

### Out of scope (Phase 1)

- Copilot, Azure OpenAI, or other adapters.
- Historical backfill of `kind` for events ingested before this change (optional script noted as Phase 1.5).
- Changes to verification Excel format (may be extended later).

### Phase 2 (future)

- Same included/billable pattern for other vendors where API exposes plan vs overage.
- Org-wide “All teams” view with provider-aware tooltips.

---

## 4. Data Model & Ingestion

### FR-CSR-001: Persist Cursor plan-included flag on usage events

#### Description

When ingesting Cursor `usageEvents`, the system SHALL persist whether each event was **included in the subscription plan** vs **billable**, so aggregates can split totals without re-reading raw API dumps.

#### Business Rules

- **Included event:** Cursor `kind` contains `"include"` (case-insensitive), e.g. `"Included in Business"`.
- **Billable event:** all other kinds; cost = `chargedCents / 100`.
- Token counts (input, output, cache write, cache read) are stored for **both** included and billable events.
- `estimated_cost` remains the **billable cost only** (included events = `0`) for backward compatibility with existing cost widgets and reports.

#### Proposed schema addition (`usage.usage_events`)

| Column | Type | Notes |
|--------|------|--------|
| `included_in_plan` | `BOOLEAN NOT NULL DEFAULT false` | `true` when Cursor kind is plan-included |
| `cursor_kind` | `VARCHAR(128) NULL` | Raw Cursor `kind` string; null for non-Cursor providers |

Optional (if needed for tooltip cost on included rows):

| Column | Type | Notes |
|--------|------|--------|
| `reference_cost` | `NUMERIC(18,6) NULL` | Optional: `chargedCents/100` even when included (informational only) |

#### Acceptance Criteria

- **AC-CSR-001-01:** Given a Cursor event with `kind: "Included in Business"`, when ingested, then `included_in_plan = true`, tokens are stored, and `estimated_cost = 0`.
- **AC-CSR-001-02:** Given a Cursor event with `kind: "Usage-based"`, when ingested, then `included_in_plan = false` and `estimated_cost = chargedCents / 100`.
- **AC-CSR-001-03:** Given a non-Cursor provider event, when ingested, then `included_in_plan = false` and `cursor_kind` is null.
- **AC-CSR-001-04:** After deploy, operators MUST re-sync Cursor collectors so new columns are populated (existing rows default to `included_in_plan = false`).

#### Priority

**P0**

---

### FR-CSR-002: Aggregate included vs billable usage in dashboard APIs

#### Description

Dashboard and Insights APIs SHALL return separate totals for **included** and **billable** tokens and cost for the selected scope (team, tool, period).

#### Business Rules

- **Included tokens:** sum of `total_tokens` where `included_in_plan = true` and `provider = 'cursor'`.
- **Billable tokens:** sum of `total_tokens` where `included_in_plan = false`.
- **Billable cost:** sum of `estimated_cost` (unchanged semantics).
- **Included cost (display):** sum of `reference_cost` if stored; otherwise `0` or omitted with UI label “not tracked”.
- When filter tool is not Cursor (or `all`), tooltip fields MAY return `null` with `breakdown_available: false`.

#### API contract (extend existing widgets)

Extend `TokenUsageWidget` / stats payload:

```json
{
  "total_tokens": 1250000,
  "input_tokens": 800000,
  "output_tokens": 450000,
  "included_tokens": 900000,
  "billable_tokens": 350000,
  "breakdown_available": true
}
```

Extend cost / stats payload:

```json
{
  "actual_spend": 42.50,
  "included_tokens": 900000,
  "billable_tokens": 350000,
  "included_cost": 0,
  "billable_cost": 42.50,
  "package_allowance": 100.00,
  "overage_cost": 0,
  "breakdown_available": true
}
```

#### Acceptance Criteria

- **AC-CSR-002-01:** Given Cursor usage in period with mixed kinds, when `/dashboard/tokens` is called for that team+tool, then `included_tokens + billable_tokens = total_tokens`.
- **AC-CSR-002-02:** Given scope with no Cursor events, when breakdown is requested, then `breakdown_available = false` and UI hides Cursor-specific tooltip sections.
- **AC-CSR-002-03:** Aggregations respect existing RBAC team scope.

#### Dependencies

- FR-CSR-001

#### Priority

**P0**

---

## 5. Package & Pricing Details

### FR-CSR-003: Show package details in team and team–tool contexts

#### Description

Users SHALL see **package and pricing configuration** (allowance, plan name, per-token rates, seat count, overage rules) when inspecting a team or team–tool pair — matching the detail level already shown in Admin → Teams when clicking a **tool chip** (`TeamToolDetailSlideOver` + `TeamToolPricingSummary`).

#### Business Rules

- Pricing resolution order: **team_tools override** → **catalogue tool default** (existing `resolve_team_tool_pricing`).
- Package fields to display (when configured):

  | Field | Source |
  |-------|--------|
  | Pricing model | `pricing_model` / frontend model |
  | Plan name | `plan_name` |
  | Package allowance (tokens) | `package_allowance` |
  | Input / output token price | `token_price`, `output_token_price` |
  | Overage price | `overage_price` |
  | Cost per seat / seat count | `cost_per_seat`, `seat_count` |
  | Flat monthly cost | `pricing_config.flat_monthly_cost` |

- For Cursor connected credentials, show **sync status** and **last sync** where available.

#### User Stories

| ID | Role | Story |
|----|------|-------|
| US-CSR-003-01 | SA / TA | As an admin, I want to see package allowance and rates for a team’s Cursor tool so I can compare usage against the plan. |
| US-CSR-003-02 | SA / FV | As finance, I want package details beside usage so I can validate billable vs included consumption. |

#### Acceptance Criteria

- **AC-CSR-003-01:** Given a team with an assigned Cursor catalogue tool and team pricing override, when the team detail panel opens, then package section shows team override values with label “team override”.
- **AC-CSR-003-02:** Given no team override, when panel opens, then tool catalogue defaults are shown with label “tool default”.
- **AC-CSR-003-03:** Given hybrid / flat_fee model, when package allowance is set, then allowance displays in tokens with thousand separators.

#### Dependencies

- FR-ADM-001, team-pricing-configuration

#### Priority

**P0**

---

## 6. Insights UX — Team Side Panel

### FR-CSR-004: Team name click opens detail side panel (tool-parity UX)

#### Description

On the Insights **Usage by Team** tab (and team name links elsewhere on Insights), clicking a **team name** SHALL open a **right-side SlideOver** with team summary, package details, and usage breakdown — similar to clicking a tool on Admin → Teams, not only the current user-only drill-down.

#### Business Rules

- Panel sections (top to bottom):

  1. **Header:** team name, active status, period (from global date filter).
  2. **Usage summary:** total tokens, billable cost, included tokens (Cursor), billable tokens (Cursor).
  3. **Package details:** FR-CSR-003 for the **currently selected tool** in Insights filters (or first assigned tool if tool = all — see FR-CSR-005).
  4. **Tools assigned:** clickable chips → nested or replace panel with `TeamToolDetailSlideOver` content.
  5. **Users table:** existing per-user breakdown (current drilldown content).

- Clicking **team row** (not just name) MAY keep opening the same panel (consistent target).
- Panel width: 480–560px (align with existing SlideOver patterns).

#### Acceptance Criteria

- **AC-CSR-004-01:** Given Usage by Team table, when user clicks team name, then side panel opens without navigating away from Insights.
- **AC-CSR-004-02:** Given panel open, when user clicks an assigned tool chip, then tool pricing + usage section updates or opens tool detail sub-view.
- **AC-CSR-004-03:** Given Cursor included/billable data exists, when panel loads, then included and billable token counts are shown separately from total cost.

#### Dependencies

- FR-CSR-002, FR-CSR-003

#### Priority

**P0**

---

## 7. Insights UX — Default Filters

### FR-CSR-005: Default to first team and first associated tool

#### Description

On Insights load, the dashboard SHALL **not** default to org-wide “All teams / All tools”. It SHALL select the **first team** (per existing sort order in team list) and the **first tool associated with that team**, so all widgets show a concrete team+tool context aligned with how InApp operates (team-scoped Cursor credentials).

#### Business Rules

- **First team:** first active team in the same order as the Teams admin list / `fetchTeams` (name ascending unless product specifies otherwise).
- **First tool:** first entry in `team.tool_ids` array; if empty, first catalogue tool linked via team credential (`credential.teamId` + `catalogueToolId`).
- If user has access to only one team (Team Admin), select that team.
- If no teams exist, fall back to `all` / `all` and show empty state.
- Persist user’s manual filter changes in session (optional: `sessionStorage`) — not required for Phase 1.
- Changing team in filter dropdown resets tool to **first tool** for that team unless user explicitly picked a tool.

#### Acceptance Criteria

- **AC-CSR-005-01:** Given two teams with tools assigned, when Insights loads, then team filter = first team and tool filter = first tool on that team.
- **AC-CSR-005-02:** Given selected team has no tools, when Insights loads, then tool filter = `all` and banner explains no tools assigned.
- **AC-CSR-005-03:** Given Team Admin with one team, when Insights loads, then that team is selected automatically.

#### Dependencies

- FR-PLT-001 (RBAC)

#### Priority

**P0**

---

## 8. Insights UX — Stat Card Tooltips

### FR-CSR-006: Total Tokens card hover tooltip (included vs billable)

#### Description

The **Total Tokens** stat card on Insights SHALL show a **tooltip on hover** breaking down Cursor usage into **included in plan** and **billable** token counts, plus input/output/cache split when available.

#### Business Rules

- Tooltip appears on hover over the stat card (desktop); tap-to-toggle on touch devices.
- Content when `breakdown_available = true` and provider scope is Cursor:

  ```
  Total tokens:     1,250,000
  Included in plan:   900,000
  Billable:           350,000
  ─────────────────────────────
  Input:              800,000
  Output:             350,000
  Cache write:         50,000
  Cache read:          50,000
  ```

- When breakdown unavailable (non-Cursor tool or legacy data): show “Breakdown available after Cursor re-sync” or hide extended lines.
- Primary card value remains **total tokens** (included + billable).

#### Acceptance Criteria

- **AC-CSR-006-01:** Given Cursor mixed usage in period, when user hovers Total Tokens card, then tooltip shows included and billable counts matching API.
- **AC-CSR-006-02:** Given tool filter = non-Cursor, when user hovers, then tooltip shows totals only or a short “Cursor breakdown not applicable” message.

#### Dependencies

- FR-CSR-002, FR-CSR-005

#### Priority

**P0**

---

### FR-CSR-007: Total Cost card hover tooltip (included vs billable)

#### Description

The **Total Cost** stat card SHALL show a **tooltip on hover** with **billable cost**, **included usage cost** (if tracked), and **package allowance** context where configured.

#### Business Rules

- Tooltip content when Cursor breakdown available:

  ```
  Billable cost:      $42.50
  Included usage:     $0.00 (plan-covered)
  ─────────────────────────────
  Package allowance:  $100.00
  Allowance used:     42.5%
  Overage:            $0.00
  ```

- **Billable cost** = sum of `estimated_cost` (matches card primary value).
- **Included usage cost** = informational; use `reference_cost` sum if stored, else show tokens-only note for included portion.
- Package allowance from resolved team–tool pricing (FR-CSR-003), not org-wide sum of all tools.

#### Acceptance Criteria

- **AC-CSR-007-01:** Given billable Cursor usage, when user hovers Total Cost card, then billable cost in tooltip matches card value.
- **AC-CSR-007-02:** Given team–tool package allowance configured, when user hovers, then allowance and consumed % are shown.
- **AC-CSR-007-03:** Given included-only period (all events plan-included), when user hovers, then billable cost = $0 and included token count > 0.

#### Dependencies

- FR-CSR-002, FR-CSR-003, FR-CSR-005

#### Priority

**P0**

---

## 9. UI Component Notes (implementation hints)

| Component | Change |
|-----------|--------|
| `StatCard` | Add optional `tooltipContent?: ReactNode` or wrap with MUI `Tooltip`. |
| `InsightsPage` | Replace `createDefaultFilters()` logic with async default from teams + tools queries. |
| `TeamDetailSlideOver` (new) | Compose `TeamToolPricingSummary`, usage stats, user table; reuse patterns from `TeamToolDetailSlideOver`. |
| `TeamToolDetailSlideOver` | Reuse on Insights when tool chip clicked. |
| `fetchDashboardStats` / adapters | Map new included/billable fields from API. |

---

## 10. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-CSR-01 | Tooltip and panel open ≤ 200ms after data cached; no extra full-page load. |
| NFR-CSR-02 | Included/billable aggregation queries MUST use same indexes as existing `usage_events` team/tool/period filters. |
| NFR-CSR-03 | Migration MUST be backward-compatible; existing reports using `estimated_cost` unchanged. |

---

## 11. Test Strategy (high level)

| Scenario | Type |
|----------|------|
| Ingest included vs billable Cursor events | Unit (`usage_parsing`, persist) |
| Dashboard aggregates split correctly | Integration |
| Default first team/tool on Insights load | Frontend unit / e2e |
| Team panel shows package + users | Frontend e2e |
| Stat card tooltips with Cursor data | Frontend component |
| Re-sync after migration populates `included_in_plan` | Manual / staging |

---

## 12. Rollout & Operations

1. Deploy migration adding `included_in_plan` (+ optional `cursor_kind`, `reference_cost`).
2. Deploy API + frontend.
3. **Re-run Cursor collector sync** for each connected credential to backfill flags on new events.
4. Optional Phase 1.5: one-off script to set `included_in_plan` from stored cursor-pull JSON dumps for historical events.

---

## 13. Open Questions

| # | Question | Default if unresolved |
|---|----------|------------------------|
| 1 | Store `reference_cost` for included events? | Yes — helps finance compare “value consumed” vs $0 bill. |
| 2 | Team panel when tool = `all` — show all tools or force pick first? | Show first assigned tool + list chips. |
| 3 | Include package details on Overview tab or only Teams tab? | Both when team+tool filter active. |
| 4 | Should included tokens count against package allowance? | Yes for display; document formula in team pricing calculator follow-up. |

---

## 14. Traceability

| Requirement | Extends |
|-------------|---------|
| FR-CSR-001 – FR-CSR-002 | FR-USG-001, FR-ING-002 |
| FR-CSR-003 | FR-ADM-001, team-pricing-configuration |
| FR-CSR-004 – FR-CSR-007 | FR-DSH-001, FR-DSH-002, FR-DSH-004, FR-DSH-009 |

**Implementation order suggested:**

1. FR-CSR-001 (schema + ingest)  
2. FR-CSR-002 (API aggregates)  
3. FR-CSR-005 (default filters)  
4. FR-CSR-006, FR-CSR-007 (tooltips)  
5. FR-CSR-003, FR-CSR-004 (side panels + package details)
