# Proposal: Team Pricing Configuration

**Status:** 📋 Proposed

## Why

Pricing for AI tools varies by team: one team may have a flat-fee enterprise licence for GitHub Copilot while another pays per token for the same tool. Currently pricing is configured at the tool level globally. This prevents accurate per-team cost attribution and forces inaccurate estimates when different teams have different contract terms.

Moving pricing configuration to the team–tool pairing gives administrators full control: each team can define its own pricing model, token rates, seat count, or package allowance for every tool it uses.

## What Changes (this slice)

### Team Tool Assignments

Each team gains the ability to associate tools with a pricing configuration. A `team_tools` join table stores per-team pricing overrides.

New concept: **Team Tool Assignment**
- A team can have zero or more tool assignments.
- Each assignment optionally carries: `pricing_model`, `token_price`, `output_token_price`, `cost_per_seat`, `seat_count`, `package_allowance`, `overage_price`, `plan_name`.
- When pricing fields are absent on the assignment, the system falls back to tool-level defaults for cost calculations.

### Teams UI

The Team create/edit panel gains a **"Tools & Pricing"** section:
- Multi-select: choose which tools this team uses.
- For each selected tool: expand to configure pricing model and cost fields.
- Pricing fields mirror the existing tool pricing form (moved here from the tool form).

### API endpoints

```
GET    /api/v1/teams/{teamId}/tools          → TeamToolAssignmentListResponse
POST   /api/v1/teams/{teamId}/tools          → TeamToolAssignment (201)
PATCH  /api/v1/teams/{teamId}/tools/{toolId} → TeamToolAssignment (200)
DELETE /api/v1/teams/{teamId}/tools/{toolId} → 204
```

## Out of Scope

- Retroactive cost recalculation against team pricing (separate reporting task)
- Tool-level default pricing (existing fields remain for fallback but are informational; removed from the Add Tool UI)

## Dependencies

- `tool-catalogue-redesign` — pricing removed from tool form
- FR-ADM-002 (Team Management)
- FR-ADM-001 (AI Tool Management)
