# Tasks: Team List Usage Metrics

## 1. Backend

- [x] 1.1 `teams/cost_calculator.py` — pricing cost from resolved team–tool rates
- [x] 1.2 `teams/metrics.py` — batch load tokens, costs, pricing total, last sync for teams
- [x] 1.3 Extend `TeamResponse` with `tokens_used`, `pricing_total`, `total_cost`, `last_synced_at`
- [x] 1.4 Wire metrics into `list_teams` and `get_team`
- [x] 1.5 Update OpenAPI `Team` schema

## 2. Frontend

- [x] 2.1 Map new fields in `adapters/teams.ts`
- [x] 2.2 Replace budget columns with Tokens used, Pricing total, Total cost, Last synced
- [x] 2.3 Remove `BudgetUsageBar` from Teams list

## 3. Tests

- [x] 3.1 Cost calculator unit tests (per token, package, seat)
- [ ] 3.2 Metrics aggregation test with usage events
