# ADR-0003: Deployment and Cloud Strategy

## Status
**Accepted**

## Date
2026-02-02

## Authors
Platform Architecture Team

---

## 1. Context

The platform architecture defined in:
- **ADR-0001 (MERN + Python Modular Platform Architecture)** and
- **ADR-0002 (Plugin and Extensibility Architecture)**

requires a deployment strategy that:

- Supports rapid development and iteration
- Minimizes operational complexity in early stages
- Remains cloud-ready and cloud-agnostic
- Scales incrementally without architectural rework
- Aligns with containerized, modular services
- Supports both Node.js platform services and Python capability services

The deployment approach must balance **developer velocity** with **production reliability**.

---

## 2. Problem Statement

Common deployment approaches introduce challenges at different stages:

- **VM-only deployments** limit scalability and reliability
- **Microservices-first deployments** introduce premature complexity
- **Kubernetes-first strategies** increase operational overhead and slow iteration
- **Environment-specific builds** cause drift and inconsistencies

The platform requires a **progressive deployment strategy** that:
- Uses the same artifacts across environments
- Starts simple and evolves when justified
- Avoids locking into a single cloud provider
- Supports independent scaling of platform and capability services

---

## 3. Decision Drivers

The deployment decision is influenced by:

1. Developer productivity
2. Operational simplicity
3. Cost efficiency
4. Cloud portability
5. Scalability without re-architecture
6. Reliability and fault isolation
7. CI/CD automation compatibility

---

## 4. Decision

The platform will adopt a **container-first, managed-infrastructure deployment strategy** with **progressive operational maturity**, defined in three phases:

1. **Containerization as the base requirement**
2. **Managed container platforms as the steady state**
3. **Kubernetes adoption only when operationally justified**

---

## 5. Containerization Strategy

### 5.1 Container-First Policy

All platform components must be packaged as containers:

- Node.js platform services
- Python capability services
- Background workers

**Rationale**
- Environment consistency
- Simplified CI/CD
- Cloud portability
- Reduced deployment friction

---

### 5.2 Stateless Containers

Containers must remain stateless:

- No local file storage
- No in-memory session persistence
- No environment-specific logic

All state is externalized to managed services.

---

## 6. Deployment Phases

### 6.1 Phase 1: Early Production Deployment

**Characteristics**
- Single virtual machine or small VM cluster
- Docker Compose orchestration
- Managed databases and caches

**Use Cases**
- Small teams
- Early-stage products
- Rapid iteration

**Benefits**
- Minimal operational overhead
- Fast setup
- Low cost

**Limitations**
- Manual scaling
- Limited fault isolation

---

### 6.2 Phase 2: Managed Container Platforms (Preferred Steady State)

**Target Platforms**
- AWS ECS (Fargate)
- Azure Container Apps / App Service
- Google Cloud Run

**Architecture**
```

Load Balancer
├── Node.js Platform Service
├── Python Capability Service(s)
└── Background Worker Service(s)

```

**Characteristics**
- Independent service scaling
- Rolling deployments
- Built-in health checks
- Managed networking

**Benefits**
- Production-grade reliability
- Reduced operational burden
- No cluster management
- Predictable cost model

This phase is considered the **default and recommended operational state**.

---

### 6.3 Phase 3: Kubernetes (When Justified)

Kubernetes may be adopted only if one or more of the following conditions are met:

- Multiple autonomous development teams
- High traffic with uneven scaling patterns
- Advanced deployment strategies (canary, blue-green)
- Complex service mesh requirements
- Regulatory or compliance-driven isolation needs

**Rationale**
- Kubernetes is a scaling tool, not a velocity tool
- Adoption should be driven by need, not convention

---

## 7. Cloud Provider Strategy

### 7.1 Cloud-Agnostic Design

The platform must remain cloud-agnostic by:
- Avoiding provider-specific APIs in application code
- Using standard container runtimes
- Externalizing infrastructure configuration

---

### 7.2 Managed Infrastructure Usage

The following components must use managed services where available:

| Concern | Strategy |
|------|--------|
| Databases | Managed relational / NoSQL |
| Caching | Managed Redis |
| Object storage | Cloud-native object storage |
| Queues / events | Managed messaging services |
| Secrets | Managed secrets manager |

**Rationale**
- Reduces operational burden
- Improves reliability
- Enables teams to focus on product development

---

## 8. CI/CD Strategy

### 8.1 CI/CD Principles

- Build once, deploy many times
- Immutable artifacts
- Automated testing before deployment
- Environment configuration via variables and secrets

---

### 8.2 Pipeline Stages

1. Source checkout
2. Static analysis and tests
3. Container image build
4. Image push to registry
5. Automated deployment

CI/CD tooling must remain replaceable and vendor-neutral.

---

## 9. Environment Parity

All environments (local, staging, production) must:

- Use the same container images
- Differ only by configuration
- Share the same runtime assumptions

**Rationale**
- Reduces deployment risk
- Improves reproducibility
- Simplifies debugging

---

## 10. Observability and Health Management

Each deployed service must provide:

- Health check endpoints
- Structured logs
- Correlation identifiers

Advanced observability (metrics, tracing, alerting) may be layered incrementally.

---

## 11. Consequences

### Positive Consequences
- Faster time to production
- Reduced operational complexity
- Clear scaling path
- Cloud portability
- Predictable deployment behavior

### Negative Consequences
- Some manual intervention in early phases
- Requires discipline to remain stateless
- Delayed access to advanced orchestration features until Kubernetes adoption

---

## 12. Alternatives Considered

1. **VM-only deployments**
   - Rejected due to scalability and reliability limitations

2. **Kubernetes-first approach**
   - Rejected due to operational overhead and reduced early velocity

3. **Platform-specific PaaS lock-in**
   - Rejected to preserve portability and flexibility

---

## 13. Decision Outcome

The platform adopts a **container-first, managed-infrastructure deployment strategy** with **progressive operational maturity**.

This approach ensures:
- Rapid early development
- Production readiness
- Minimal rework as scale increases

---

## 14. Review & Revisit Criteria

This ADR should be revisited if:
- Deployment scale increases significantly
- Operational complexity exceeds assumptions
- Regulatory or compliance requirements change
- Kubernetes adoption becomes necessary

---

**End of ADR**
