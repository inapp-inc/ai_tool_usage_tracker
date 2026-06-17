# Proposal: Credentials — Connect Tool Redesign

**Status:** 📋 Proposed

## Why

The Credentials page is where live API connections are established and validated. Its current state mixes up the catalogue concept (choosing a tool) with the credential workflow, and it carries UI elements that no longer belong there:

- **"Add Credential"** button label suggests storing a key, not connecting to a live service — rename to **"Connect Tool"** to reflect that an actual validation round-trip happens.
- **Production / Sandbox environment selector** adds friction without value: the environment distinction is managed at the tool or team level, not at the credential level.
- **Save without validation** is unsafe: a bad API key should be rejected at entry time before any collection jobs run against it.

This change makes the Credentials section the single place where API tokens are validated and saved, providing immediate feedback on whether a credential is accepted by the provider.

## What Changes (this slice)

### 1. Button rename: "Connect Tool" (was "Add Credential")

The primary CTA on the Credentials page changes to "Connect Tool" to make the live-validation intent clear.

### 2. Remove environment selector (Production / Sandbox)

The `environment` field is removed from the credential create and edit forms. The field is dropped from `CredentialCreateRequest` and `CredentialUpdateRequest`. Existing records retain their stored value but the field is no longer displayed.

### 3. Token validation on save

When a user submits the Connect Tool form, the backend:
1. Calls the provider adapter's `validate_api_key()` before persisting.
2. Returns a `422` with a human-readable error message if validation fails.
3. Only saves the credential (encrypted) and returns `201` on successful validation.

The frontend shows the validation error inline in the form and does not close the slide-over on failure.

### 4. Validation endpoint

New lightweight endpoint for UI-side validation (optional / pre-save check):

```
POST /api/v1/credentials/validate
Body: { provider: string, api_token: string }
Response 200: { valid: true }
Response 422: { valid: false, message: string }
```

This keeps validation fast and user-facing without requiring an existing credential record.

## Out of Scope

- Full credential lifecycle management (rotation reminders, expiry — existing FR-ADM-003 scope)
- Credential-level environment tagging (can be re-added later if business need arises)

## Dependencies

- Existing `credentials` API and `CredentialCreateRequest`
- Provider adapter `validate_api_key()` (already implemented per-provider)
- `tool-catalogue-redesign` — tools must exist before credentials can reference them
