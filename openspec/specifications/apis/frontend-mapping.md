# Frontend ↔ OpenAPI Mapping

**Status:** Active  
**Date:** 2026-06-16  
**Scope:** `frontend/src/api/*` on branch `develop` (mock-first SPA)  
**Canonical contract:** [openapi.yaml](./openapi.yaml) · [schemas.yaml](./components/schemas.yaml)

This document inventories every API function exported from the frontend, maps it to the target OpenAPI operation, documents **request payloads** and **response shapes**, and records implementation status.

---

## Conventions

| Aspect | Value |
|--------|-------|
| Base path | `/api/v1` (`VITE_API_BASE_URL`, default `/api/v1`) |
| HTTP client | `frontend/src/api/client.ts` — Bearer JWT, `X-Correlation-ID`, 401 refresh retry |
| Mock pattern | In-memory data + artificial latency (`MOCK_LATENCY_MS`) |
| Frontend casing | **camelCase** in TypeScript types and mock JSON |
| OpenAPI casing | **snake_case** in request/response bodies |
| List responses | OpenAPI: `{ data: T[], meta: PaginationMeta }` · Mock: bare `T[]` (no envelope yet) |
| Date filters | ISO 8601 strings in query (`from`, `to`) — UTC |

### Implementation status

| Status | Meaning |
|--------|---------|
| **mock** | No HTTP call; local in-memory implementation |
| **partial** | Some functions call the API; others are mocked |
| **wired** | All functions use `apiFetch` / `apiRequest` against the contract path |

### Adapter rules (when wiring mocks → backend)

1. Unwrap `response.data` from list endpoints via `apiRequest` (already supported in `client.ts`).
2. Map snake_case ↔ camelCase at the API module boundary (not in page components).
3. Map enum differences explicitly (see per-module delta tables below).
4. Composite UI types (e.g. `DashboardStats`) may require multiple OpenAPI calls or a BFF aggregate endpoint.

---

## Summary

| Module | Functions | Wired | Mock | Primary pages |
|--------|-----------|-------|------|---------------|
| `auth.ts` | 4 | 4 | 0 | Login, session restore |
| `tools.ts` | 5 | 5 | 0 | Admin → Tools |
| `teams.ts` | 4 | 4 | 0 | Admin → Teams, Uploads, Alerts, Insights |
| `members.ts` | 5 | 0 | 5 | Admin → Members |
| `credentials.ts` | 4 | 0 | 4 | Admin → Credentials |
| `alerts.ts` | 6 | 0 | 6 | Alerts |
| `uploads.ts` | 5 | 0 | 5 | Uploads, Upload preview |
| `dashboard.ts` | 5 | 0 | 5 | Insights (overview tab) |
| `usage.ts` | 7 | 0 | 7 | Insights (usage tab), Admin dropdowns |
| `reports.ts` | 7 | 0 | 7 | Insights (reports tab) |
| `auditLog.ts` | 1 | 0 | 1 | Admin → Audit log |
| `notifications.ts` | 0 | — | — | Placeholder (empty export) |

**Total frontend API surface:** 53 exported functions across 11 domain modules.

### Completed backend modules

| Module | Frontend | Backend change | Completed |
|--------|----------|----------------|-----------|
| Auth | `auth.ts` (4/4 wired) | [authentication-backend](../../changes/authentication-backend/) | 2026-06-16 |
| Teams | `teams.ts` (4/4 wired) | [teams-backend](../../changes/teams-backend/) | 2026-06-16 |
| Tools | `tools.ts` (5/5 wired) | [apis/tools/](./tools/) | 2026-06-16 |

---

## Auth — `frontend/src/api/auth.ts`

| Function | Method | Path | OpenAPI schema (req → res) | Status |
|----------|--------|------|---------------------------|--------|
| `login` | POST | `/auth/login` | `LoginRequest` → `TokenResponse` + profile | wired |
| `refreshToken` | POST | `/auth/refresh` | `RefreshRequest` → `TokenResponse` | wired |
| `fetchCurrentUser` | GET | `/auth/me` | — → `UserProfile` | wired |
| `restoreAuthSession` | — | refresh + me | composite | wired |

### `login`

**Request body** (`LoginRequest`)

| Field | Type | Required | OpenAPI `LoginRequest` |
|-------|------|----------|------------------------|
| `email` | string | yes | `email` |
| `password` | string | yes | `password` |

**Response** (`LoginResponse` — mock only; differs from OpenAPI)

