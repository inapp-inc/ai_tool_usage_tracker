# Multi-Vendor Architecture & Product Design

**Module:** Tool catalogue, packages, billing types, vendor adapters, dashboards  
**Status:** Draft (target architecture)  
**Priority:** P0 (platform evolution — post Cursor Phase 1)  
**Related:** [cursor-implementation.md](./cursor-implementation.md) · [02-dashboards.md](./02-dashboards.md) · [06-usage-ingestion.md](./06-usage-ingestion.md) · [database.md](../specifications/database.md) · [provider-creation.md](../specifications/provider-creation.md)

---

## 1. Objective

Build an **enterprise-grade AI Tool Usage Tracker** that supports multiple AI vendors with different billing models:

| Billing model | Examples |
|---------------|----------|
| **Token based** | OpenAI, Claude, Gemini, Azure OpenAI, Bedrock, Vertex AI |
| **Request based** | Cursor, Copilot Chat |
| **Credit based** | Cursor Max, OpenRouter |
| **Seat based** | Figma, GitHub Copilot Business, Notion AI, Grammarly |
| **License based** | Enterprise SKUs with fixed entitlement periods |

The platform SHALL:

1. **Normalize** all vendor data into a **common usage schema** for reporting, alerts, and executive KPIs.
2. **Preserve** vendor-specific dimensions (models, agents, seats, credits, languages, etc.) for drill-down dashboards and insights.
3. **Bind** each team to a **tool + package + budget** so spend and utilization are measured against the correct entitlement.

---

## 2. Core Concept

Every tool in the catalogue belongs to exactly one **billing type**. Adapters map vendor API payloads into the common schema; dashboard widgets and insight panels are selected by billing type + vendor.

```
Vendor API  →  Adapter (parse + cost rules)  →  usage_events (canonical)
                     ↓
              tool_master.billing_type  →  Dashboard template + Insights template
                     ↓
              team_tools.package_id     →  Allowance, budget, alerts
```

### 2.1 Billing Types

#### TOKEN_BASED

**Examples:** OpenAI, Claude, Gemini, Azure OpenAI, Bedrock, Vertex AI

| Metric | Description |
|--------|-------------|
| Input tokens | Prompt / context tokens |
| Output tokens | Completion tokens |
| Cached tokens | Cache read + cache write (where API exposes) |
| Requests | API call count (optional) |
| Cost | Billable USD (vendor-reported or calculated) |

**Dashboard emphasis:** token trends, cost per model, top users, input vs output split.

---

#### REQUEST_BASED

**Examples:** Cursor (usage events), Copilot Chat

| Metric | Description |
|--------|-------------|
| Requests | Discrete API / UI actions |
| Chat sessions | Session count (where available) |
| Agent runs | Agent-mode invocations |
| Completions | Composer / inline completions |
| Tokens | Often present as secondary metric (Cursor) |
| Cost | Plan-included vs additional billable (Cursor — see [cursor-implementation.md](./cursor-implementation.md)) |

**Dashboard emphasis:** request mix, agent adoption, included vs billable cost, top consumers.

---

#### CREDIT_BASED

**Examples:** Cursor Max, OpenRouter

| Metric | Description |
|--------|-------------|
| Credits consumed | Units debited in period |
| Credits remaining | Balance / quota left |
| Cost | USD equivalent of credits |

**Dashboard emphasis:** credit burn rate, runway, top credit consumers.

---

#### SEAT_BASED

**Examples:** Figma, GitHub Copilot Business, Notion AI, Grammarly

| Metric | Description |
|--------|-------------|
| Purchased seats | Licensed seat count |
| Assigned seats | Seats allocated to users |
| Active seats | Seats with activity in period |
| Inactive seats | Assigned but no activity |
| Cost | Subscription / per-seat cost |

**Dashboard emphasis:** license utilization, unused seats, active vs assigned ratio.

---

