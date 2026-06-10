# ADR-013: Docker Compose Deployment with Local Volume Storage

**Status:** Accepted  
**Date:** 2026-06-10  
**Supersedes (Phase 1):** [ADR-007](./ADR-007-aws-eks-deployment.md) (compute/deployment), [ADR-009](./ADR-009-s3-object-storage-ingestion.md) (object storage)

---

## Context

Phase 1 MVP deployment must be **fully containerized on Docker** with **local persistent storage** on the host. The product owner requires:

- All services (API, workers, Beat, PostgreSQL, Redis, frontend, proxy, observability) run as **Docker containers**.
- File uploads, generated reports, and backups stored on **local Docker volumes** — not Amazon S3, MinIO cloud, or other remote object stores.
- No dependency on AWS EKS, ElastiCache, CloudFront, or Secrets Manager for Phase 1 go-live.

ADR-007 (EKS) and ADR-009 (S3) remain valid as **Phase 2 cloud migration options** but do **not** apply to Phase 1 implementation.

---

## Decision

Deploy **development, staging, and production** using **Docker Compose** on a VM or bare-metal host:

| Component | Implementation |
|-----------|----------------|
| Compute | Docker Compose services (`api`, `worker`, `beat`, …) |
| Database | `postgres:15-alpine` + volume `ai-tracker-postgres-data` |
| Cache / broker | `redis:7-alpine` + volume `ai-tracker-redis-data` |
| Object storage | **Local filesystem** via volume `ai-tracker-storage-data` mounted at `/var/lib/ai-tracker/storage` |
| Backups | Volume `ai-tracker-backups-data` (`pg_dump`, storage tarballs) |
| Frontend | `frontend` container (nginx static) + `nginx` reverse proxy |
| Secrets | Host `.env` (gitignored) or Docker Compose `secrets:` |
| CI/CD | GitHub Actions → build images → `docker compose up` on target host |
| Observability | Prometheus, Grafana, OTel Collector as Compose services |

**Storage adapter:** application uses `STORAGE_BACKEND=local` with `LOCAL_STORAGE_ROOT` (see [deployment.md](../specifications/deployment.md)).

Production hardening via `docker-compose.prod.yml` (no published DB/Redis ports, TLS, Redis AUTH, resource limits).

---

## Consequences

### Positive

- Single operational model across all environments.
- No cloud account or egress costs for Phase 1.
- Simpler local debugging — same Compose stack everywhere.
- Backups via local volumes + optional off-host `rsync`.

### Negative

- Manual host scaling (add replicas on same host or second host) vs Kubernetes HPA.
- Local disk becomes single point of failure — mitigated by off-host backup copies.
- No presigned S3 URLs — downloads served via API or nginx from local paths.

### Neutral

- ADR-007 and ADR-009 preserved for future cloud migration ADR.
- Kubernetes manifests deferred.

---

## Alternatives

| Alternative | Why Not Chosen (Phase 1) |
|-------------|--------------------------|
| **Amazon EKS (ADR-007)** | Deferred; owner requires Docker Compose only for Phase 1. |
| **Amazon S3 (ADR-009)** | Deferred; owner requires local volume storage. |
| **MinIO container** | Unnecessary when native filesystem adapter suffices. |
| **Bind mounts only** | Named volumes preferred for portability; bind mounts optional for dev. |

**Related:** ADR-001, ADR-003, ADR-004, ADR-010, [deployment.md](../specifications/deployment.md)