| Field | Type | OpenAPI equivalent | Notes |
|-------|------|-------------------|-------|
| `user` | `User` | from `GET /auth/me` after login | Mock embeds user inline |
| `user.id` | string | `UserProfile.id` | |
| `user.email` | string | `UserProfile.email` | |
| `user.name` | string | `UserProfile.display_name` | rename |
| `user.platformRole` | `Role` | `UserProfile.role` | same enum values |
| `user.teamMemberships` | `TeamMembership[]` | derived from `team_ids` | mock builds `{ teamId, teamName, role }` |
| `accessToken` | string | `TokenResponse.access_token` | rename |

**Target OpenAPI flow:** `POST /auth/login` → `TokenResponse`, then optional `GET /auth/me` → `UserProfile`.

### `refreshToken`

**Request body**

| Field | Type | OpenAPI `RefreshRequest` |
|-------|------|--------------------------|
| `refresh_token` | string | `refresh_token` |

**Response** (`TokenResponse`)

| Field | Type | Notes |
|-------|------|-------|
| `access_token` | string | stored via `setAccessToken` |
| `refresh_token` | string? | rotated when returned |
| `token_type` | string | `"Bearer"` |
| `expires_in` | number | seconds |

### `fetchCurrentUser`

**Response** — mapped to frontend `User`

| OpenAPI `UserProfile` | Frontend `User` |
|-----------------------|-----------------|
| `id` | `id` |
| `email` | `email` |
| `display_name` | `name` |
| `role` | `platformRole` |
| `team_ids[]` | `teamMemberships[].teamId` (teamName filled from teams cache) |

---

## Tools — `frontend/src/api/tools.ts`

> **Detailed spec:** [apis/tools/](./tools/README.md) — endpoints, payloads, adapter mapping, JSON examples.

| Function | Method | Path | Status |
|----------|--------|------|--------|
| `fetchTools` | GET | `/tools` | wired |
| `createTool` | POST | `/tools` | wired |
| `updateTool` | PATCH | `/tools/{toolId}` | wired |
| `deleteTool` | DELETE | `/tools/{toolId}` | wired |
| `syncTool` | POST | `/tools/{toolId}/sync` | wired |

### Types

**`AiTool`** (list/detail response)

| Field | Type | OpenAPI `Tool` | Delta |
|-------|------|---------------|-------|
| `id` | string | `id` | |
| `name` | string | `name` | |
| `provider` | `ToolProvider` | `vendor` | rename; FE enum includes `mabl`, `windsurf` |
| `description` | string | — | **FE only** |
| `pricing` | `ToolPricing` | split across pricing fields | see below |
| `status` | `active` \| `inactive` \| `error` | `active` boolean | FE adds `error` state |
| `apiKeyMasked` | string | — | **FE only** (from credentials) |
| `lastSyncAt` | string \| null | — | sync metadata |
| `tokenCount` | number | — | usage aggregate |
| `costTotal` | number | — | usage aggregate |
| `createdAt` | string | `created_at` | |

**`ToolPricing`** (frontend) vs OpenAPI pricing

| Frontend `ToolPricing` | OpenAPI |
|------------------------|---------|
| `model`: `per_token` \| `per_seat` \| `flat_fee` \| `hybrid` | `pricing_model`: `flat_token` \| `package_with_overage` \| `custom` |
| `inputCostPer1K`, `outputCostPer1K` | `token_price`, `pricing_config` |
| `costPerSeat`, `seatCount` | `pricing_config` |
| `flatMonthlyCost`, `planName`, `includedTokens`, `overageRate` | `package_allowance`, `overage_price`, `pricing_config` |

**`CreateToolRequest` / `UpdateToolRequest`**

| Field | Type | OpenAPI `ToolCreateRequest` |
|-------|------|----------------------------|
| `name` | string | `name` |
| `provider` | `ToolProvider` | `vendor` |
| `apiKey` | string | — | stored via credentials API, not tool create |
| `description` | string | — | **FE only** |
| `pricing` | `ToolPricing` | `pricing_model`, `token_price`, … |

**`syncTool(id)`** — no request body. Response: updated `AiTool`. OpenAPI path TBD.

---

## Teams — `frontend/src/api/teams.ts` ✅ Complete

**Status:** Completed **2026-06-16** — backend CRUD, form fields (budgets, tool access), and Admin → Teams UI wired. See [teams-backend/implementation-status.md](../../changes/teams-backend/implementation-status.md).

| Function | Method | Path | OpenAPI schema | Status |
|----------|--------|------|----------------|--------|
| `fetchTeams` | GET | `/teams` | → `TeamListResponse` | wired |
| `createTeam` | POST | `/teams` | `TeamCreateRequest` → `Team` | wired |
| `updateTeam` | PATCH | `/teams/{teamId}` | `TeamUpdateRequest` → `Team` | wired |
| `deleteTeam` | DELETE | `/teams/{teamId}` | → 204 | wired |

### `Team` response

