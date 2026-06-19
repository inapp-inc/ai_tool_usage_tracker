# Design: Credentials — Connect Tool Redesign

## UI Changes

### CredentialsPage

| Element | Before | After |
|---------|--------|-------|
| Primary button | "Add Credential" | "Connect Tool" |
| Slide-over title (create) | "Add Credential" | "Connect Tool" |
| Environment field | Present (Production / Sandbox radio) | Removed |
| Save behaviour | Saves immediately | Validates token first; error shown inline on failure; credential saved only on success |
| Validation feedback | None | Inline error below API key field: "Invalid API key — provider rejected the token." |

### Form fields after redesign

| Field | Required | Notes |
|-------|----------|-------|
| Tool | Yes | Select from active **catalogue** tools |
| Team | Yes | Team that owns this connection; usage is attributed to this team |
| Label / Name | No | Free text |
| API Key | Yes | Masked input |
| Description | No | Free text |

Environment selector removed entirely.

## Admin workflow (Teams → Credentials → Data)

1. **Teams** — create a team and assign one or more catalogue tools (with optional pricing).
2. **Credentials** — connect each tool: pick catalogue tool + team + API key.
3. **Auto-sync** — on successful connect, the backend syncs **all connected credentials** for that team (30-day usage backfill + members).
4. **Teams list** — shows tokens, cost, and last synced from ingested usage for assigned tools that have credentials.

Manual refresh: **Teams** page refresh button calls `POST /teams/{id}/sync` (same logic as auto-sync).

## Backend Changes

### `POST /api/v1/credentials` — validation before persist

```
1. Resolve provider from tool_id
2. Call adapter.validate_api_key(api_token, pricing_config=tool.pricing_config)
3a. On ProviderValidationError → return 422 { detail: "<message>" }
3b. On success → encrypt and persist → return 201
```

The existing `POST /api/v1/credentials` endpoint gains this pre-save validation step.

### New: `POST /api/v1/credentials/validate`

```yaml
path: /credentials/validate
method: POST
requestBody:
  tool_id: string (uuid)
  api_token: string
responses:
  200: { valid: true, provider: string }
  422: { valid: false, message: string }
auth: Bearer JWT (super_admin or team_admin)
```

Performs validation only — does not persist anything.

### Schema changes

`CredentialCreateRequest`:
- Remove `environment` field
- Keep all other fields

`CredentialUpdateRequest`:
- Remove `environment` field

`CredentialResponse`:
- Remove `environment` from display fields (retain in DB for backwards compatibility; not returned by API)

## Frontend Changes

- `CredentialsPage.tsx`:
  - Rename button and slide-over title
  - Remove environment radio/select
  - On form submit: call `POST /credentials` (validation + save in one step); catch 422 and display `detail` under the API key field
  - Optional: add "Verify" button that calls `POST /credentials/validate` before full submit

- `frontend/src/api/credentials.ts`:
  - Add `validateCredential({ toolId, apiToken })` function
  - Remove `environment` from `CredentialCreateBody` type
