# Design: Team Pricing Configuration

## Database

New table `admin.team_tools`:

```sql
CREATE TABLE admin.team_tools (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id          UUID NOT NULL REFERENCES admin.teams(id) ON DELETE CASCADE,
    tool_id          UUID NOT NULL REFERENCES admin.tools(id) ON DELETE CASCADE,
    pricing_model    VARCHAR(32),       -- flat_token | package_with_overage | custom | per_seat
    token_price      NUMERIC(18,8),
    output_token_price NUMERIC(18,8),
    cost_per_seat    NUMERIC(18,4),
    seat_count       INTEGER,
    package_allowance BIGINT,
    overage_price    NUMERIC(18,8),
    plan_name        VARCHAR(200),
    pricing_config   JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now(),
    UNIQUE (team_id, tool_id)
);
```

## API Schemas

### `TeamToolAssignment` response

```yaml
id: string (uuid)
team_id: string (uuid)
tool_id: string (uuid)
tool_name: string          # denormalized for display
pricing_model: string | null
token_price: number | null
output_token_price: number | null
cost_per_seat: number | null
seat_count: integer | null
package_allowance: integer | null
overage_price: number | null
plan_name: string | null
created_at: string (datetime)
updated_at: string (datetime)
```

### `TeamToolAssignRequest` (create/update)

```yaml
tool_id: string (uuid)        # required on create; ignored on update
pricing_model: string | null
token_price: number | null
output_token_price: number | null
cost_per_seat: number | null
seat_count: integer | null
package_allowance: integer | null
overage_price: number | null
plan_name: string | null
```

## Frontend

### TeamsPage

The team create/edit slide-over gains a **"Tools & Pricing"** accordion section below the team name field:

1. Tool multi-select (loads from `GET /api/v1/tools?active=true`)
2. For each selected tool: collapsible pricing row with:
   - Pricing model selector (Per token / Per seat / Flat fee / Hybrid)
   - Conditional fields matching the existing ToolPricing shape
3. "Unsaved tool assignments" are submitted on team save (batch create/update calls)

### New API module: `frontend/src/api/teamTools.ts`

- `fetchTeamTools(teamId)` → `TeamToolAssignment[]`
- `upsertTeamTool(teamId, body)` → `TeamToolAssignment`
- `removeTeamTool(teamId, toolId)` → void

## Cost Calculation Precedence

1. `team_tools.pricing_model` + cost fields (if set for the team–tool pair)
2. `admin.tools` default pricing fields (fallback)
3. Zero cost (graceful degradation)

## RBAC

- Super Admin: full CRUD on team–tool assignments for any team.
- Team Admin: read and update assignments only for teams they administer.