| Field | Type | OpenAPI `Team` | Delta |
|-------|------|---------------|-------|
| `id` | string | `id` | |
| `name` | string | `name` | |
| `description` | string | `description` | |
| `memberCount` | number | `member_count` | rename |
| `tokenBudget` | number \| null | `token_budget` | |
| `costBudget` | number \| null | `cost_budget` | |
| `tokenUsedThisMonth` | number | — | **FE only** — usage summary (computed later) |
| `costUsedThisMonth` | number | — | **FE only** |
| `status` | `active` \| `inactive` | `active` boolean | map `active` ↔ `status` |
| `toolIds` | string[] | `tool_ids` | stored as JSONB until tools FK slice |
| `createdAt` | string | `created_at` | |

### `CreateTeamRequest` / `UpdateTeamRequest`

| Field | Type | OpenAPI `TeamCreateRequest` | Delta |
|-------|------|----------------------------|-------|
| `name` | string | `name` | |
| `description` | string | `description` | |
| `tokenBudget` | number \| null | `token_budget` | |
| `costBudget` | number \| null | `cost_budget` | |
| `toolIds` | string[] | `tool_ids` | |

---

## Members — `frontend/src/api/members.ts`

| Function | Method | Path | Status |
|----------|--------|------|--------|
| `fetchMembers(view?)` | GET | `/members?view=all\|invited` | **wired** |
| `fetchMembersByTeam` | GET | `/teams/{teamId}/members` | **wired** |
| `inviteMember` | POST | `/users` | **wired** |
| `updateMember` | PATCH | `/users/{userId}` | **wired** |
| `removeMember` | DELETE | `/users/{userId}` | **wired** (deactivates) |

**Views:** `all` (default) — invited platform users plus tool token emails from all teams; `invited` — manually created platform users only (`GET /users` equivalent). Per-team filter uses `/teams/{teamId}/members`.

### `Member` response

| Field | Type | Planned OpenAPI / `TeamMember` | Delta |
|-------|------|-------------------------------|-------|
| `id` | string | `id` / `user_id` | |
| `name` | string | `display_name` | |
| `email` | string | `email` | |
| `platformRole` | `Role` | `role` | |
| `teams` | `{ id, name }[]` | multiple team memberships | org-level FE model |
| `status` | `active` \| `inactive` | `active` boolean | |
| `lastActiveAt` | string \| null | — | **FE only** |
| `createdAt` | string | `created_at` | |

### `InviteMemberRequest`

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | → `display_name` |
| `email` | string | unique per org |
| `platformRole` | `Role` | → `role` |
| `teamIds` | string[] | may require N× `POST /teams/{id}/members` |

### `UpdateMemberRequest` (all optional)

| Field | Type |
|-------|------|
| `name` | string |
| `platformRole` | `Role` |
| `teamIds` | string[] |
| `status` | `active` \| `inactive` |

### `fetchMembersByTeam(teamId)` response

OpenAPI `TeamMember[]` in `{ data, meta }`:

| OpenAPI `TeamMember` | Frontend row |
|----------------------|--------------|
| `user_id` | `id` (synthetic `tool:…` when `source=tool`) |
| `email` | `email` |
| `display_name` | `name` |
| `joined_at` | `createdAt` |
| `source` | `source` (`platform` \| `tool`) |
| `tool_id` / `tool_name` | `toolId` / `toolName` |

Team filter merges **platform members** (team memberships) with **tool token emails** from tools assigned to the team (`team.tool_ids`).

---

## Credentials — `frontend/src/api/credentials.ts`

| Function | Method | Path | OpenAPI schema | Status |
|----------|--------|------|----------------|--------|
| `fetchCredentials` | GET | `/credentials` | → `{ data: Credential[] }` | **wired** |
| `createCredential` | POST | `/credentials` | `CredentialCreateRequest` → `Credential` | **wired** |
| `updateCredential` | PATCH | `/credentials/{id}` | partial body → `Credential` | **wired** |
| `revokeCredential` | DELETE | `/credentials/{credentialId}` | → 204 | **wired** |

Each credential maps **1:1 to an AI tool** (`admin.tools`): the encrypted API key, masked secret, expiry, environment, and active status live on the tool record. Team scope is derived from team `tool_ids` assignments.

### `Credential` response

| Field | Type | OpenAPI `Credential` | Delta |
|-------|------|---------------------|-------|
| `id` | string | `id` | |
| `label` | string | — | **FE only** |
| `description` | string | — | **FE only** |
| `toolId` | string | `tool_id` | |
| `toolName` | string | — | denormalized |
| `teamId` | string | `team_id` | |
| `teamName` | string | — | denormalized |
| `environment` | `production` \| `sandbox` | `environment` | |
| `keyMasked` | string | `masked_secret` | rename |
| `status` | `active` \| `inactive` | — | derived from delete/revoke |
| `rotationReminderDays` | number \| null | — | **FE only** |
| `expiresAt` | string \| null | `expires_at` | |
| `lastUsedAt` | string \| null | — | **FE only** |
| `createdAt` | string | `created_at` | |
| `createdByName` | string | — | **FE only** |

