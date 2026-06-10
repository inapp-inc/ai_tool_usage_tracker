# ADR-007: AWS EKS Deployment Topology

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

The platform must achieve **99.5% monthly uptime** (NFR-AVL-001), support horizontal scaling to 200 concurrent users and ingestion bursts, and deploy via **Docker** as specified in `project.md`. Components include FastAPI API containers, Celery workers, Celery Beat, **PostgreSQL in Docker** (not RDS), Redis, and S3.

The team needs a production-grade deployment with Multi-AZ resilience, secrets management, and CI/CD via GitHub Actions without excessive operational burden.

---

## Decision

Deploy Phase 1 production on **Amazon EKS** with the following topology:

| Component | AWS Service |
|-----------|-------------|
| Compute | EKS (API + worker pods) |
| Load balancing | Application Load Balancer (ALB Ingress Controller) |
| Database | PostgreSQL 15 Docker container + persistent volume |
| Cache / broker | ElastiCache Redis (cluster mode) |
| Object storage | S3 (SSE-KMS encryption) |
| Secrets | AWS Secrets Manager + External Secrets Operator |
| Email | Amazon SES |
| Container registry | Amazon ECR |
| DNS | Route 53 |
| Static SPA | S3 + CloudFront (optional CDN) |

Network: VPC with public subnets (ALB, NAT) and private subnets (EKS nodes, Redis). PostgreSQL runs in Docker (Compose stack or co-located container), not in RDS subnets. No direct internet ingress to application or data tiers.

Environments: **dev**, **staging**, **production** with promotion via GitHub Actions.

---

## Consequences

### Positive

- EKS provides horizontal pod autoscaling for API and workers independently.
- Daily `pg_dump` from Docker PostgreSQL and volume snapshots meet backup targets (NFR-BKP-002).
- Managed services (ALB, S3, optional ElastiCache) reduce undifferentiated operational work where used.
- Aligns with cloud-native direction while remaining portable (Kubernetes manifests).
- VPC endpoints reduce data egress exposure for S3 and Secrets Manager.

### Negative

- EKS operational learning curve and cluster cost even at low scale.
- NAT Gateway costs in Multi-AZ VPC architecture.
- Vendor cloud coupling to AWS (acceptable per project direction; mitigated by Kubernetes portability).

### Neutral

- ECS/Fargate viable alternative on AWS; EKS chosen per project.md explicit mention of EKS.
- Multi-region DR deferred to Phase 2 optional PostgreSQL streaming replica + backup replication (NFR-BKP-002).

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **AWS ECS/Fargate** | Project mentions ECS/EKS; EKS chosen for Kubernetes ecosystem and HPA patterns documented in architecture. |
| **Single EC2 / VM deployment** | Does not meet horizontal scaling and HA requirements cleanly. |
| **On-premises Kubernetes** | Conflicts with AWS S3/ElastiCache direction where those are used; PostgreSQL remains Docker-based either way. |
| **Heroku / Render PaaS** | Insufficient control for enterprise HA, private networking, and compliance evidence. |
| **Serverless-only** | Poor fit for Celery workers and long-running ingestion (see ADR-004). |

**Supersedes:** None  
**Related:** ADR-001, ADR-004, ADR-010
