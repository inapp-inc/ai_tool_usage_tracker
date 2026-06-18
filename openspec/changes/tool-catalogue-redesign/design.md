# Design: Tool Catalogue Redesign

## UI Changes

### ToolsPage

| Element | Before | After |
|---------|--------|-------|
| Primary button | "Connect Tool" | "Add Tool" |
| Slide-over title (create) | "Add an AI provider API key" | "Add Tool" |
| Slide-over title (edit) | "Update tool configuration" | "Edit Tool" |
| API Key field | Present in tool form | **Removed** — credentials are managed in the Credentials section |
| Pricing panel | Per-tool token rates, seat cost, package allowance | Removed from form and list |
| Tools list columns | Tool, Status, Tokens used, Members, Pricing, Total cost, Last synced + sync/members actions | Tool, Provider, Status + edit/delete actions only |
| API Endpoint URL field | Not present | Text field: full API URL used by the application (required for `custom` provider, optional otherwise) |
| Provider dropdown | Hardcoded enum | Loaded from `GET /api/v1/settings/providers` (with fallback to built-in list during transition) |

### Tool form fields after redesign

| Field | Required | Notes |
|-------|----------|-------|
| Tool name | Yes | Unique within org |
| Provider | Yes | Lookup-driven select |
| Description | No | Free text |
| API Endpoint URL | Conditional | Full URL the application calls (e.g. `https://api.openai.com/v1/chat/completions`). Required when provider is `custom`; optional otherwise |

### Tools list columns after redesign

| Column | Notes |
|--------|-------|
| Tool | Tool display name |
| Provider | Provider display name from Settings lookup (by `provider_id`) |
| Status | active / inactive / error |
| Actions | Edit, Delete only — no sync or members actions on this page |

API keys are **not** collected here. Use the **Credentials** section to connect and validate API keys per tool.
Pricing details (token rates, seat count, package allowance, overage) are configured on Team Tool assignments in the Teams section.

## Backend Changes

### Migration

New column on `admin.tools`:

```sql
api_endpoint VARCHAR(512) NULL
```

### API schema deltas

`ToolCreateRequest` and `ToolUpdateRequest` gain:
```yaml
api_endpoint:
  type: string
  maxLength: 512
  nullable: true
  description: "Base API URL used by the collector adapter for this tool."
```

`ToolResponse` gains:
```yaml
api_endpoint:
  type: string
  nullable: true
```

### Adapter behaviour

Adapters resolve their base URL from:
1. `tool.api_endpoint` (if non-empty)
2. Hardcoded default (existing behaviour, unchanged for built-in providers)

### Validation

- `api_endpoint`, when provided, must start with `https://`.
- When `provider` is `custom`, `api_endpoint` is required.
- `api_key` is **not** accepted on `ToolCreateRequest` / `ToolUpdateRequest` — keys are managed exclusively through the Credentials API.

## Frontend Changes

- `ToolsPage.tsx`: update labels, remove pricing form fields, add `api_endpoint` field, simplify tools list to Tool / Provider / Status with edit and delete only.
- `frontend/src/api/adapters/tools.ts`: add `apiEndpoint` to `AiTool` and write-body types.
- Provider dropdown: replace hardcoded array with query to `/api/v1/settings/providers`; fallback to built-in enum when query fails.

## Data Migration

Existing tool records get `api_endpoint = NULL`. No behavioural change for built-in providers.
