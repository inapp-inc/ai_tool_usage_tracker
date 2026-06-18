# Design: Settings — Provider Lookup Keys

**Target identity model:** Providers are identified by UUID `id` and human-readable `label` only — no slug. See [provider-creation.md](../../specifications/provider-creation.md) for integration config and migration from legacy slug keys.

## Database

Table `admin.providers` (target shape):

```sql
CREATE TABLE admin.providers (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label         VARCHAR(200) NOT NULL UNIQUE,
    description   TEXT,
    logo_url      VARCHAR(512),
    built_in      BOOLEAN NOT NULL DEFAULT FALSE,
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);
```

Seed insert (migration) — stable UUIDs assigned per row; tools reference `provider_id`:

```sql
INSERT INTO admin.providers (id, label, built_in, sort_order) VALUES
  ('…', 'OpenAI',       TRUE, 10),
  ('…', 'Anthropic',    TRUE, 20),
  ('…', 'Google',       TRUE, 30),
  ('…', 'Azure OpenAI', TRUE, 40),
  ('…', 'Cohere',       TRUE, 50),
  ('…', 'Mistral',      TRUE, 60),
  ('…', 'Cursor',       TRUE, 70),
  ('…', 'Mabl',         TRUE, 80),
  ('…', 'Windsurf',     TRUE, 90),
  ('…', 'Figma',        TRUE, 100),
  ('…', 'Custom',       TRUE, 110);
```

## API Schemas

### `Provider` response

```yaml
id: uuid
label: string
description: string | null
logo_url: string | null
built_in: boolean
active: boolean
sort_order: integer
```

### `ProviderCreateRequest`

```yaml
label: string (required, maxLength: 200, unique among active providers)
description: string | null
logo_url: string | null
sort_order: integer (default: 0)
```

### `ProviderUpdateRequest`

```yaml
label: string | null
description: string | null
logo_url: string | null
active: boolean | null
sort_order: integer | null
```

### `ProviderListResponse`

```yaml
data: Provider[]
```

## Frontend

### Navigation

New "Settings" item in the sidebar nav (`/admin/settings`), visible only to Super Admins.

### SettingsPage (`frontend/src/pages/admin/SettingsPage.tsx`)

- Tab bar: "Providers" (only tab for this slice)
- Providers tab: DataTable with columns: Label, Active, Built-in, Actions (edit, toggle active, delete non-built-in)
- "Add Provider" button → slide-over form with Label, Description fields
- Edit slide-over: same fields + Active toggle

### Provider API module (`frontend/src/api/providers.ts`)

```ts
fetchProviders(activeOnly?: boolean): Promise<Provider[]>
createProvider(body): Promise<Provider>
updateProvider(providerId, body): Promise<Provider>
deleteProvider(providerId): Promise<void>
```

### Tool/credential dropdowns

Replace hardcoded provider arrays with:

```ts
const { data: providers } = useQuery({ queryKey: ['providers'], queryFn: () => fetchProviders(true) })
```

Dropdown displays `label`; forms persist `provider_id`. Fallback to built-in static list on query failure to ensure dropdowns never appear empty.

## RBAC

- `GET /settings/providers` — all authenticated users
- `POST / PATCH / DELETE` — super_admin only
- Built-in providers: PATCH (label/logo/active), DELETE forbidden (return 409 Conflict)
