# Tasks: Settings — Provider Lookup Keys

## 1. Backend

- [x] 1.1 Alembic migration — create `admin.providers` table with built-in seed data
- [x] 1.2 SQLAlchemy model `Provider`
- [x] 1.3 `ProviderRepository`: list (active filter), create, update, delete (guard built-in)
- [x] 1.4 API router at `/api/v1/settings/providers` — GET (public auth), POST/PATCH/DELETE (super_admin)
- [x] 1.5 DELETE guard: return 409 if `built_in = TRUE`
- [x] 1.6 Slug validation: `^[a-z0-9_]+$`, unique constraint
- [x] 1.7 Tool vendor validation against active providers; generic adapter fallback for unknown slugs
- [x] 1.8 Custom (non-built-in) providers require `api_endpoint` on tool create/update

## 2. Frontend

- [x] 2.1 Add "Settings" menu item to sidebar (super_admin only, route `/admin/settings`)
- [x] 2.2 Create `SettingsPage.tsx` with Providers table
- [x] 2.3 Providers DataTable: slug, label, active badge, built-in badge, edit/delete actions
- [x] 2.4 Add Provider slide-over form (slug, label, description)
- [x] 2.5 Edit Provider slide-over (label, description, active toggle)
- [x] 2.6 `frontend/src/api/providers.ts` with CRUD + `providerRequiresApiEndpoint`
- [x] 2.7 `ToolsPage.tsx` loads providers dynamically; requires API URL for custom providers
- [x] 2.8 Static fallback list when query fails

## 3. Tests

- [x] 3.1 Backend: create custom provider
- [x] 3.2 Backend: delete built-in returns 409