### `CreateCredentialRequest`

| Field | Type | OpenAPI `CredentialCreateRequest` |
|-------|------|-----------------------------------|
| `label` | string | — | **FE only** |
| `description` | string | — | **FE only** |
| `toolId` | string | `tool_id` |
| `teamId` | string | `team_id` |
| `environment` | `CredentialEnvironment` | `environment` |
| `apiKey` | string | `secret_value` |
| `rotationReminderDays` | number \| null | — | **FE only** |
| `expiresAt` | string \| null | `expires_at` |

**`CreateCredentialResponse`**

| Field | Type | OpenAPI |
|-------|------|---------|
| `credential` | `Credential` | `Credential` (no plain secret) |
| `plainKey` | string | one-time `secret_value` in create response |

### `UpdateCredentialRequest`

All fields optional except `apiKey` (omitted). Maps to planned `PATCH /credentials/{id}` for `label`, `description`, `team_id`, `tool_id`, `environment`, `expires_at`, `rotation_reminder_days`.

---

## Alerts (thresholds) — `frontend/src/api/alerts.ts`

| Function | Method | Path | OpenAPI schema | Status |
|----------|--------|------|----------------|--------|
| `fetchAlertRules` | GET | `/thresholds` | → `{ data: Threshold[] }` | **wired** |
| `createAlertRule` | POST | `/thresholds` | `ThresholdCreateRequest` → `Threshold` | **wired** |
| `updateAlertRule` | PATCH | `/thresholds/{thresholdId}` | partial → `Threshold` | **wired** |
| `deleteAlertRule` | DELETE | `/thresholds/{thresholdId}` | → 204 | **wired** |
| `fetchAlertHistory` | GET | `/thresholds/events` | → `AlertEvent[]` | **wired** |
| `acknowledgeAlert` | POST | `/thresholds/events/{id}/acknowledge` | → `AlertEvent` | **wired** |

### Enum mapping

| Frontend | OpenAPI | Notes |
|----------|---------|-------|
| `thresholdType`: `token_count` | `token_count` | match |
| `thresholdType`: `cost_usd` | `cost_amount` | rename |
| `thresholdType`: `budget_percent` | `package_utilization_pct` | rename |
| `scope`: `organization` | — | **FE only** — map to org-wide threshold without team_id |
| `scope`: `team` | `team` | |
| `scope`: `user` | `user` | |
| — | `tool` | OpenAPI scope not used in FE alerts UI |
| `severity`: `info` | — | **FE only** |
| `severity`: `warning`, `critical` | same | |
| `channel`: `email` | `notify_email: true` | |
| `channel`: `webhook` | webhook URL field *(planned)* | |
| `channel`: `both` | email + webhook | |

### `AlertRule` response

| Field | Type | OpenAPI `Threshold` | Delta |
|-------|------|--------------------|-------|
| `id` | string | `id` | |
| `name` | string | — | **FE only** |
| `severity` | `AlertSeverity` | `severity` | FE adds `info` |
| `thresholdType` | `ThresholdType` | `threshold_type` | see enum map |
| `thresholdValue` | number | `limit_value` | |
| `scope` | `ThresholdScope` | `scope` | FE adds `organization` |
| `teamId` | string \| null | `team_id` | |
| `teamName` | string \| null | — | denormalized |
| `channel` | `AlertChannel` | `notify_email`, webhook | composite |
| `webhookUrl` | string \| null | — | **planned** |
| `emailRecipients` | string[] | — | **FE only** |
| `status` | `active` \| `inactive` | `active` | map |
| `triggerCount` | number | — | **FE only** |
| `lastTriggeredAt` | string \| null | — | **FE only** |
| `createdAt` | string | — | **FE only** |

### `CreateAlertRuleRequest`

Same fields as `AlertRule` except id, status, triggerCount, lastTriggeredAt, teamName.

### `AlertEvent` response *(planned OpenAPI)*

| Field | Type |
|-------|------|
| `id` | string |
| `ruleId` | string |
| `ruleName` | string |
| `severity` | `AlertSeverity` |
| `message` | string |
| `teamName` | string \| null |
| `triggeredAt` | string (ISO) |
| `acknowledgedAt` | string \| null |
| `acknowledgedBy` | string \| null |

**`acknowledgeAlert(id)`** — no request body. Returns updated `AlertEvent`.

---

## Uploads — `frontend/src/api/uploads.ts`

