# ADR-019: Scheduled Vendor API Usage Collectors

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

FR-ING-004 requires automated collection of usage from vendor AI tool APIs using stored credentials, with **hourly** or **daily** schedules configurable per integration. File upload ingestion (FR-ING-001) alone cannot meet FR-USG-002 near-real-time sync goals.

---

## Decision

Implement a **collector module** in the ingestion bounded context:

1. **Configuration:** `ingestion.collector_configs` links tool, optional team, encrypted credential, provider, and `schedule` (`hourly`|`daily`).
2. **Execution:** Celery task `ingestion.collect_usage` on the `ingestion` queue, triggered by Beat (hourly/daily scans) or on-demand API.
3. **Adapters:** Provider-specific collectors (OpenAI, Anthropic, Azure AI, Cursor) following ADR-011 adapter pattern.
4. **Frontend connect:** REST API accepts provider-managed connection with API token (write-once) or existing credential reference; schedule selectable at connect time.
5. **Pipeline:** Normalized events feed FR-USG-002 idempotent ingestion → aggregate refresh → threshold evaluation hook.

---

## Consequences

### Positive

- Reduces manual upload burden; aligns with US-USG-002-01.
- Reuses FR-ADM-003 credential encryption.
- Clear separation: config API (sync) vs collection (async worker).

### Negative

- Vendor API diversity increases adapter maintenance.
- Hourly collection increases API call volume and worker load.

### Neutral

- File upload remains supported in parallel.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Polling only via file exports** | Does not satisfy API sync requirement |
| **Single global poll interval** | Cannot meet per-integration hourly vs daily choice |
| **Frontend stores token in browser** | Violates NFR-SEC-001; server-side credentials required |

**Supersedes:** None  
**Related:** ADR-011, FR-ING-004, FR-USG-002
