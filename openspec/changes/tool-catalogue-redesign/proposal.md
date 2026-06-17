# Proposal: Tool Catalogue Redesign

**Status:** 📋 Proposed

## Why

The current "Connect Tool" workflow conflates two separate concerns: cataloguing an AI tool (its name, provider, endpoint, and pricing) with establishing live API credentials for that tool. Users want to register tools they use — including endpoint details per tool — without needing to supply or validate API keys at that moment. Pricing configuration also belongs with teams (FR-ADM-002), not here. The button label "Connect Tool" implies an API connection is happening, when in fact the user is just adding a catalogue entry.

Additionally, providers are currently hardcoded in the frontend enum. They should be driven by a configurable lookup managed in Settings (see `settings-provider-lookup` change), making the platform extensible without code changes.

## What Changes (this slice)

### 1. Button label: "Add Tool" (was "Connect Tool")

`ToolsPage.tsx` — rename the primary CTA and any associated dialog titles / aria labels.

### 2. API endpoint field per tool entry

When adding a tool, allow the user to enter a **Base API URL / endpoint** for the provider. This is stored on the tool record and passed to adapters at collection time (replacing hardcoded URLs in adapter files). Field is optional for built-in providers (OpenAI, Anthropic, etc.) and required for custom providers.

New `api_endpoint` field on the tools table and API:
- `POST /api/v1/tools` → accept `api_endpoint?: string`
- `PATCH /api/v1/tools/{id}` → accept `api_endpoint?: string`
- `GET /api/v1/tools` / `GET /api/v1/tools/{id}` → return `api_endpoint`

### 3. Pricing configuration moves to Teams

Remove the per-tool pricing configuration panel from the Add/Edit Tool slide-over. Pricing (model, token rates, seat cost, package allowance) is now configured per team–tool pairing in the Teams section (see `team-pricing-configuration` change).

Tool records retain a `default_pricing_model` (informational) but per-team cost overrides live on team configuration.

### 4. Provider is lookup-driven

The provider dropdown reads from a lookup table managed under Settings (see `settings-provider-lookup` change). The frontend no longer hardcodes the `providerValues` array; it fetches from `GET /api/v1/settings/providers`.

During transition, built-in providers are seeded on first run.

## Out of Scope

- API key / credential management (handled by `credentials-connect-tool-redesign`)
- Provider CRUD in Settings (handled by `settings-provider-lookup`)
- Per-team pricing configuration (handled by `team-pricing-configuration`)

## Dependencies

- `settings-provider-lookup` — provider dropdown data source
- `team-pricing-configuration` — destination for pricing config fields removed here