| Function | Method | Path | OpenAPI schema | Status |
|----------|--------|------|----------------|--------|
| `fetchUploads` | GET | `/uploads` | → `{ data: Upload[] }` | **wired** |
| `uploadFile` | POST | `/uploads` | multipart → `UploadCreateResponse` | **wired** |
| `fetchUploadPreview` | GET | `/uploads/{uploadId}/preview` | → `UploadPreview` | **wired** |
| `submitUpload` | POST | `/uploads/{uploadId}/commit` | optional body → 202 | **wired** |
| `deleteUpload` | DELETE | `/uploads/{uploadId}` | → 204 | **wired** |

CSV/JSON rows are stored in `ingestion.parsed_rows` with **`raw_payload`** (original columns) and **`mapped_payload`** (tool/user/token mapping). Preview returns both as `raw_data` and `mapped_data` per row.

### `uploadFile(file, teamId)` request

| Part | Type | OpenAPI multipart |
|------|------|-------------------|
| `file` | `File` | `file` (binary) |
| — | — | `team_id` (required in OpenAPI) |
| `teamId` arg | string \| null | `team_id` |

### `UploadRecord` response

| Field | Type | OpenAPI `Upload` | Delta |
|-------|------|-----------------|-------|
| `id` | string | `id` | |
| `fileName` | string | `filename` | rename |
| `format` | `csv` \| `json` | inferred from file | |
| `status` | `pending` \| `processing` \| `completed` \| `error` | `UploadStatus` | FE simplifies enum |
| `rowCount` | number \| null | `matched_rows` + `unmatched_rows` | |
| `errorCount` | number \| null | `unmatched_rows` | |
| `errorMessage` | string \| null | `error_message` | |
| `uploadedByName` | string | — | **FE only** |
| `teamId` | string \| null | `team_id` | |
| `teamName` | string \| null | — | denormalized |
| `fileSizeKb` | number | `size_bytes` | unit conversion |
| `createdAt` | string | `created_at` | |
| `processedAt` | string \| null | `completed_at` | rename |

### `UploadPreview` response

| Field | Type | OpenAPI `UploadPreview` | Delta |
|-------|------|------------------------|-------|
| `uploadId` | string | `upload_id` | |
| `fileName` | string | — | **FE only** |
| `totalRows` | number | `total_rows` | |
| `validRows` | number | `matched_rows` | rename |
| `errorRows` | number | `unmatched_rows` | rename |
| `rows` | `UploadPreviewRow[]` | `sample_rows` | FE returns all preview rows |

**`UploadPreviewRow`**

| Field | Type | OpenAPI `ParsedUsageRow` |
|-------|------|-------------------------|
| `rowIndex` | number | `row_number` |
| `userId` | string | `matched_user_id` |
| `userName` | string | — | from email/local |
| `model` | string | — | **FE only** |
| `tokens` | number | `input_tokens` + `output_tokens` |
| `cost` | number | — | **FE only** |
| `timestamp` | string | `occurred_at` | |
| `status` | `valid` \| `error` | derived from match |
| `errorReason` | string \| null | — | **FE only** |

### `SubmitUploadRequest`

| Field | Type | OpenAPI commit body |
|-------|------|---------------------|
| `teamId` | string \| null | confirm `team_id` override |

Headers: `Idempotency-Key` (OpenAPI required for commit).

---

## Dashboard — `frontend/src/api/dashboard.ts`

| Function | Query params | Response type | OpenAPI endpoint |
|----------|--------------|---------------|------------------|
| `fetchDashboardStats(from, to)` | `from`, `to` | `DashboardStats` | composite — see below |
| `fetchTokenTimeseries(from, to)` | `from`, `to` | `TokenDataPoint[]` | `GET /dashboard/trends` |
| `fetchTeamCost(from, to)` | `from`, `to` | `TeamCostDataPoint[]` | `GET /dashboard/usage-by-team` |
| `fetchTopUsers(from, to)` | `from`, `to` | `TopUser[]` | `GET /dashboard/top-consumers?entity=users` |
| `fetchRecentAlerts()` | — | `RecentAlert[]` | `GET /dashboard/alerts` |

### `DashboardStats`

| Field | Type | OpenAPI source |
|-------|------|----------------|
| `totalTokens` | number | `TokenUsageWidget.total_tokens` |
| `totalCost` | number | `CostOverviewWidget.actual_spend` |
| `activeTools` | number | count of `UsageByToolItem[]` |
| `activeTeams` | number | count of usage-by-team rows |
| `tokensDelta` | number (%) | derived / trends comparison |
| `costDelta` | number (%) | derived |
| `toolsDelta` | number (%) | derived |
| `teamsDelta` | number (%) | derived |

### `TokenDataPoint`

| Field | Type | OpenAPI `TrendPoint` |
|-------|------|---------------------|
| `date` | string (display) | `period_start` formatted |
| `tokens` | number | `total_tokens` |
| `cost` | number | `estimated_cost` |

