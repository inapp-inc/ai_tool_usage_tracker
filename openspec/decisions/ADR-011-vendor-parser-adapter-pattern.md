# ADR-011: Vendor Parser Adapter Pattern

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

Phase 1 ingestion accepts vendor export files from **OpenAI**, **Anthropic**, **Azure AI**, **Cursor**, and other configurable providers (FR-ING-001). Each vendor uses different column layouts, JSON schemas, and file formats (CSV, JSON, XLSX). The system must auto-detect format, normalize to a canonical usage record, and support new vendors without rewriting core ingestion logic (Open/Closed principle).

Parsing is CPU/IO intensive and runs in Celery workers (ADR-004).

---

## Decision

Implement vendor-specific parsers using the **Adapter pattern** behind a common **`ParserPort`** interface:

```text
ParserPort
├── detect(content) → bool
├── parse(content) → List[UsageRecord]
└── vendor_id() → str

Implementations: OpenAIParser, AnthropicParser, AzureAIParser, CursorParser, ConfigurableParser
Factory: ParserFactory.resolve(content) → ParserPort
```

**Canonical `UsageRecord`** fields: `vendor_event_id`, `user_email`, `tool_id`, `team_id`, `occurred_at`, `input_tokens`, `output_tokens`, `metadata`.

**ConfigurableParser** uses JSON mapping templates for additional vendors without code deployment. New first-class vendor support adds a dedicated adapter when mapping templates are insufficient.

---

## Consequences

### Positive

- New vendors added with isolated adapter code or configuration.
- Unit tests per vendor parser with fixture files.
- Normalization boundary clear before persistence to `usage_events`.
- Aligns with hexagonal architecture (ADR-001) and DDD ingestion bounded context.

### Negative

- Each major vendor format change requires adapter update or template revision.
- Auto-detection ambiguity if formats overlap—may require explicit vendor selection fallback.
- ConfigurableParser increases validation complexity for admin-defined mappings.

### Neutral

- Phase 2 vendor **API sync** will use separate Anti-Corruption Layer adapters (REST), distinct from file export parsers.
- Parser code lives in same monolith repository; extraction to microservice possible later.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Single generic CSV mapper only** | Insufficient for nested JSON exports (Anthropic, Azure). |
| **Hard-coded parsing in one service** | Violates Open/Closed; untestable monolith function. |
| **Third-party ETL tool (Airbyte)** | Operational overhead and cost disproportionate for Phase 1 file uploads. |
| **LLM-based schema inference** | Non-deterministic; unsuitable for financial usage data without validation. |
| **Database-stored raw files only (no parse)** | Does not meet usage tracking and dashboard requirements. |

**Supersedes:** None  
**Related:** ADR-001, ADR-004, ADR-009
