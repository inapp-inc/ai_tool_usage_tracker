# ADR-016: Dashboard Cache Key RBAC Scope Hashing

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

ADR-008 requires Redis cache-aside for dashboard widgets. Dashboard responses are **RBAC-scoped** — the same date filter yields different data for a Team Member vs Super Admin. Caching by organization and date alone would leak data across roles or team scopes (NFR-PER-006, NFR-SCL-005).

---

## Decision

Dashboard cache keys MUST include:

1. `organization_id`
2. Widget endpoint identifier
3. **`scope_hash`** — SHA-256 of canonical JSON: `{role, allowed_team_ids[], allowed_user_id}`
4. **`filter_hash`** — SHA-256 of normalized query parameters (`from`, `to`, `team_id`, `tool_id`, `granularity`, `limit`, `entity`)

Key format: `dash:{org_id}:{endpoint}:{scope_hash}:{filter_hash}`

TTL: configurable 60–300 seconds (default 120).

Invalidation: delete by prefix `dash:{org_id}:*` on aggregate refresh, pricing change, or membership change.

---

## Consequences

### Positive

- Prevents cross-role and cross-team cache leakage.
- Testable invariant for security integration tests.
- Org-wide invalidation is simple and correct.

### Negative

- Higher cardinality of cache keys vs org-only keys.
- Prefix invalidation may delete more entries than strictly necessary.

### Neutral

- CDN or shared HTTP caching remains unsuitable for dashboard APIs.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Cache by org + filters only** | RBAC leakage risk |
| **No caching** | Misses NFR-PER-001 at scale |
| **Per-user cache keys only** | Insufficient for team-scoped roles; higher cardinality |

**Supersedes:** None  
**Superseded by:** None  
**Related:** ADR-008, ADR-005
