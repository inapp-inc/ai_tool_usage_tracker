# Architecture & Design Patterns (Reference Library)

**Purpose:** A reusable reference that the **design step** must consult. It enumerates the major architecture and design patterns commonly applicable in product work, explains each pattern, and provides quick selection heuristics and failure modes.

**How to use in a design pass:**

1. Identify the **drivers** (scale, change rate, reliability, latency, team topology, compliance, data consistency, time-to-market).
2. For each driver, shortlist candidate patterns below.
3. Record: **chosen patterns**, **rejected patterns** (and why), and any **guardrails** (constraints, ADRs, non-goals).

---

## 1) Architectural styles (system-level structure)

### Layered (N-tier)
- **What it is**: Separate concerns into layers (e.g., UI → application/service → domain → data access). Dependencies flow “down”.
- **Use when**: You want simple structure, predictable dependencies, and broad team familiarity.
- **Watch outs**: “Business logic in controllers”, leaky abstractions, overly chatty layers, anemic domain model.

### Modular monolith
- **What it is**: One deployable unit, but **strict internal module boundaries** (no cross-module database tables/collections, clear APIs between modules).
- **Use when**: You need speed, simpler ops, and bounded complexity; likely precursor to service extraction.
- **Watch outs**: Modules becoming spaghetti due to weak boundaries; shared “utils” becoming a dumping ground.

### Microservices
- **What it is**: Independently deployable services with explicit contracts, separate data ownership, and operational isolation.
- **Use when**: Team autonomy and independent scaling/deployments are worth the operational cost; clear bounded contexts exist.
- **Watch outs**: Distributed transactions, observability burden, versioning/compatibility, network failure modes, duplicated logic.

### Service-oriented “capability services”
- **What it is**: Focused services for cross-cutting capabilities (e.g., analytics, ML inference) consumed by the core system.
- **Use when**: Specialized runtime/stack needs (GPU, Python stack), or heavy workloads that shouldn’t live in the core app.
- **Watch outs**: Hidden coupling via shared schemas, backpressure issues, unclear ownership.

### Event-driven architecture (EDA)
- **What it is**: Components communicate via events; producers publish facts, consumers react asynchronously.
- **Use when**: You need loose coupling, async workflows, auditability, and independent evolution of consumers.
- **Watch outs**: Event schema evolution, eventual consistency, debugging complexity, duplicate delivery handling.

### Hexagonal / Ports & Adapters
- **What it is**: The domain/application core defines “ports” (interfaces). External systems (DB, HTTP, queues) are “adapters”.
- **Use when**: You want testability, substitutable infrastructure, and strict separation of domain logic from IO.
- **Watch outs**: Over-abstraction for tiny apps; too many layers if boundaries aren’t meaningful.

### Clean Architecture
- **What it is**: Concentric boundaries: entities/domain in the center; use-cases/application around it; frameworks/IO on the outside. Dependencies always point inward.
- **Use when**: You need long-lived domain logic insulated from frameworks, and strong test seams.
- **Watch outs**: Over-ceremonial design; “DTO explosion” if not managed.

### Domain-Driven Design (DDD)
- **What it is**: Model the domain using ubiquitous language; define bounded contexts; use aggregates/entities/value objects where useful.
- **Use when**: The domain is complex, rules-heavy, and shared understanding is critical.
- **Watch outs**: Cargo-culting DDD terms; overcomplicating simple CRUD; unclear boundaries.

---

## 2) Module and component patterns (within a service/app)

### MVC / Thin controllers
- **What it is**: Controllers handle transport (HTTP), delegate to services/use-cases; domain logic stays out of controllers.
- **Use when**: Standard web apps where clarity and separation help.
- **Watch outs**: Fat controllers, business logic leaking into routing/middleware.

### Use-case / Application service layer
- **What it is**: A layer that coordinates domain and IO for a specific “user intent” (create task, pay invoice).
- **Use when**: Workflows span multiple repositories/integrations; you need a clear place for orchestration.
- **Watch outs**: Turning into a “god service”; unclear transaction boundaries.

### Repository (Data Access Layer)
- **What it is**: Abstract persistence behind an interface (e.g., `TaskRepository`). Domain/app code doesn’t speak database directly.
- **Use when**: You want test seams, consistent query policies (tenant isolation), or multiple persistence backends.
- **Watch outs**: Leaking query language into the interface; repositories returning persistence models not domain models.

### Unit of Work (UoW)
- **What it is**: A pattern to group multiple changes into one atomic commit/transaction boundary.
- **Use when**: Multiple writes must succeed or fail together.
- **Watch outs**: Forcing transactions across boundaries; hiding expensive transactions.

### Dependency Injection (DI)
- **What it is**: Dependencies are provided from the outside, often via constructors or factories.
- **Use when**: You want testability and swap-able implementations.
- **Watch outs**: Container complexity; runtime wiring errors if not validated.

