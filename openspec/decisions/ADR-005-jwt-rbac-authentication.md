# ADR-005: JWT and RBAC Authentication (Phase 1)

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The platform serves five roles (Super Admin, Team Admin, Finance Viewer, Team Member, Auditor) with distinct data scopes and action permissions (FR-PLT-001). Phase 1 must authenticate users and enforce authorization on every API call. Full **SSO/SAML** is explicitly **out of scope** for Phase 1 (deferred to Phase 2, FR-P2-002).

Security NFRs require JWT lifecycle management, RBAC enforcement server-side, and secure credential handling separate from user authentication.

---

## Decision

Implement **JWT-based authentication** with **server-side RBAC** for Phase 1:

- Access tokens issued on successful login; validated on every API request via middleware.
- Token signing keys stored in **AWS Secrets Manager** (NFR-SEC-008).
- Default access token TTL: 15–60 minutes (configurable); refresh token rotation recommended.
- RBAC policy layer maps roles to permissions; enforced in application services, not UI alone.
- All API endpoints require `Authorization: Bearer <token>` except `/auth/login` and health checks.

Roles and scopes align with functional requirements (org-wide vs team-scoped vs read-only vs personal).

---

## Consequences

### Positive

- Simple integration with React SPA and stateless API horizontal scaling.
- No session affinity required on API pods.
- Clear Phase 1 delivery path without IdP federation complexity.
- Aligns with project.md technical direction.

### Negative

- Enterprise customers may require SSO before adoption—Phase 2 work required.
- JWT revocation requires short TTLs, refresh rotation, or token blocklist (Redis)—must be designed explicitly.
- Local user/password management adds admin overhead until SSO arrives.

### Neutral

- MFA not specified in Phase 1; can be added via IdP in Phase 2 SSO.
- Service-to-service auth (worker → API) uses internal credentials, not user JWTs.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **SSO/SAML (Phase 1)** | Explicitly out of scope; increases delivery time and IdP integration complexity. |
| **Session cookies (server-side sessions)** | Requires sticky sessions or shared session store; JWT better for stateless API scaling. |
| **OAuth2-only with external IdP** | No IdP mandated for MVP; JWT with local auth sufficient for Phase 1. |
| **API keys for user auth** | Unsuitable for interactive UI; appropriate only for future machine-to-machine ingestion APIs. |
| **Auth0/Cognito managed auth** | Valid option but adds vendor dependency and cost; defer unless customer mandates. |

**Supersedes:** None  
**Superseded by:** Future ADR for SSO/SAML (Phase 2)  
**Related:** ADR-001, ADR-002
