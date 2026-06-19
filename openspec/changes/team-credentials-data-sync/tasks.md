# Tasks: Team credentials data sync

## Documentation

- [x] Add proposal and design for team → credentials → sync workflow
- [x] Update credentials-connect-tool-redesign design with required team + auto-sync

## Backend

- [x] Extract `sync_team_tools_for_organization` for API + background use
- [x] Add `run_team_sync_background` after credential create / secret update
- [x] Persist usage events with catalogue `tool_id` and resolved `team_id`
- [x] Expand `usage_tool_ids_for_filter` for catalogue + connected ids

## Frontend

- [x] Invalidate team and usage queries after credential connect / update

## Tests

- [x] Team sync internal entry point
- [x] Usage tool id filter includes catalogue id
- [x] Existing team tool sync tests pass