---

## 3) Behavioral OO design patterns (local code structure)

### Strategy
- **What it is**: Encapsulate interchangeable algorithms behind a common interface.
- **Use when**: Business rules vary by tenant, feature flag, plan, region, or version.
- **Watch outs**: Too many tiny strategies; unclear selection logic.

### Factory / Abstract Factory
- **What it is**: Centralize object creation and selection of concrete implementations.
- **Use when**: Construction is non-trivial, environment-dependent, or you must choose among implementations.
- **Watch outs**: Factories hiding excessive logic; global factories acting like service locators.

### Adapter
- **What it is**: Wrap an external API/client to match an internal interface.
- **Use when**: Integrations differ from your desired abstraction; you want to isolate vendor specifics.
- **Watch outs**: Adapters becoming leaky; mixing mapping + business logic.

### Facade
- **What it is**: Provide a simpler interface over a complex subsystem.
- **Use when**: You want to reduce call-site complexity and stabilize dependencies.
- **Watch outs**: Facade becoming a dumping ground / god object.

### Decorator
- **What it is**: Add behavior to an object without modifying its code (composition over inheritance).
- **Use when**: Cross-cutting concerns (caching, tracing, retries) should be layered.
- **Watch outs**: Order-of-operations bugs; hard-to-follow stacks of decorators.

### Observer / Publish–Subscribe (in-process)
- **What it is**: Notify subscribers when state changes (events/callbacks).
- **Use when**: Decoupling components in a UI or within a process.
- **Watch outs**: Memory leaks, implicit control flow, hard-to-test reactive chains.

### Command
- **What it is**: Encapsulate a request as an object (`execute()`), often enabling retries, queuing, or undo.
- **Use when**: You have workflows that need persistence, scheduling, or consistent execution semantics.
- **Watch outs**: Excess ceremony for simple operations.

---

## 4) Integration & API patterns (between systems)

### API-first / Contract-first (OpenAPI)
- **What it is**: Define API contracts before or alongside implementation; generate types/stubs where possible.
- **Use when**: Multiple clients/teams integrate; you want compatibility and testable contracts.
- **Watch outs**: Contract drift; unclear versioning strategy.

### Aggregator (API composition)
- **What it is**: A component (often an API endpoint/service) that **aggregates** data from multiple sources/services and returns a single, client-friendly response. This reduces client chattiness and centralizes composition.
- **Use when**: A UI/page needs data from multiple domains; you want consistent composition, caching, and authorization in one place; network latency makes multiple round-trips expensive.
- **Watch outs**: Becoming a “god endpoint” that embeds business rules; N+1 fan-out calls; unclear ownership (is it a BFF or a domain service?); caching/consistency pitfalls; partial failure handling (timeouts, fallbacks).

### BFF (Backend For Frontend)
- **What it is**: A backend tailored to a specific UI/client, aggregating data and shaping responses.
- **Use when**: UI needs differ by channel; you want to reduce client complexity and chattiness.
- **Watch outs**: Duplicating business logic; unclear ownership between BFF and core services.

### API Gateway
- **What it is**: Central entry point for routing, auth, rate limits, request shaping, and observability.
- **Use when**: Many services exist, you need uniform edge policies.
- **Watch outs**: “Smart gateway” accumulating business logic; single point of failure if not resilient.

### Anti-corruption layer (ACL)
- **What it is**: A boundary layer that prevents external models from polluting your domain model.
- **Use when**: Integrating with legacy/3rd-party systems with incompatible concepts.
- **Watch outs**: Under-investing leads to model leakage and brittle code.

---

## 4a) Migration & modernization patterns

### Strangler Fig
- **What it is**: Incrementally replace parts of a legacy system by routing a subset of traffic/paths to a new implementation, expanding over time until the old path can be removed.
- **Use when**: You need to modernize without a “big bang” rewrite; you can carve functionality by route/module; you want continuous delivery during migration.
- **Watch outs**: Split-brain behavior if contracts aren’t aligned; data migration complexity; duplicated logic; unclear end-state; routing/observability gaps; integration tests must cover both old and new paths during transition.

## 5) Data & consistency patterns

### CQRS (Command Query Responsibility Segregation)
- **What it is**: Separate write model (commands) from read model (queries), optionally with different storage.
- **Use when**: Read and write workloads differ significantly; complex queries; scalability demands.
- **Watch outs**: Complexity; eventual consistency; duplication of models.

### Event Sourcing
- **What it is**: Store state as an append-only stream of events; derive current state via replay/projection.
- **Use when**: You need strong auditability, temporal queries, or complex business invariants.
- **Watch outs**: Event evolution, replay cost, operational complexity; requires mature tooling.

### Saga (distributed workflow)
- **What it is**: Coordinate multi-step operations across services using a sequence of local transactions with compensations.
- **Use when**: Multi-service workflows need reliable completion without distributed transactions.
- **Watch outs**: Compensations are hard; partial failure cases; timeouts and idempotency.