#### LICENSE_BASED

**Examples:** Enterprise agreements with fixed annual entitlement

Same seat-oriented metrics as SEAT_BASED, plus **subscription window**, **renewal date**, and **contract cap** fields on `team_tools`.

---

## 3. Data Model (Target)

> **Note:** Phase 1 uses `admin.tools`, `admin.team_tools`, and `usage.usage_events` with Cursor-specific columns (`included_in_plan`, `cursor_kind`, `reference_cost`). This section defines the **target** catalogue model for multi-vendor rollout. Migrations SHALL extend existing tables or add companion tables without breaking current Cursor flows.

### 3.1 Tool Master — `tool_master`

Canonical catalogue entry for each vendor product the org can monitor.

```sql
CREATE TABLE admin.tool_master (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(128) NOT NULL,
    vendor          VARCHAR(64)  NOT NULL,   -- e.g. cursor, openai, figma
    billing_type    VARCHAR(32)  NOT NULL,   -- TOKEN_BASED | REQUEST_BASED | ...
    logo_url        TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_tool_master_billing_type CHECK (
        billing_type IN (
            'TOKEN_BASED', 'REQUEST_BASED', 'CREDIT_BASED',
            'SEAT_BASED', 'LICENSE_BASED'
        )
    )
);
```

**Mapping from current schema:** `admin.tools` (catalogue row) gains or aligns with `billing_type`; `vendor` already exists.

---

### 3.2 Tool Package Master — `tool_packages`

Predefined or admin-seeded packages per tool (Hobby / Pro / Business, Pay-as-you-go, etc.).

```sql
CREATE TABLE admin.tool_packages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id         UUID NOT NULL REFERENCES admin.tool_master(id) ON DELETE CASCADE,
    package_name    VARCHAR(128) NOT NULL,
    billing_type    VARCHAR(32)  NOT NULL,  -- mirrors tool; denormalized for query speed
    monthly_price   NUMERIC(18, 6),
    yearly_price    NUMERIC(18, 6),
    seat_limit      INTEGER,
    token_limit     BIGINT,
    request_limit   BIGINT,
    credit_limit    NUMERIC(18, 6),
    currency        CHAR(3) NOT NULL DEFAULT 'USD',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Limits:** At most one primary limit column is authoritative per `billing_type` (e.g. `token_limit` for TOKEN_BASED, `seat_limit` for SEAT_BASED).

---

### 3.3 Example Hardcoded Packages (Seed Data)

| Vendor | Packages |
|--------|----------|
| **Cursor** | Hobby, Pro, Business, Enterprise |
| **OpenAI** | Pay As You Go, Scale Tier, Enterprise |
| **Copilot** | Individual, Business, Enterprise |
| **Figma** | Starter, Professional, Organization, Enterprise |
| **Claude** | Free, Pro, Team, Enterprise |
| **Gemini** | Free, Advanced, Workspace Enterprise |

Seed scripts SHALL idempotently upsert packages; orgs select from catalogue — no free-text plan names in production UI.

---

### 3.4 Team Tool Configuration — `team_tools`

Extends current team–tool assignment with explicit package binding and budget.

```sql
-- Target columns (extend admin.team_tools / team_tool assignments)
team_id              UUID NOT NULL REFERENCES admin.teams(id),
tool_id              UUID NOT NULL REFERENCES admin.tool_master(id),
package_id           UUID REFERENCES admin.tool_packages(id),
subscription_start   DATE,
subscription_end     DATE,
monthly_budget       NUMERIC(18, 6),
alert_threshold      NUMERIC(5, 2),   -- % of budget or allowance
notes                TEXT,
-- existing pricing override columns retained for edge cases
```

**Admin UX flow:**

```
Team  →  Tool  →  Available packages (filtered by tool)  →  Budget + alert threshold
```

Package selection drives default allowances (`token_limit`, `seat_limit`, etc.) on the Insights and team detail panels.

---

### 3.5 Common Usage Schema — `usage_events`

Target canonical fact table (extends `usage.usage_events`):

```sql
CREATE TABLE usage.usage_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source              VARCHAR(32)  NOT NULL,  -- collector | upload | manual
    tool_id             UUID REFERENCES admin.tools(id),
    team_id             UUID REFERENCES admin.teams(id),
    organization_id     UUID REFERENCES auth.organizations(id),
    user_email          VARCHAR(255),
    user_id             UUID REFERENCES auth.users(id),
    occurred_at         TIMESTAMPTZ NOT NULL,
    provider            VARCHAR(64)  NOT NULL,  -- vendor slug
    model               VARCHAR(128),

    -- Request / session (REQUEST_BASED)
    request_type        VARCHAR(64),            -- chat | agent | composer | ...
    requests            INTEGER NOT NULL DEFAULT 0,

    -- Token (TOKEN_BASED / REQUEST_BASED secondary)
    input_tokens        BIGINT NOT NULL DEFAULT 0,
    output_tokens       BIGINT NOT NULL DEFAULT 0,
    cache_write_tokens  BIGINT NOT NULL DEFAULT 0,
    cache_read_tokens   BIGINT NOT NULL DEFAULT 0,
    total_tokens        BIGINT NOT NULL DEFAULT 0,

    -- Credit (CREDIT_BASED)
    credits_used        NUMERIC(18, 6),

    -- Cost
    cost_usd            NUMERIC(18, 6) NOT NULL DEFAULT 0,  -- maps to estimated_cost
    included_in_plan    BOOLEAN NOT NULL DEFAULT false,       -- Cursor / plan split
    reference_cost      NUMERIC(18, 6),                       -- plan consumption value
    cursor_kind         VARCHAR(128),                         -- vendor-specific; nullable

    vendor_event_id     VARCHAR(255),
    raw_payload         JSONB,                                  -- optional; or external object store
    collector_id        UUID,
    upload_id           UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Effective cost rule (implemented for Cursor):**

