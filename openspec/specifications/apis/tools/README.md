# Tools API Specification

**Module:** AI Tool Management (FR-ADM-001)  
**Status:** Implemented — backend + frontend wired (2026-06-16)  
**Date:** 2026-06-16

Canonical OpenAPI: [`../openapi.yaml`](../openapi.yaml) · [`../components/schemas.yaml`](../components/schemas.yaml)

## Documents

| File | Description |
|------|-------------|
| [api-mapping.md](./api-mapping.md) | REST endpoints, frontend functions, auth, HTTP status codes |
| [payloads.md](./payloads.md) | Request/response models (OpenAPI + frontend TypeScript) |
| [adapter-mapping.md](./adapter-mapping.md) | camelCase ↔ snake_case, pricing model translation, FE-only fields |
| [examples.json](./examples.json) | Sample request/response JSON bodies |

## Frontend sources

| Path | Purpose |
|------|---------|
| `frontend/src/api/tools.ts` | Live API client |
| `frontend/src/api/adapters/tools.ts` | OpenAPI ↔ frontend mapping |
| `frontend/src/pages/admin/ToolsPage.tsx` | Admin CRUD + sync UI |

## Backend

| Path | Purpose |
|------|---------|
| `backend/app/tools/` | CRUD, API key validation, sync |
| `backend/app/collector/adapters/` | Provider adapters (OpenAI, Anthropic, Google, Azure, Cohere, Mistral, Custom, Mabl, Windsurf) |
| `backend/alembic/versions/006_admin_tools.py` | `admin.tools` + collector `tool_id` FK |

## Supported providers

`openai`, `anthropic`, `google`, `azure_openai`, `cohere`, `mistral`, `custom`, `mabl`, `windsurf`, `cursor`, `figma`

API keys are validated against the provider on create/update. Sync pulls token usage, cost, and balance (when package allowance is set).

## Implementation checklist

- [x] Migration `006_admin_tools`
- [x] `app/tools/` backend package
- [x] Wire `frontend/src/api/tools.ts` + `adapters/tools.ts`
- [x] `DELETE /tools/{toolId}`, `POST /tools/{toolId}/sync`
- [x] Persist `description` + `pricing_config` for FE pricing shape
- [x] Collector linked per tool with validate-on-save
