# Tasks: Settings — Provider Lookup Keys

## 1. Backend

- [ ] 1.1 Alembic migration — create `admin.providers` table with built-in seed data
- [ ] 1.2 SQLAlchemy model `Provider`
- [ ] 1.3 `ProviderRepository`: list (active filter), create, update, delete (guard built-in)
- [ ] 1.4 API router at `/api/v1/settings/providers` — GET (public auth), POST/PATCH/DELETE (super_admin)
- [ ] 1.5 DELETE guard: return 409 if `built_in = TRUE`
- [ ] 1.6 Slug validation: `^[a-z0-9_]+$`, unique constraint
- [ ] 1.7 Update OpenAPI spec with `Provider`, `ProviderCreateRequest`, `ProviderUpdateRequest`, `/settings/providers` paths

## 2. Frontend

- [ ] 2.1 Add "Settings" menu item to sidebar (super_admin only, route `/admin/settings`)
- [ ] 2.2 Create `SettingsPage.tsx` with Providers tab
- [ ] 2.3 Providers DataTable: slug, label, active badge, built-in badge, edit/delete actions
- [ ] 2.4 Add Provider slide-over form (slug, label, description)
- [ ] 2.5 Edit Provider slide-over (label, description, logo_url, active toggle)
- [ ] 2.6 Create `frontend/src/api/providers.ts` with `fetchProviders`, `createProvider`, `updateProvider`, `deleteProvider`
- [ ] 2.7 Replace hardcoded `PROVIDER_OPTIONS` / `providerValues` in `ToolsPage.tsx` with `useQuery` from `fetchProviders`
- [ ] 2.8 Replace hardcoded provider list in `CredentialsPage.tsx` with same query
- [ ] 2.9 Add static fallback list for when query fails (keeps forms usable offline)

## 3. Tests

- [ ] 3.1 Backend: list returns seeded built-in providers
- [ ] 3.2 Backend: delete built-in returns 409
- [ ] 3.3 Backend: create with invalid slug pattern returns 422
- [ ] 3.4 Frontend: Settings route accessible to super_admin; hidden for other roles
