# Tools — Request & Response Payloads

Naming: **OpenAPI** uses `snake_case`; **frontend** uses `camelCase`.

---

## OpenAPI schemas

Source: [`../components/schemas.yaml`](../components/schemas.yaml)

### `PricingModel` (OpenAPI enum)

```
flat_token | package_with_overage | custom
```

### `ToolCreateRequest`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | 1–100 chars, unique per org |
| `vendor` | string | yes | 1–100 chars |
| `pricing_model` | `PricingModel` | yes | |
| `token_price` | number (decimal) | yes | ≥ 0, price per 1K tokens |
| `package_allowance` | integer (int64) | no | ≥ 0; required when `pricing_model` = `package_with_overage` |
| `overage_price` | number (decimal) | no | ≥ 0; required with package allowance |
| `pricing_config` | object | no | Extended JSON for custom/hybrid pricing |

### `ToolUpdateRequest`

All fields optional:

| Field | Type |
|-------|------|
| `name` | string (1–100) |
| `vendor` | string (max 100) |
| `pricing_model` | `PricingModel` |
| `token_price` | number ≥ 0 |
| `package_allowance` | integer ≥ 0 |
| `overage_price` | number ≥ 0 |
| `active` | boolean |

### `Tool` (response)

| Field | Type | Required |
|-------|------|----------|
| `id` | uuid | yes |
| `organization_id` | uuid | yes |
| `name` | string | yes |
| `vendor` | string | yes |
| `pricing_model` | `PricingModel` | yes |
| `token_price` | number | yes |
| `package_allowance` | integer \| null | no |
| `overage_price` | number \| null | no |
| `pricing_config` | object | no (DB default `{}`) |
| `active` | boolean | yes |
| `created_at` | date-time | yes |
| `updated_at` | date-time | no in schema; present in DB |

### `ToolListResponse`

| Field | Type |
|-------|------|
| `data` | `Tool[]` |
| `meta` | `PaginationMeta` |

---

## Frontend TypeScript types

Source: `frontend/src/api/tools.ts`

### `ToolProvider`

```
openai | anthropic | google | azure_openai | cohere | mistral | custom
```

### `PricingModel` (frontend)

```
per_token | per_seat | flat_fee | hybrid
```

### `ToolPricing`

| Field | Type |
|-------|------|
| `model` | `PricingModel` |
| `inputCostPer1K` | number \| null |
| `outputCostPer1K` | number \| null |
| `costPerSeat` | number \| null |
| `seatCount` | number \| null |
| `flatMonthlyCost` | number \| null |
| `planName` | string \| null |
| `includedTokens` | number \| null |
| `overageRate` | number \| null |

### `AiTool` (list/detail — frontend)

| Field | Type | OpenAPI `Tool` | Notes |
|-------|------|---------------|-------|
| `id` | string | `id` | |
| `name` | string | `name` | |
| `provider` | `ToolProvider` | `vendor` | rename + enum mapping |
| `description` | string | — | **FE/DB extension** — store in `pricing_config` or column |
| `pricing` | `ToolPricing` | split fields + `pricing_config` | see [adapter-mapping.md](./adapter-mapping.md) |
| `status` | `active` \| `inactive` \| `error` | `active` boolean | `error` = sync health (FE-only) |
| `apiKeyMasked` | string | — | from **Credentials** (`secret_last_four`) |
| `lastSyncAt` | string \| null | — | collector/sync metadata |
| `tokenCount` | number | — | usage aggregate (read model) |
| `costTotal` | number | — | usage aggregate (read model) |
| `createdAt` | string | `created_at` | |

### `CreateToolRequest`

| Field | Type | Sent to `/tools`? |
|-------|------|-------------------|
| `name` | string | yes → `name` |
| `provider` | `ToolProvider` | yes → `vendor` |
| `apiKey` | string | **no** → Credentials API |
| `description` | string | extension |
| `pricing` | `ToolPricing` | yes → pricing fields + `pricing_config` |

### `UpdateToolRequest`

`Partial<CreateToolRequest>` — empty `apiKey` on edit means “unchanged”.

---

## JSON examples (OpenAPI)

### Create tool — package with overage

```json
{
  "name": "ChatGPT Enterprise",
  "vendor": "OpenAI",
  "pricing_model": "package_with_overage",
  "token_price": 0.002,
  "package_allowance": 10000000,
  "overage_price": 0.003
}
```

### Tool response

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440010",
  "organization_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "ChatGPT Enterprise",
  "vendor": "OpenAI",
  "pricing_model": "package_with_overage",
  "token_price": 0.002,
  "package_allowance": 10000000,
  "overage_price": 0.003,
  "active": true,
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

---

## JSON examples (frontend mock shape)

### `AiTool` (per-token)

```json
{
  "id": "tool_1",
  "name": "Production OpenAI",
  "provider": "openai",
  "description": "Primary GPT-4o production endpoint.",
  "pricing": {
    "model": "per_token",
    "inputCostPer1K": 0.005,
    "outputCostPer1K": 0.015,
    "costPerSeat": null,
    "seatCount": null,
    "flatMonthlyCost": null,
    "planName": null,
    "includedTokens": null,
    "overageRate": null
  },
  "status": "active",
  "apiKeyMasked": "sk-...a3Fb",
  "lastSyncAt": "2026-06-16T09:30:00.000Z",
  "tokenCount": 2840000,
  "costTotal": 184.6,
  "createdAt": "2026-03-18T10:00:00.000Z"
}
```

### `CreateToolRequest` (form submit)

```json
{
  "name": "Production OpenAI",
  "provider": "openai",
  "apiKey": "sk-proj-xxxxxxxxxxxx",
  "description": "Primary GPT-4o production endpoint.",
  "pricing": {
    "model": "per_token",
    "inputCostPer1K": 0.005,
    "outputCostPer1K": 0.015,
    "costPerSeat": null,
    "seatCount": null,
    "flatMonthlyCost": null,
    "planName": null,
    "includedTokens": null,
    "overageRate": null
  }
}
```

### Flat-fee pricing example

```json
{
  "name": "Internal LLM Gateway",
  "provider": "custom",
  "apiKey": "sk-internal-xxxxx",
  "description": "Self-hosted gateway.",
  "pricing": {
    "model": "flat_fee",
    "inputCostPer1K": null,
    "outputCostPer1K": null,
    "costPerSeat": null,
    "seatCount": null,
    "flatMonthlyCost": 99,
    "planName": "Team Pro",
    "includedTokens": 1000000,
    "overageRate": 0.002
  }
}
```