### `TeamCostDataPoint`

| Field | Type | OpenAPI usage-by-team row |
|-------|------|--------------------------|
| `team` | string | `team_name` |
| `cost` | number | `estimated_cost` |

### `TopUser`

| Field | Type | OpenAPI `TopConsumerItem` |
|-------|------|--------------------------|
| `id` | string | `entity_id` |
| `name` | string | `entity_name` |
| `team` | string | — | join from team data |
| `tokens` | number | `total_tokens` |
| `cost` | number | `estimated_cost` |
| `percentOfTotal` | number | derived |

### `RecentAlert`

| Field | Type | OpenAPI `ActiveAlertSummary` |
|-------|------|------------------------------|
| `id` | string | `alert_id` |
| `title` | string | derived from threshold type |
| `severity` | `critical` \| `warning` \| `info` | `severity` |
| `triggeredAt` | string | `triggered_at` |
| `team` | string | `team_name` |

---

## Usage / insights — `frontend/src/api/usage.ts`

| Function | Args | Response | OpenAPI |
|----------|------|----------|---------|
| `fetchUsageSummary(from, to)` | ISO dates | `UsageSummary` | composite tokens + cost |
| `fetchTeamUsage(from, to)` | ISO dates | `TeamUsageRow[]` | `GET /dashboard/usage-by-team` |
| `fetchDailyUsage(from, to)` | ISO dates | `DailyUsagePoint[]` | `GET /dashboard/trends` |
| `fetchUserUsage(teamId, from, to)` | team + dates | `UserUsageRow[]` | top-consumers + filter |
| `fetchTeamDrilldown(teamId, from, to, toolId)` | + optional tool | `UserUsageRow[]` | same + `tool_id` query |
| `fetchToolOptions()` | — | `{ id, name }[]` | `GET /tools?active=true` |
| `fetchDailyBreakdown(date, teamId, toolId)` | date + filters | `DailyBreakdownTeam[]` | **gap** — planned |

### `UsageSummary`

| Field | Type |
|-------|------|
| `totalTokens` | number |
| `totalCost` | number |
| `avgCostPerToken` | number |
| `periodDays` | number |

### `TeamUsageRow`

| Field | Type | OpenAPI row (partial) |
|-------|------|----------------------|
| `teamId` | string | `team_id` |
| `teamName` | string | `team_name` |
| `tokens` | number | `total_tokens` |
| `cost` | number | `estimated_cost` |
| `percentOfTotal` | number | derived |
| `memberCount` | number | — | **FE only** |
| `tokenBudget` | number \| null | — | **FE only** |
| `costBudget` | number \| null | — | **FE only** |
| `budgetUtilization` | number \| null | — | **FE only** |
| `trend` | number (%) | — | **FE only** |

### `DailyUsagePoint`

| Field | Type |
|-------|------|
| `date` | string |
| `tokens` | number |
| `cost` | number |

### `UserUsageRow`

| Field | Type |
|-------|------|
| `userId` | string |
| `userName` | string |
| `userEmail` | string |
| `teamId` | string |
| `teamName` | string |
| `tokens` | number |
| `cost` | number |
| `percentOfTeamTotal` | number |
| `requestCount` | number |
| `avgTokensPerRequest` | number |

### `DailyBreakdownTeam` *(planned OpenAPI)*

| Field | Type |
|-------|------|
| `teamId` | string |
| `teamName` | string |
| `tokens` | number |
| `cost` | number |
| `users` | `{ userId, userName, tokens, cost }[]` |

---

## Reports — `frontend/src/api/reports.ts`

| Function | Method | Path | Status |
|----------|--------|------|--------|
| `fetchReports` | GET | `/reports` *(planned)* | mock |
| `createReport` | POST | `/reports/generate` | mock |
| `deleteReport` | DELETE | `/reports/{id}` *(planned)* | mock |
| `downloadReport` | GET | `/reports/jobs/{jobId}/download` | mock |
| `fetchSubscriptions` | GET | `/reports/{id}/subscriptions` *(planned)* | mock |
| `createSubscription` | POST | `/reports/{id}/subscriptions` *(planned)* | mock |
| `deleteSubscription` | DELETE | `/reports/{id}/subscriptions/{subId}` *(planned)* | mock |

### `Report` response

