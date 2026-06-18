# Proposal: Settings — Provider Lookup Keys

**Status:** 📋 Proposed

## Why

Provider names (OpenAI, Anthropic, Figma, Cursor, etc.) are currently hardcoded in several places across frontend and backend. Adding a new provider requires a code change, a build, and a deploy. Administrators have no way to define custom or internal AI providers without engineering involvement.

A **Settings** section with a **Providers** lookup table lets Super Admins manage the list of available providers at runtime. The frontend loads the provider list dynamically, and the backend validates new tools and collectors against this live list.

## What Changes (this slice)

### 1. New top-level navigation: Settings

Add a "Settings" menu item in the main sidebar (Super Admin only). Initial tab: **Providers**.

### 2. Providers lookup table

A configurable list of provider entries, each with:
- `id` — UUID primary key (system-assigned on create)
- `label` — display name (e.g. "OpenAI", "My Internal LLM"); unique among active providers
- `description` — optional short description
- `logo_url` — optional external image URL for display
- `built_in` — boolean; built-in providers (seeded) cannot be deleted but can be disabled
- `active` — toggle to show/hide from dropdowns

### 3. API endpoints

```
GET    /api/v1/settings/providers              → ProviderListResponse
POST   /api/v1/settings/providers              → Provider (201)  [super_admin]
PATCH  /api/v1/settings/providers/{providerId} → Provider (200)  [super_admin]
DELETE /api/v1/settings/providers/{providerId} → 204             [super_admin; non-built-in only]
```

`GET` is accessible to all authenticated users (needed by tool/credential dropdowns).

### 4. Frontend — dynamic provider dropdown

Tool form and credential form load providers from `GET /api/v1/settings/providers?active=true`. Built-in providers are seeded on migration so the dropdowns always have data.

### 5. Seed data

Built-in provider seeds (added in migration): OpenAI, Anthropic, Google, Azure OpenAI, Cohere, Mistral, Cursor, Mabl, Windsurf, Figma, Custom — each with a stable UUID `id`.

## Out of Scope

- Per-provider OAuth or SSO configuration
- Provider-specific adapter registration — **superseded by** [provider-creation.md](../../specifications/provider-creation.md) (config-driven integration engine)
- Other settings categories (notifications, appearance, etc.)

## Dependencies

- `tool-catalogue-redesign` — consumes provider list for tool form dropdown
- `credentials-connect-tool-redesign` — consumes provider list for credential form
