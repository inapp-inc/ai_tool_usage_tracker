# ADR-0004: Data and Persistence Strategy

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

requires a data and persistence approach that:

- Supports modular, plugin-driven feature development
- Handles diverse data access patterns
- Scales independently with platform growth
- Aligns with cloud-native, managed infrastructure
- Avoids premature coupling between unrelated domains

The platform includes:
- A Node.js-based platform core
- Python-based capability services
- Event-driven and API-driven communication
- Multi-tenant requirements

A single-database strategy is insufficient to meet these needs.

---

## 2. Problem Statement

Common data architecture challenges include:

- Overloading a single database with incompatible workloads
- Tight coupling between services through shared schemas
- Difficulty evolving schemas in plugin-based systems
- Poor performance when analytical and transactional workloads coexist
- Complicated tenant isolation strategies

The platform requires a **flexible, scalable, and evolvable persistence strategy** that:
- Supports multiple data models
- Aligns storage technology with access patterns
- Preserves service and plugin boundaries
- Enables future scaling and refactoring without major redesign

---

## 3. Decision Drivers

The data architecture decision is driven by:

1. Support for modular and plugin-based development
2. Performance across diverse workloads
3. Schema evolution flexibility
4. Multi-tenancy requirements
5. Cloud-native managed service compatibility
6. Operational simplicity
7. Future analytics and ML needs

---

## 4. Decision

The platform will adopt a **polyglot persistence strategy**, where:

- Different storage technologies are used for different concerns
- Data ownership is clearly defined per service or domain
- No shared databases are accessed directly across service boundaries
- Integration occurs via APIs and events, not shared schemas

---

## 5. Data Ownership Model

### 5.1 Ownership Principle

Each service or domain module **owns its data**.

- The Node.js platform core owns platform metadata
- Python capability services own analytical and computational datasets
- Plugins may introduce their own data stores, scoped to their domain

No component directly reads or writes another component’s database.

---

### 5.2 Data Access Rules

- Cross-domain data access must occur via:
  - Public APIs, or
  - Domain events
- Direct database access across boundaries is prohibited

This enforces loose coupling and long-term maintainability.

---

## 6. Storage Technologies and Responsibilities

### 6.1 MongoDB (Platform Data Store)

**Used for:**
- Tenant configuration
- Plugin metadata and lifecycle state
- Feature flags
- Semi-structured domain data
- Platform-level operational data

**Rationale:**
- Schema flexibility aligns with evolving plugin models
- Natural fit for JSON-based configuration
- Rapid iteration without heavy migration overhead

---

### 6.2 PostgreSQL (Analytical and Structured Data)

**Used for:**
- Reporting and analytics
- Aggregations and historical analysis
- ML-ready datasets
- Strongly relational business data within Python services

**Rationale:**
- Strong consistency guarantees
- Mature analytical capabilities
- Compatibility with data science tooling

---

### 6.3 Redis (Ephemeral and Performance Data)

**Used for:**
- Caching
- Distributed locks
- Rate limiting
- Short-lived session or workflow state

**Rationale:**
- High performance
- Simple operational model
- Complements primary data stores

---

### 6.4 Object Storage

**Used for:**
- Files and documents
- Model artifacts
- Reports and exports
- Large, unstructured blobs

**Rationale:**
- Cost-effective
- Scales independently
- Avoids database misuse for binary data

---

## 7. Multi-Tenancy Strategy

### 7.1 Tenant Context Propagation

Tenant identity is established at the platform level and propagated via:

- JWT claims
- Request context
- Event metadata

Example:
```json
{
  "tenant_id": "tenant_123",
  "user_id": "user_456"
}
````

---

### 7.2 Tenant Isolation Approach

The platform adopts **logical tenant isolation**:

* Tenant identifiers included in all persisted records
* Indexing strategies optimized for tenant-based queries
* Physical isolation reserved for regulatory or high-risk cases

**Rationale:**

* Balances scalability and operational simplicity
* Avoids excessive infrastructure sprawl

---

## 8. Schema Evolution Strategy

### 8.1 MongoDB Schema Evolution

* Backward-compatible schema changes preferred
* Optional fields favored over breaking changes
* Plugin-owned collections evolve independently

---

### 8.2 Relational Schema Evolution

* Version-controlled migrations
* Forward-only migration strategy
* Rollbacks handled via compensating migrations

---

## 9. Data Integration and Events

### 9.1 Event as Integration Mechanism

Changes in one domain are communicated via events rather than shared tables.

Example:

```
USER_CREATED
ORDER_COMPLETED
PLUGIN_ENABLED
```

### 9.2 Benefits

* Decouples schemas
* Improves scalability
* Enables asynchronous processing
* Supports future service extraction

---

## 10. Data Consistency Model

The platform adopts a **mixed consistency approach**:

* Strong consistency within a service boundary
* Eventual consistency across services and plugins

**Rationale:**

* Supports scalability
* Avoids distributed transactions
* Aligns with cloud-native patterns

---

## 11. Backup, Retention, and Recovery

* Managed database backups enabled by default
* Retention policies defined per data class
* Recovery procedures tested periodically
* Object storage versioning enabled where applicable

---

## 12. Consequences

### Positive Consequences

* Flexibility across diverse workloads
* Clear data ownership boundaries
* Easier schema evolution
* Better performance characteristics
* Strong alignment with plugin architecture

### Negative Consequences

* Increased architectural discipline required
* More technologies to understand
* Eventual consistency adds complexity

---

## 13. Alternatives Considered

1. **Single database for all workloads**

   * Rejected due to performance and coupling risks

2. **Shared databases across services**

   * Rejected due to tight coupling and ownership ambiguity

3. **Strict physical tenant isolation**

   * Rejected due to operational and cost overhead in early stages

---

## 14. Decision Outcome

The platform adopts a **polyglot, ownership-driven persistence strategy** that aligns data storage technology with workload characteristics while preserving modularity and scalability.

---

## 15. Review & Revisit Criteria

This ADR should be revisited if:

* Data volume or access patterns change significantly
* Regulatory or compliance requirements evolve
* Tenant isolation requirements become stricter
* New data workloads emerge

---

**End of ADR**