| Field | Type | OpenAPI `ReportJob` / planned | Delta |
|-------|------|------------------------------|-------|
| `id` | string | `job_id` / report id | |
| `name` | string | — | **FE only** |
| `type` | `ReportType` | `report_type` | different enum values |
| `format` | `pdf` \| `csv` \| `xlsx` | `format`: `json` \| `csv` \| `pdf` | FE adds `xlsx` |
| `status` | `pending` \| `processing` \| `completed` \| `error` | `JobStatus` | map `failed` → `error` |
| `schedule` | `once` \| `daily` \| `weekly` \| `monthly` | — | **FE only** |
| `periodFrom` | string | `from` | |
| `periodTo` | string | `to` | |
| `teamIds` | string[] | `team_id` (single) | FE supports multi-team |
| `generatedAt` | string \| null | `completed_at` | |
| `fileSizeKb` | number \| null | — | **FE only** |
| `createdByName` | string | — | **FE only** |
| `createdAt` | string | `created_at` | |
| `errorMessage` | string \| null | `error_message` | |
| `subscriptionCount` | number | — | **FE only** |

### Report type enum mapping

| Frontend `ReportType` | OpenAPI `ReportType` |
|-----------------------|---------------------|
| `usage_summary` | `tool_usage_summary` |
| `cost_breakdown` | `cost` |
| `team_comparison` | `team_usage` |
| `user_activity` | `user_usage` |
| `budget_variance` | — | **FE only** |

### `CreateReportRequest`

| Field | Type | OpenAPI `ReportGenerateRequest` |
|-------|------|-------------------------------|
| `name` | string | — | **FE only** |
| `type` | `ReportType` | `report_type` |
| `format` | `ReportFormat` | `format` |
| `schedule` | `ReportSchedule` | — | **FE only** |
| `periodFrom` | string | `from` |
| `periodTo` | string | `to` |
| `teamIds` | string[] | `team_id` (first or repeated calls) |

### `ReportSubscription` / `CreateSubscriptionRequest` *(planned)*

**`ReportSubscription`**

| Field | Type |
|-------|------|
| `id` | string |
| `reportId` | string |
| `channel` | `email` \| `in_app` \| `both` |
| `cadence` | `daily` \| `weekly` \| `monthly` |
| `emailRecipients` | string[] |
| `createdAt` | string |
| `createdByName` | string |

**`CreateSubscriptionRequest`**

| Field | Type |
|-------|------|
| `channel` | `SubscriptionChannel` |
| `cadence` | `SubscriptionCadence` |
| `emailRecipients` | string[] |

**`downloadReport(id)`** — no body; triggers file download (OpenAPI 302 or blob).

---

## Audit log — `frontend/src/api/auditLog.ts`

| Function | Method | Path | Status |
|----------|--------|------|--------|
| `fetchAuditLog(filters)` | GET | `/audit-logs` | mock |

### Query (`AuditLogFilters` → OpenAPI params)

| Frontend filter | Type | OpenAPI query param |
|-----------------|------|---------------------|
| `search` | string | `q` or `search` *(client-side in mock)* |
| `category` | `AuditCategory` \| `""` | `resource_type` / category |
| `from` | string (ISO date) | `from` |
| `to` | string (ISO date) | `to` |

### `AuditLogEntry` response

| Field | Type | OpenAPI `AuditLogEntry` | Delta |
|-------|------|------------------------|-------|
| `id` | string | `id` | |
| `action` | `AuditAction` | `action` | FE uses dotted names |
| `category` | `AuditCategory` | derived from `resource_type` | |
| `actorName` | string | — | from user lookup |
| `actorEmail` | string | `actor_email` | |
| `actorRole` | string | — | **FE only** |
| `targetType` | string \| null | `resource_type` | |
| `targetName` | string \| null | — | **FE only** |
| `description` | string | — | **FE only** |
| `ipAddress` | string | `source_ip` | rename |
| `createdAt` | string | `created_at` | |

OpenAPI also includes: `actor_id`, `resource_id`, `outcome`, `correlation_id` — not surfaced in FE UI today.

---

## Notifications — `frontend/src/api/notifications.ts`

Stub module. Target shapes from OpenAPI:

**`GET /notifications`** → `NotificationListResponse`

| Field | Type |
|-------|------|
| `data` | `Notification[]` |
| `unread_count` | number |
| `meta` | `PaginationMeta` |

**`Notification`**

| Field | Type |
|-------|------|
| `id` | string |
| `alert_type` | string |
| `severity` | `AlertSeverity` |
| `tool_name` | string? |
| `team_name` | string? |
| `threshold_value` | number |
| `current_value` | number |
| `read` | boolean |
| `deep_link` | string |
| `created_at` | string |

**`GET /notifications/unread-count`** → `{ unread_count: number }`

**`POST /notifications/{notificationId}/read`** → 204

---

## Health probe

**`GET /health`** → `HealthResponse`

| Field | Type |
|-------|------|
| `status` | `ok` \| `degraded` |
| `database` | `ok` \| `error` |

Used in `client.test.ts` only.

---

## Collectors (token usage pull) — `backend/app/collector/` *(implemented)*