| Row type | `cost_usd` (billable) | `reference_cost` (plan) |
|----------|------------------------|-------------------------|
| Included in plan | `0` | Token/request value from vendor (`totalCents` / `chargedCents`) |
| Additional billable | Vendor charged amount | `NULL` |
| **Display total** | `reference_cost + cost_usd` (via `usage_event_effective_cost_sql`) | |

Non-Cursor vendors SHALL follow the same pattern where the API distinguishes plan vs overage.

---

## 4. Adapter Architecture

Each vendor implements:

| Component | Responsibility |
|-----------|----------------|
| **Collector adapter** | Pull usage from vendor API; paginate; map to `UsageRecord` |
| **Cost resolver** | Apply billing-type rules (included vs billable, credits, seats) |
| **Dashboard profile** | Widget set + insight panels for UI routing |
| **Verification export** | Optional Excel/CSV parity check (Cursor pattern) |

Adapters MUST NOT write directly to API responses; all persistence goes through `usage_events` + aggregator services.

---

## 5. Vendor-Specific Implementations

### 5.1 OpenAI

**APIs**

- `/v1/organization/usage/completions`
- `/v1/organization/costs`

**Billing type:** `TOKEN_BASED`

**Dashboard cards:** Total Tokens, Input Tokens, Output Tokens, Total Cost, Requests

**Charts:** Usage trend, Cost trend, Top users, Top models, Top projects

**Insights:** Most expensive user, Most used model, Unused projects, Cost forecast

---

### 5.2 Claude

**API:** Admin API · Usage API

**Billing type:** `TOKEN_BASED`

**Dashboard cards:** Total Tokens, Input Tokens, Output Tokens, Cost, Messages

**Insights:** Top teams, Top users, Most used models, Opus vs Sonnet comparison

---

### 5.3 Gemini

