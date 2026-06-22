# Vendor Mapping — Normalized Schemas

**Status:** Implemented (Cursor excluded — existing mapping unchanged)

## Categories

| Category | Vendors | Storage |
| --- | --- | --- |
| Token Based | OpenAI, Claude, Gemini, Azure OpenAI, Bedrock, OpenRouter, DeepSeek, Groq, Mistral, Cohere | `usage.usage_events` via `UsageRecord` |
| Productivity Based | GitHub Copilot, Amazon Q Developer, Gemini Code Assist | `copilot.*` + productivity tables |
| License Based | Figma, Notion AI, Grammarly, Canva | License events → `UsageRecord` seat proxy + future license tables |

## Code location

- `backend/app/normalization/schemas.py` — normalized dataclasses
- `backend/app/normalization/cost_engine.py` — cost rules
- `backend/app/normalization/token.py` — token vendor mappers
- `backend/app/normalization/productivity.py` — productivity mappers
- `backend/app/normalization/license.py` — license mappers
- `backend/app/normalization/converters.py` — `NormalizedTokenEvent` → `UsageRecord`

## Cost engine

**Token:** API cost if present; else `(input/1M × input_price) + (output/1M × output_price)`

**Productivity:** `monthly_package_cost / assigned_seats`

**License:** `monthly_package_cost / assigned_licenses`