In-process scheduler in the API container. Frontend will configure `pull_interval_minutes` via these endpoints (not yet wired in `frontend/src/api/`).

| Function (planned FE) | Method | Path | Request | Response |
|-----------------------|--------|------|---------|----------|
| `fetchCollectors` | GET | `/collectors` | — | `{ data: CollectorResponse[] }` |
| `createCollector` | POST | `/collectors` | `CollectorCreateRequest` | `CollectorResponse` |
| `updateCollector` | PATCH | `/collectors/{id}` | `CollectorUpdateRequest` | `CollectorResponse` |
| `deleteCollector` | DELETE | `/collectors/{id}` | — | 204 |
| `runCollector` | POST | `/collectors/{id}/run` | — | `CollectorRunResponse` |
| `fetchCollectorRuns` | GET | `/collectors/{id}/runs` | — | `{ data: CollectorRunResponse[] }` |
| `fetchUsageEvents` | GET | `/usage/events?collector_id=` | query | `{ data: UsageEventResponse[] }` |
| `fetchUsageSummary` | GET | `/usage/summary?collector_id=` | query | `UsageSummaryResponse` |

See [token-collector-mvp](../../changes/token-collector-mvp/specs/collector-api/spec.md) for full payload shapes.

---

## OpenAPI paths not used by frontend

| Path | `operationId` | Notes |
|------|---------------|-------|
| `GET /dashboard/tokens` | `getDashboardTokens` | Aggregated into `fetchDashboardStats` |
| `GET /dashboard/cost` | `getDashboardCost` | Aggregated into stats / usage summary |
| `GET /dashboard/usage-by-tool` | `getDashboardUsageByTool` | Not in current Insights UI |
| `GET /dashboard/my-usage` | `getDashboardMyUsage` | Routes redirect to Insights |
| `POST /credentials/{credentialId}/rotate` | `rotateCredential` | No rotate UI action |
| `POST /uploads/{uploadId}/reprocess` | `reprocessUpload` | Not in Uploads UI |
| `GET /reports/jobs/{jobId}` | `getReportJob` | Mock uses inline `Report.status` |
| `GET /audit-logs/export` | `exportAuditLogs` | Client-side CSV export only |
| `POST /teams/{teamId}/members` | `addTeamMember` | Members page uses org-level API |
| `DELETE /teams/{teamId}/members/{userId}` | `removeTeamMember` | Members page uses org-level API |

---

## Page → API index

| Route | API modules / functions |
|-------|-------------------------|
| `/login` | `auth.login` |
| `/insights` | `dashboard.*`, `usage.*`, `reports.*`, `teams.fetchTeams` |
| `/alerts`, `/alerts/history` | `alerts.*`, `teams.fetchTeams` |
| `/uploads` | `uploads.fetchUploads`, `uploads.uploadFile`, `uploads.deleteUpload`, `teams.fetchTeams` |
| `/uploads/:id/preview` | `uploads.fetchUploadPreview`, `uploads.submitUpload`, `uploads.deleteUpload` |
| `/admin/tools` | `tools.*` |
| `/admin/teams` | `teams.*` ✅, `usage.fetchToolOptions` ✅ |
| `/admin/members` | `members.*`, `teams.fetchTeams` |
| `/admin/credentials` | `credentials.*`, `teams.fetchTeams`, `usage.fetchToolOptions` |
| `/admin/audit-log` | `auditLog.fetchAuditLog` |

---

## Recommended OpenAPI additions

Priority gaps (payloads documented above as *planned*):

1. **`/users` CRUD** — org-wide member admin (`Member`, `InviteMemberRequest`)
2. **Threshold events** — `AlertEvent` list + acknowledge
3. **Report catalog + subscriptions** — `Report`, `ReportSubscription` persistence
4. **`PATCH /credentials/{credentialId}`** — `UpdateCredentialRequest`
5. **`POST /tools/{toolId}/sync`** — returns updated tool/sync metadata
6. **`GET /dashboard/daily-breakdown`** — `DailyBreakdownTeam[]`

Extend [schemas.yaml](./components/schemas.yaml) with frontend-aligned schemas or document adapter mappings when integrating.

---

## Related documents

- [openapi.yaml](./openapi.yaml) — canonical REST contract
- [schemas.yaml](./components/schemas.yaml) — request/response component schemas
- [README.md](./README.md) — API conventions and auth matrix
- [frontend-standards.md](../frontend-standards.md) — `src/api/` access rules
- [user-management-backend](../../changes/user-management-backend/specs/platform-user-admin/spec.md) — planned `/users` API
- [notifications-backend](../../changes/notifications-backend/specs/threshold-management/spec.md) — threshold backend
- [reporting-backend](../../changes/reporting-backend/specs/report-delivery-api/spec.md) — report generation flow