**API:** Google AI Studio · Vertex AI

**Billing type:** `TOKEN_BASED`

**Dashboard cards:** Prompt count, Tokens, Cost, Projects, Regions, Models

**Insights:** Top projects, Top models, High-cost users

---

### 5.4 Cursor

**API:** `/teams/filtered-usage-events`

**Billing type:** `REQUEST_BASED` (with token + cost dimensions)

**Status:** Phase 1 implemented — see [cursor-implementation.md](./cursor-implementation.md)

**Dashboard cards:** Total Tokens, Total Cost, Agent usage, Chat usage, Composer usage, Top users, Top models, Top cost consumers

**Insights:** Agent adoption, Token consumption trend, Model distribution, Cost per user, Accepted lines, Deleted lines, Chat requests

**Cost rules:** Included kind → plan consumption (`reference_cost`); non-included → additional billable (`cost_usd`).

---

### 5.5 GitHub Copilot

**Full specification:** [copilot-productivity-analytics.md](./copilot-productivity-analytics.md)

**OpenSpec change:** `copilot-schema`

**API**

- `/orgs/{org}/copilot/metrics/reports/users-1-day` (user usage)
- `/orgs/{org}/copilot/metrics/reports/organization-1-day` (org usage)
- `/orgs/{org}/copilot/billing/seats`

**Billing type:** `SEAT_BASED` — productivity analytics, **not** token consumption

**Dashboard cards:** Total seats, Assigned seats, Active users, Inactive users, Monthly cost, Seat utilization %, Average acceptance rate

**Charts:** Seat utilization, Active users trend, Suggestions vs acceptances, Top languages, IDE distribution

**Insights:** Adoption, License waste, Power users, Acceptance rate, IDE/language concentration

**Dedicated UI:** `/insights/copilot`

---

### 5.6 Figma

**API:** Organization API · Activity Logs API

**Billing type:** `SEAT_BASED`

**Dashboard cards:** Total seats, Assigned seats, Active users, Inactive users, Files created, Projects, Teams

**Insights:** Unused seats, Most active designers, File activity trend, Team activity, License utilization

---

### 5.7 Notion AI

**Billing type:** `SEAT_BASED`

**Dashboard cards:** Seats, Active users, Pages created, AI usage, Workspace activity

**Insights:** Unused seats, Most active users, Workspace adoption

---

### 5.8 Grammarly

**Billing type:** `SEAT_BASED`

**Dashboard cards:** Seats, Active users, Writing sessions, Suggestions accepted, Writing improvements

**Insights:** Most active users, Seat utilization, Writing adoption

---

## 6. Executive Dashboard

Org-wide view aggregating all billing types into unified KPIs.

### 6.1 Global KPIs

| KPI | Source |
|-----|--------|
| Total AI spend | Sum effective cost across all tools |
| Total tools | Active catalogue tools |
| Total teams | Active teams with assignments |
| Total users | Distinct users with usage in period |
| Total tokens | Sum where `billing_type` supports tokens |
| Total seats | Sum purchased/assigned where seat-based |
| Total requests | Sum where request-based |
| Total credits | Sum where credit-based |
| Top cost tool | Rank by spend |
| Top cost team | Rank by spend |
| Top cost user | Rank by spend |

### 6.2 Charts

- Spend by tool
- Spend by team
- Spend by user
- Usage trend (normalized units per billing type)
- Monthly growth
- Tool adoption
- License utilization (seat-based tools)
- AI ROI score (configurable formula — Phase 2)

### 6.3 Executive Insights

- Highest cost tool
- Unused licenses
- Inactive teams
- Forecasted monthly cost
- Forecasted annual cost
- Most valuable tool (usage vs cost)
- Least utilized tool
- Optimization recommendations

### 6.4 Alert Center