### Transactional Outbox
- **What it is**: Persist domain changes and outgoing messages/events in one DB transaction; publish from outbox asynchronously.
- **Use when**: You must avoid “DB commit succeeded but event publish failed” inconsistencies.
- **Watch outs**: Requires publisher polling and dedupe; outbox growth management.

### Idempotency keys
- **What it is**: Clients supply a key so retries don’t duplicate effects.
- **Use when**: Payments, task creation, any operation where retries are common.
- **Watch outs**: Key storage/TTL; defining “same request” equivalence.

### Optimistic concurrency (ETags/version fields)
- **What it is**: Detect conflicting writes by checking a version on update.
- **Use when**: Concurrent updates are possible and you need conflict detection without locks.
- **Watch outs**: Handling conflicts in UX/API; ensuring version bumps are correct.

---

## 6) Reliability & resiliency patterns

### Retry with backoff + jitter
- **What it is**: Retry transient failures with increasing delays and randomness.
- **Use when**: Network calls and transient dependencies.
- **Watch outs**: Retry storms; retrying non-idempotent operations without idempotency.

### Timeout budgeting
- **What it is**: Explicit timeouts at each boundary to prevent resource exhaustion.
- **Use when**: Any remote call; user-facing latency constraints.
- **Watch outs**: Cascading failures if timeouts are inconsistent.

### Circuit breaker
- **What it is**: Stop calling a failing dependency temporarily to allow recovery.
- **Use when**: Unreliable external services; to reduce load and improve tail latency.
- **Watch outs**: Tuning thresholds; fallbacks must be correct.

### Bulkhead
- **What it is**: Isolate resources so one dependency can’t consume everything.
- **Use when**: Mixed workloads; protecting critical paths.
- **Watch outs**: Capacity planning; increased operational knobs.

### Rate limiting / throttling
- **What it is**: Limit requests to protect services and tenants.
- **Use when**: Multi-tenant systems, public APIs, or expensive endpoints.
- **Watch outs**: Fairness across tenants; communicating limits to clients.

---

## 7) Security & multi-tenancy patterns

### Defense in depth
- **What it is**: Multiple layers of controls (authn, authz, validation, logging, secure defaults).
- **Use when**: Always.
- **Watch outs**: Gaps created by assuming a single control is enough.

### RBAC / ABAC
- **What it is**: Role-based access control vs attribute-based policies.
- **Use when**: RBAC for simpler role models; ABAC for fine-grained, contextual rules.
- **Watch outs**: Permission sprawl; policy complexity; auditability.

### Tenant isolation (data partitioning)
- **What it is**: Enforce tenant/user constraints at every query boundary; optionally separate DB/schema per tenant.
- **Use when**: Multi-tenant or “per user” isolation requirements.
- **Watch outs**: Forgetting filters; authorization checks after the fact; leakage through caches/logging.

---

## 8) Observability patterns (operability by design)

### Structured logging + correlation IDs
- **What it is**: Machine-parseable logs with request IDs propagated across boundaries.
- **Use when**: Always for non-trivial systems; essential for distributed workflows.
- **Watch outs**: Logging secrets/PII; missing correlation propagation.

### Metrics + SLOs
- **What it is**: Quantitative signals (latency, error rate, saturation) with targets.
- **Use when**: Reliability matters; you need to manage performance over time.
- **Watch outs**: Measuring too much but acting on too little; ignoring cardinality costs.

### Tracing (distributed traces)
- **What it is**: End-to-end timing across services/components.
- **Use when**: Microservices, async workflows, or performance investigation.
- **Watch outs**: Sampling gaps; cost; missing instrumentation in critical spans.

---

## 9) Quick selection checklist (copy into design docs)

Use this as a **“considered patterns”** section. Keep it short but explicit.

- **Architecture style considered**: Layered / Modular monolith / Microservices / Hexagonal / Clean / DDD / EDA
  - **Chosen**: …
  - **Rejected**: … (why)
- **Integration**: OpenAPI-first / BFF / Gateway / ACL
  - **Chosen**: …
  - **Rejected**: …
- **Aggregation/composition**: Aggregator (API composition)
  - **Chosen**: …
  - **Rejected**: …
- **Migration/modernization**: Strangler Fig
  - **Chosen**: …
  - **Rejected**: …
- **Data & consistency**: Repository/UoW / CQRS / Event sourcing / Saga / Outbox / Idempotency / Optimistic concurrency
  - **Chosen**: …
  - **Rejected**: …
- **Reliability**: Retries / Timeouts / Circuit breaker / Bulkheads / Rate limits
  - **Chosen**: …
  - **Rejected**: …
- **Security**: RBAC/ABAC / Tenant isolation / Defense in depth
  - **Chosen**: …
  - **Rejected**: …

