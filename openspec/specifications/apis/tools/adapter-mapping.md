# Tools — Frontend ↔ OpenAPI Adapter Mapping

Implement in `frontend/src/api/adapters/tools.ts` when wiring the backend (mirror [teams adapter](../../../frontend/src/api/adapters/teams.ts)).

---

## Field renames

| Frontend (camelCase) | OpenAPI (snake_case) |
|----------------------|----------------------|
| `provider` | `vendor` |
| `createdAt` | `created_at` |
| `organizationId` | `organization_id` |
| `pricing.model` | `pricing_model` |
| `pricing.inputCostPer1K` | `token_price` and/or `pricing_config.input_cost_per_1k` |
| `pricing.outputCostPer1K` | `pricing_config.output_cost_per_1k` |
| `pricing.includedTokens` | `package_allowance` |
| `pricing.overageRate` | `overage_price` |
| `status` | `active` |

### Status mapping

| Frontend `status` | OpenAPI `active` | Notes |
|-------------------|------------------|-------|
| `active` | `true` | |
| `inactive` | `false` | deactivate, not delete |
| `error` | `true` (typically) | FE-only; derive from collector/sync health |

---

## Provider / vendor mapping

Tools reference providers by **`provider_id`** (UUID from Settings). The OpenAPI `vendor` field holds the provider **label** for display and legacy compatibility.

| Frontend | API |
|----------|-----|
| `providerId` | `provider_id` on tool create/update |
| `provider` (display) | Resolve label from `GET /settings/providers` by id |

Store `provider_id` on the tool record; resolve label for display via the providers lookup — no slug field.

---

## Pricing model mapping

| Frontend `PricingModel` | OpenAPI `pricing_model` | Primary fields |
|-------------------------|-------------------------|----------------|
| `per_token` | `flat_token` | `token_price` = avg or input rate; `pricing_config` holds input/output |
| `per_seat` | `custom` | `pricing_config`: `{ cost_per_seat, seat_count }` |
| `flat_fee` | `package_with_overage` | `package_allowance`, `overage_price`, `pricing_config.flat_monthly_cost` |
| `hybrid` | `custom` | `pricing_config` holds combined seat + token fields |

### `ToolPricing` → OpenAPI (create/update)

**`per_token`**

```typescript
{
  pricing_model: "flat_token",
  token_price: pricing.inputCostPer1K ?? 0, // or blended rate
  pricing_config: {
    model: "per_token",
    input_cost_per_1k: pricing.inputCostPer1K,
    output_cost_per_1k: pricing.outputCostPer1K,
  }
}
```

**`flat_fee`**

```typescript
{
  pricing_model: "package_with_overage",
  token_price: pricing.overageRate ?? 0,
  package_allowance: pricing.includedTokens,
  overage_price: pricing.overageRate,
  pricing_config: {
    model: "flat_fee",
    flat_monthly_cost: pricing.flatMonthlyCost,
    plan_name: pricing.planName,
  }
}
```

**`per_seat` / `hybrid`**

```typescript
{
  pricing_model: "custom",
  token_price: 0,
  pricing_config: { model: pricing.model, ...pricing }
}
```

### OpenAPI `Tool` → `AiTool`

| Source | Target |
|--------|--------|
| `vendor` / `provider_id` | `provider` (label from providers lookup by id) |
| `active` | `status` (`active` / `inactive`) |
| `token_price`, `package_allowance`, `overage_price`, `pricing_config` | `pricing` object |
| — | `description` from `pricing_config.description` or DB column |
| — | `apiKeyMasked` from credentials join (optional on list) |
| — | `tokenCount`, `costTotal` from usage aggregates (0 until usage slice) |
| — | `lastSyncAt` from collector last run (null until collector linked) |

---

## API key handling

| Step | API |
|------|-----|
| 1. Create tool | `POST /tools` (no secret) |
| 2. Store credential | `POST /credentials` with `tool_id`, encrypted secret |
| 3. Display mask | `secret_last_four` → `apiKeyMasked` (`sk-...{last4}`) |

On **edit**, non-empty `apiKey` → `POST /credentials` rotate or `PATCH /credentials/{id}` (planned).

---

## Gaps to resolve in implementation

1. **`DELETE /tools/{toolId}`** — add to OpenAPI or use deactivate-only.
2. **`POST /tools/{toolId}/sync`** — add to OpenAPI or fold into collector `POST .../run`.
3. **`description`** — add column or `pricing_config.description`.
4. **`status: error`** — define source (collector run failure vs tool health).
5. **List enrichments** — document whether `GET /tools` returns usage totals or requires separate dashboard call.