| Alert type | Trigger |
|------------|---------|
| Budget exceeded | Team tool `monthly_budget` |
| Token threshold | Package `token_limit` |
| Seat threshold | `assigned_seats / purchased_seats` |
| Inactive license warning | Seat assigned, no activity N days |
| Package renewal reminder | `subscription_end` approaching |
| Cost spike detection | Period-over-period $ delta |
| Package expiry notification | `subscription_end` passed |

---

## 7. UI Routing by Billing Type

Insights and tool detail panels SHALL select widgets from a **dashboard profile** registry:

```typescript
type DashboardProfile = {
  billingType: BillingType;
  vendor?: string;
  statCards: StatCardDefinition[];
  charts: ChartDefinition[];
  insights: InsightPanelDefinition[];
};
```

| Billing type | Default stat cards | Default charts |
|--------------|-------------------|----------------|
| TOKEN_BASED | Tokens, Input, Output, Cost | Usage trend, Cost trend, Top models |
| REQUEST_BASED | Requests, Tokens, Cost, Included vs billable | Request mix, Top users |
| CREDIT_BASED | Credits used, Remaining, Cost | Burn rate |
| SEAT_BASED | Purchased, Assigned, Active, Utilization % | Seat trend, Inactive list |

Vendor-specific panels (e.g. Cursor agent adoption) extend the profile via `vendor` key.

---

## 8. Implementation Phases

| Phase | Scope | Status |
|-------|--------|--------|
| **1** | Cursor REQUEST_BASED ingest, included vs billable cost, Insights UX | In progress — [cursor-implementation.md](./cursor-implementation.md) |
| **2** | `tool_packages` seed + team package picker; migrate pricing overrides | Planned |
| **3** | OpenAI + Claude TOKEN_BASED adapters | Planned |
| **4** | Copilot + Figma SEAT_BASED adapters | Planned |
| **5** | Executive dashboard + cross-tool alerts | Planned |
| **6** | Credit-based (OpenRouter, Cursor Max) | Planned |

---

## 9. Acceptance Criteria (Platform)

- **AC-MVT-001:** Given a tool with `billing_type = SEAT_BASED`, when Insights loads for that tool, then seat KPIs render and token-only widgets are hidden.
- **AC-MVT-002:** Given a team bound to `package_id`, when usage is aggregated, then allowance and budget comparisons use package limits—not org-wide defaults.
- **AC-MVT-003:** Given usage from two vendors in the same period, when Executive dashboard loads, then total spend equals sum of effective costs across all events.
- **AC-MVT-004:** Given a new vendor adapter, when events are ingested, then all rows conform to `usage_events` schema without vendor-specific columns required for cross-tool reports.
- **AC-MVT-005:** Given Cursor included + billable events, when cost API is called, then total = included plan cost + additional billable cost.

---

## 10. Dependencies & References

| Area | Document |
|------|----------|
| Current DB schema | [database.md](../specifications/database.md) |
| Dashboard requirements | [02-dashboards.md](./02-dashboards.md) |
| Ingestion | [06-usage-ingestion.md](./06-usage-ingestion.md) |
| Cursor Phase 1 | [cursor-implementation.md](./cursor-implementation.md) |
| Team pricing (today) | [team-pricing-configuration](../changes/team-pricing-configuration/proposal.md) |
| Dynamic providers | [provider-creation.md](../specifications/provider-creation.md) |
| Tool catalogue redesign | [tool-catalogue-redesign](../changes/tool-catalogue-redesign/proposal.md) |

---

## 11. Open Questions

1. **Single vs dual table for tools:** Merge `admin.tools` into `tool_master` or add `billing_type` + FK to packages on existing table?
2. **raw_payload retention:** Store in PostgreSQL JSONB vs object store (S3/local) with pointer on row?
3. **ROI score formula:** Finance-defined or configurable per org?
4. **License-based vs seat-based:** Single billing type with flags, or separate enum value?

---

*Last updated: 2026-06-17 — initial architecture from product design prompt.*
