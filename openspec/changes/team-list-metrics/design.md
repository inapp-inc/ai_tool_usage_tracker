# Design: Team List Usage Metrics

## Period

All usage aggregates use the **current calendar month** (UTC): `start_of_month(now)` → `now`.

## Aggregations

### Tokens used & total cost

```sql
SELECT team_id,
       SUM(total_tokens),
       SUM(estimated_cost)
FROM usage.usage_events
WHERE organization_id = :org
  AND team_id IS NOT NULL
  AND occurred_at >= :month_start
  AND occurred_at <= :now
GROUP BY team_id
```

Includes rows from **CSV uploads** (`upload_id` set) and **collector sync** (`collector_id` set).

### Pricing total

Per team, per assigned tool:

1. Group usage: `(team_id, tool_id) → input_tokens, output_tokens, total_tokens`
2. Resolve pricing via `resolve_team_tool_pricing(team_tool, tool)`
3. Apply `calculate_pricing_cost(pricing, input, output, total)` (see `teams/cost_calculator.py`)
4. Sum across tools; events without `tool_id` contribute `estimated_cost` to pricing total as fallback

### Last synced

For each team, union of `team.tool_ids` and `admin.team_tools.tool_id`:

```sql
SELECT MAX(t.last_sync_at)
FROM admin.tools t
WHERE t.id = ANY(:tool_ids) AND t.organization_id = :org
```

Null when no tools synced yet.

## API schema delta

```yaml
Team:
  properties:
    tokens_used:
      type: integer
      description: Total tokens this calendar month (imports + API).
    pricing_total:
      type: number
      description: Cost from team–tool pricing applied to usage.
    total_cost:
      type: number
      description: Sum of estimated_cost on usage events this month.
    last_synced_at:
      type: string
      format: date-time
      nullable: true
```

## Frontend

`TeamsPage` columns: Team, Members, Tools, **Tokens used**, **Pricing total**, **Total cost**, **Last synced**, Status, Actions.

Remove `BudgetUsageBar` from the list. Map new API fields in `adapters/teams.ts`.
