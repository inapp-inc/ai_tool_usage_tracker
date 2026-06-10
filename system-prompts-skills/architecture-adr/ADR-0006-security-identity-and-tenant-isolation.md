# ADR-0006: Security, Identity, and Tenant Isolation

## Status
**Accepted**

## Date
2026-02-02

## Authors
Platform Architecture Team

---

## 1. Context

The platform architecture defined in:
- **ADR-0001 (MERN + Python Modular Platform Architecture)**
- **ADR-0002 (Plugin and Extensibility Architecture)**
- **ADR-0003 (Deployment and Cloud Strategy)**
- **ADR-0004 (Data and Persistence Strategy)**
- **ADR-0005 (Eventing and Asynchronous Communication)**

supports:
- A multi-tenant SaaS model
- Plugin-based extensibility
- Event-driven communication
- Independent Node.js and Python services

This architecture requires a **centralized, consistent, and scalable security model** that ensures:
- Strong identity guarantees
- Robust tenant isolation
- Controlled plugin execution
- Minimal duplication of security logic across services

---

## 2. Problem Statement

Without a unified security and identity strategy, platforms typically face:

- Fragmented authentication mechanisms
- Inconsistent authorization checks
- Accidental cross-tenant data exposure
- Excessive duplication of security logic
- Increased risk when extending the platform via plugins

The platform requires a **single source of truth for identity and tenant context**, while allowing services and plugins to operate independently and securely.

---

## 3. Decision Drivers

The decision is driven by:

1. Multi-tenant SaaS requirements
2. Plugin-based extensibility
3. Security consistency across services
4. Cloud-native deployment patterns
5. Principle of least privilege
6. Auditable and enforceable access controls
7. Ease of future compliance

---

## 4. Decision

The platform will adopt a **centralized identity and authorization model**, where:

- Identity is established and validated at the **Node.js platform core**
- Authorization and tenant context are enforced centrally
- Services and plugins consume **trusted, platform-issued identity tokens**
- Tenant isolation is enforced logically by default
- Security responsibilities are clearly separated between platform and plugins

---

## 5. Identity Architecture

### 5.1 Central Identity Authority

The Node.js platform core acts as the **identity authority**.

Responsibilities:
- User authentication
- Token issuance
- Tenant resolution
- Role and permission evaluation

No downstream service performs primary authentication.

---

### 5.2 Authentication Mechanisms

Supported mechanisms may include:
- Username/password
- OAuth 2.0 / OpenID Connect
- Enterprise identity providers (SSO)

Authentication method choice is abstracted behind the platform.

---

## 6. Token Strategy

### 6.1 JWT-Based Identity Propagation

Identity and tenant context are propagated using **JSON Web Tokens (JWTs)**.

#### Canonical JWT Claims

```json
{
  "iss": "platform-core",
  "sub": "user_123",
  "tenant_id": "tenant_456",
  "roles": ["admin"],
  "permissions": ["invoice.create", "report.view"],
  "iat": 1706865000,
  "exp": 1706868600
}
````

---

### 6.2 Token Trust Model

* Tokens are signed by the platform
* Downstream services validate signature and expiry
* No downstream service modifies token claims

This establishes a **zero-trust internal model** with strong guarantees.

---

## 7. Authorization Model

### 7.1 Role-Based and Permission-Based Access

The platform supports:

* Role-Based Access Control (RBAC)
* Fine-grained permission checks

Permissions are:

* Declared by plugins
* Enforced centrally
* Evaluated per request and per event

---

### 7.2 Plugin Permission Declaration

Plugins must explicitly declare required permissions.

Example:

```ts
permissions: ["invoice.create", "invoice.read"]
```

The platform validates:

* Permission existence
* Tenant enablement
* User entitlement

---

## 8. Tenant Isolation Strategy

### 8.1 Logical Tenant Isolation (Default)

Tenant isolation is enforced via:

* Tenant-scoped tokens
* Tenant identifiers in all data records
* Tenant-aware indexing
* Tenant context in all events

This approach balances:

* Scalability
* Cost efficiency
* Operational simplicity

---

### 8.2 Physical Tenant Isolation (Exceptional)

Physical isolation (separate databases or deployments) may be used when:

* Regulatory requirements demand it
* High-risk tenants require stronger isolation
* Contractual obligations exist

This is an exception, not the default.

---

## 9. Plugin Security Model

### 9.1 Execution Boundaries

Plugins:

* Cannot bypass platform authentication
* Cannot access data outside declared permissions
* Operate strictly within tenant context
* Cannot access infrastructure credentials directly

---

### 9.2 Plugin Trust Levels

Plugins may be classified by trust level:

* Core plugins
* First-party plugins
* Third-party plugins

Higher-risk plugins may be:

* Restricted in permissions
* Sandboxed
* Subject to additional review

---

## 10. Service-to-Service Security

### 10.1 Internal Communication

* All inter-service calls must include platform-issued tokens
* Services validate tokens before processing requests or events
* Mutual TLS may be added later if required

---

### 10.2 Event Security

* Events include tenant context
* Consumers validate event metadata
* No consumer trusts event payloads blindly

---

## 11. Secrets Management

* Secrets are stored in managed secrets services
* Secrets are injected at runtime
* Secrets are never committed to source control

---

## 12. Audit and Compliance

The platform must support:

* Audit logging of authentication and authorization decisions
* Tenant-scoped access logs
* Plugin activation and permission changes
* Traceability across API calls and events

---

## 13. Consequences

### Positive Consequences

* Strong tenant isolation guarantees
* Consistent security enforcement
* Reduced duplication of auth logic
* Safer plugin extensibility
* Easier compliance and auditing

### Negative Consequences

* Central platform becomes a critical security component
* Requires disciplined permission management
* Token lifecycle management must be carefully handled

---

## 14. Alternatives Considered

1. **Decentralized authentication**

   * Rejected due to inconsistency and duplication risks

2. **Service-specific authorization logic**

   * Rejected due to maintainability concerns

3. **Physical tenant isolation by default**

   * Rejected due to operational and cost overhead

---

## 15. Decision Outcome

The platform adopts a **centralized identity, authorization, and tenant isolation model**, with the Node.js platform core acting as the authoritative security boundary.

This decision ensures:

* Strong security guarantees
* Safe extensibility
* Clear ownership of security responsibilities

---

## 16. Review & Revisit Criteria

This ADR should be revisited if:

* Regulatory requirements change
* Tenant isolation requirements increase
* Plugin ecosystem expands significantly
* Zero-trust networking requirements evolve

---

**End of ADR**
