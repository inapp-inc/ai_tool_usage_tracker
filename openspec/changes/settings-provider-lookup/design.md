# Design: Settings — Provider Lookup Keys

## Database

New table `admin.providers`:

```sql
CREATE TABLE admin.providers (
    slug          VARCHAR(64) PRIMARY KEY,
    label         VARCHAR(200) NOT NULL,
    description   TEXT,
    logo_url      VARCHAR(512),
    built_in      BOOLEAN NOT NULL DEFAULT FALSE,
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);
```

Seed insert (migration):

```sql
INSERT INTO admin.providers (slug, label, built_in, sort_order) VALUES
  ('openai',       'OpenAI',       TRUE, 10),
  ('anthropic',    'Anthropic',    TRUE, 20),
  ('google',       'Google',       TRUE, 30),
  ('azure_openai', 'Azure OpenAI', TRUE, 40),
  ('cohere',       'Cohere',       TRUE, 50),
  ('mistral',      'Mistral',      TRUE, 60),
  ('cursor',       'Cursor',       TRUE, 70),
  ('mabl',         'Mabl',         TRUE, 80),
  ('windsurf',     'Windsurf',     TRUE, 90),
  ('figma',        'Figma',        TRUE, 100),
  ('custom',       'Custom',       TRUE, 110);
```

## API Schemas

### `Provider` response

```yaml
slug: string
label: string
description: string | null
logo_url: string | null
built_in: boolean
active: boolean
sort_order: integer
```

### `ProviderCreateRequest`

```yaml
slug: string (required, pattern: ^[a-z0-9_]+$, maxLength: 64)
label: string (required, maxLength: 200)
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
- Providers tab: DataTable with columns: Label, Slug, Active, Built-in, Actions (edit, toggle active, delete non-built-in)
- "Add Provider" button → slide-over form with Slug, Label, Description fields
- Edit slide-over: same fields + Active toggle

### Provider API module (`frontend/src/api/providers.ts`)

```ts
fetchProviders(activeOnly?: boolean): Promise<Provider[]>
createProvider(body): Promise<Provider>
updateProvider(slug, body): Promise<Provider>
deleteProvider(slug): Promise<void>
```

### Tool/credential dropdowns

Replace hardcoded provider arrays with:

```ts
const { data: providers } = useQuery({ queryKey: ['providers'], queryFn: () => fetchProviders(true) })
```

Fallback to built-in static list on query failure to ensure dropdowns never appear empty.

## RBAC

- `GET /settings/providers` — all authenticated users
- `POST / PATCH / DELETE` — super_admin only
- Built-in providers: PATCH (label/logo/active), DELETE forbidden (return 409 Conflict)
