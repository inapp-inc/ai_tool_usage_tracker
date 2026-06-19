# Proposal: Team credentials data sync

## Problem

Admins create **Teams** with multiple catalogue tools assigned, then connect **Credentials** (catalogue tool + team + API key). After a successful connect, **Teams should show usage metrics and members** for every assigned tool that has a live credential. Today, data often stays empty because:

- Usage sync runs only for the single connected credential record, not the full team assignment set.
- Usage events may be stored with the connected tool id while team metrics expect catalogue tool ids.
- The workflow is not documented end-to-end.

## Goal

Document and implement the intended workflow:

1. **Teams** — assign one or more catalogue tools (with optional team-level pricing).
2. **Credentials** — connect a catalogue tool to a team with an API key.
3. **Automatic sync** — on successful connect (or secret rotation), pull usage for all connected credentials on that team.
4. **Team display** — list metrics (tokens, cost, last synced) and members from ingested usage + provider member APIs.

## Scope

- OpenSpec design for workflow and data attribution rules.
- Backend: team-scoped background sync after credential connect; usage events attributed to **team id** and **catalogue tool id**.
- Frontend: refresh team/dashboard queries after connect.
- Tests for catalogue tool id persistence and team sync trigger.

## Out of scope

- Changing the Teams or Credentials UI layout.
- New provider adapters.

## Success criteria

- After connecting a credential for Team A + Tool X, Team A shows non-zero usage (when the provider returns data) without manual refresh.
- `POST /teams/{id}/sync` and auto-sync after connect use the same code path.
- Usage events have `team_id` and catalogue `tool_id` set for assigned teams.
