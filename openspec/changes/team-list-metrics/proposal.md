# Proposal: Team List Usage Metrics

**Status:** 📋 Proposed

## Why

The Teams list still shows **Token budget** and **Cost budget** progress bars, but operators need to see **actual team activity**: tokens consumed, costs from usage (imports + live API sync), pricing-based totals using team–tool rates, and when data was last collected.

## What Changes

### Teams list columns (replace budget bars)

| Remove | Add |
|--------|-----|
| Token budget | **Tokens used** (current calendar month) |
| Cost budget | **Pricing total** (cost from team–tool pricing applied to usage) |
| | **Total cost** (sum of `estimated_cost` on usage events — imports + API) |
| | **Last synced** (latest `last_sync_at` across assigned tools with credentials) |

Budget fields remain on the team edit form for threshold alerts; they are removed from the **list view only**.

### Data sources

| Field | Source |
|-------|--------|
| Tokens used | `usage.usage_events` where `team_id` matches, current month |
| Total cost | Sum of `estimated_cost` on those events (CSV imports + collector API sync) |
| Pricing total | Team–tool pricing (`admin.team_tools` → tool fallback) applied to token totals per tool |
| Last synced | `MAX(admin.tools.last_sync_at)` for tools assigned to the team |

### API

Extend `Team` response (list + get) with:

```yaml
tokens_used: integer
pricing_total: number
total_cost: number
last_synced_at: string (datetime) | null
```

## Out of Scope

- Removing budget fields from team create/edit
- Retroactive cost recalculation job
- Custom date range on the list (fixed to current calendar month)

## Dependencies

- `team-pricing-configuration` — team–tool pricing overrides
- Usage attribution (`usage.usage_events.team_id`, `tool_id`)
- Credentials / tool sync (`admin.tools.last_sync_at`)
