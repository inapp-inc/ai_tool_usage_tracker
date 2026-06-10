# ADR-014: Opaque Refresh Tokens with Database Rotation

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

ADR-005 establishes JWT access tokens with recommended refresh token rotation for Phase 1. The OpenAPI contract and [database.md](../../openspec/specifications/database.md) define an `auth.refresh_tokens` table storing hashed refresh tokens with revocation timestamps.

Implementation must choose how refresh tokens are represented, stored, and rotated without exposing usable secrets if the database is compromised.

---

## Decision

Use **opaque refresh tokens** (cryptographically random, 256-bit) with **SHA-256 hash-at-rest** in `auth.refresh_tokens` and **strict rotation on every refresh**:

1. Plaintext refresh token returned once to the client in `TokenResponse.refresh_token`.
2. Server stores only `SHA-256(plaintext)` in `token_hash`.
3. On `POST /auth/refresh`: validate hash, revoke current row (`revoked_at`), insert new row, return new token pair.
4. Reuse of a revoked refresh token SHALL reject the request and MAY revoke all active refresh tokens for that user (reuse detection — optional Phase 1 enhancement).

Access tokens remain stateless JWTs (HS256) with short TTL per ADR-005.

---

## Consequences

### Positive

- Database leak does not expose usable refresh tokens.
- Revocation is immediate and auditable via `revoked_at`.
- Aligns with `auth.refresh_tokens` schema already specified.
- Supports future token reuse detection for breach response.

### Negative

- Requires database round-trip on every refresh (acceptable at MVP scale).
- Opaque tokens cannot carry claims — user lookup required on refresh.

### Neutral

- JWT refresh tokens remain an alternative if stateless refresh is needed later — would require new ADR to supersede this record.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **JWT refresh tokens** | Harder to revoke without blocklist; contradicts dedicated refresh table |
| **Store plaintext refresh tokens** | Unacceptable security risk on DB breach |
| **No refresh tokens** | Poor SPA UX; conflicts with OpenAPI TokenResponse |
| **Redis-only refresh storage** | Loses audit trail; PostgreSQL already specified |

**Supersedes:** None  
**Superseded by:** None  
**Related:** ADR-005, ADR-003
