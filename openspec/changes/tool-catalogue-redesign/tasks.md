# Tasks: Tool Catalogue Redesign

## 1. Backend

- [x] 1.1 Alembic migration — add `api_endpoint VARCHAR(512) NULL` to `admin.tools`
- [x] 1.2 Update `ToolCreateRequest`, `ToolUpdateRequest`, `ToolResponse` schemas with `api_endpoint`
- [x] 1.3 Validate: `custom` provider requires `api_endpoint`; value must start with `https://`
- [x] 1.4 Update `ToolRepository.create` / `update` to persist and return `api_endpoint`
- [x] 1.5 Update collector adapter base resolution: prefer `tool.api_endpoint` over hardcoded default
- [x] 1.6 Update OpenAPI spec (`openspec/specifications/apis/openapi.yaml`) with `api_endpoint` field

## 2. Frontend

- [x] 2.1 Rename "Connect Tool" button to "Add Tool" in `ToolsPage.tsx`
- [x] 2.2 Rename slide-over titles ("Add Tool" / "Edit Tool")
- [x] 2.3 Remove pricing fields (token rates, seat cost, package allowance) from tool form
- [x] 2.4 Add `api_endpoint` text field ("API Endpoint URL" — full URL) to tool form; mark required when provider is `custom`
- [x] 2.5 Update provider dropdown to fetch from `GET /api/v1/settings/providers` with built-in fallback
- [x] 2.6 Update `frontend/src/api/adapters/tools.ts` — add `apiEndpoint` to `AiTool` and write-body types; remove `apiKey` from `CreateToolRequest`
- [x] 2.7 Update `ToolsPage` form schema (zod) to include `apiEndpoint` and custom-provider validation
- [x] 2.8 Remove API key field from Add/Edit Tool form — API keys are collected in the Credentials section only
- [x] 2.9 Simplify tools list: remove Tokens used, Members, Pricing, Total cost, Last synced, sync and members actions; add Provider column with display name

## 3. Tests

- [x] 3.1 Backend unit test: `custom` provider without `api_endpoint` returns 422
- [x] 3.2 Backend unit test: `api_endpoint` returned correctly in tool response
- [ ] 3.3 Frontend test: "Add Tool" label present; pricing fields absent from form; list shows Tool, Provider, Status only
