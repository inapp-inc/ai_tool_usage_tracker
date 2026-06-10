# Deployment Topology

**Phase 1 deployment:** **100% Docker Compose** on a VM or bare-metal host. All services and storage use **local Docker volumes** — no AWS EKS, S3, or ElastiCache.

Architecture diagrams below include optional AWS patterns **deferred to Phase 2**. Canonical operational spec: [deployment.md](../specifications/deployment.md).

**Stack alignment:** Docker Compose · PostgreSQL (Docker) · Redis (Docker) · Local volume storage · GitHub Actions CI/CD

---

## Docker Compose Stack (Database & Local/Staging)

PostgreSQL is **not** deployed on Amazon RDS. It runs as a Docker service with a named volume, on the same Docker network as the API and workers.

**Canonical specification:** [local-development.md](../specifications/local-development.md) (implemented in TASK-INF-001). **Full deployment spec:** [deployment.md](../specifications/deployment.md).

```mermaid
flowchart TB
    subgraph compose ["Docker Compose Network — ai-tracker-network"]
        API["FastAPI container<br/>ai-tracker-api"]
        WORKER["Celery worker<br/>ai-tracker-worker"]
        BEAT["Celery Beat<br/>ai-tracker-beat"]
        PG["postgres:15-alpine<br/>volume: ai-tracker-postgres-data"]
        REDIS["redis:7-alpine<br/>AOF enabled · DB 0/1/2"]
    end

    API --> PG
    API --> REDIS
    WORKER --> PG
    WORKER --> REDIS
    BEAT --> REDIS
```

| Implementation detail | Value |
|-----------------------|-------|
| Compose file | `docker-compose.yml` (repository root) |
| Backend source | `backend/` |
| Interim health probe | `GET /health` (migrates to `/api/v1/health` in TASK-INF-002) |
| Env template | `.env.example` |

See [database.md](./database.md#docker-deployment) for PostgreSQL backups (`pg_dump`), sizing, and connection settings.

---

## Phase 1 Production Topology (Docker Compose)

All staging and production workloads run on a **Docker host** using Compose (see [deployment.md](../specifications/deployment.md), ADR-013):

```mermaid
flowchart TB
    subgraph host ["Docker Host"]
        subgraph network ["ai-tracker-network"]
            PROXY["nginx<br/>TLS · routing"]
            FE["frontend<br/>React static"]
            API["api × N replicas"]
            WORKER["worker × N"]
            BEAT["beat × 1"]
            PG["postgres"]
            REDIS["redis"]
            PROM["prometheus"]
            GRAF["grafana"]
        end
        VOL_PG[("postgres_data")]
        VOL_STORE[("storage_data")]
        VOL_BACKUP[("backups_data")]
    end

    USERS["Users"] --> PROXY
    PROXY --> FE
    PROXY --> API
    API --> PG
    API --> REDIS
    API --> VOL_STORE
    WORKER --> PG
    WORKER --> REDIS
    WORKER --> VOL_STORE
    PG --> VOL_PG
```

| Setting | Production |
|---------|------------|
| Compose files | `docker-compose.yml` + `docker-compose.prod.yml` |
| Secrets | Host `.env` or Compose `secrets:` |
| Backups | Daily `pg_dump` → `backups_data` volume + off-host rsync |
| Frontend | `frontend` + `nginx` containers — not S3/CloudFront |

---

## Phase 2 — AWS Cloud Topology (Deferred)

> The diagrams below describe an **optional Phase 2** migration path. **Do not implement for Phase 1 MVP.** Superseded for Phase 1 by [ADR-013](../decisions/ADR-013-docker-compose-local-storage.md).

## Production Deployment Topology (Phase 2 reference)

```mermaid
flowchart TB
    subgraph internet ["Internet"]
        USERS["Users - Browser"]
    end

    subgraph aws ["AWS Cloud - Region: configurable"]
        subgraph edge_aws ["Edge"]
            R53["Route 53<br/>DNS"]
            CF["CloudFront<br/>Static SPA - optional"]
            ALB["Application Load Balancer<br/>HTTPS · WAF optional"]
        end

        subgraph vpc ["VPC 10.0.0.0/16"]
            subgraph public_subnet ["Public Subnets - Multi-AZ"]
                NAT["NAT Gateway"]
                ALB_NODE["ALB Nodes"]
            end

            subgraph app_subnet ["Private Subnets - Application - Multi-AZ"]
                EKS["Amazon EKS Cluster"]
                API_PODS["FastAPI Pods<br/>min 2 · HPA max 10"]
                WORK_PODS["Celery Worker Pods<br/>min 2 · HPA per queue"]
                BEAT_POD["Celery Beat Pod<br/>replicas=1 leader"]
                OTEL_COL["OTel Collector DaemonSet"]
            end

            subgraph data_subnet ["Data Tier - Docker"]
                POSTGRES["PostgreSQL 15<br/>Docker · persistent volume"]
                ELASTIC["Redis<br/>Docker or ElastiCache"]
            end

            subgraph endpoints ["VPC Endpoints"]
                S3_EP["S3 Gateway Endpoint"]
                SM_EP["Secrets Manager Interface"]
                ECR_EP["ECR Interface"]
            end
        end

        S3["Amazon S3<br/>uploads · reports"]
        SM["Secrets Manager"]
        SES["Amazon SES<br/>Email"]
        ECR["Amazon ECR<br/>Container Images"]
        CW["CloudWatch Logs<br/>optional aggregation"]
    end

    subgraph cicd ["CI/CD"]
        GHA["GitHub Actions"]
    end

    USERS --> R53
    R53 --> CF
    R53 --> ALB
    CF --> S3
    ALB --> ALB_NODE
    ALB_NODE --> API_PODS

    API_PODS --> POSTGRES
    API_PODS --> ELASTIC
    API_PODS --> S3_EP
    WORK_PODS --> POSTGRES
    WORK_PODS --> ELASTIC
    WORK_PODS --> S3_EP
    WORK_PODS --> SES
    BEAT_POD --> ELASTIC

    API_PODS --> SM_EP
    WORK_PODS --> SM_EP
    S3_EP --> S3
    SM_EP --> SM

    EKS --> ECR_EP
    ECR_EP --> ECR
    GHA --> ECR
    GHA --> EKS

    API_PODS --> OTEL_COL
    WORK_PODS --> OTEL_COL
    OTEL_COL --> CW
```

---

## Kubernetes Workload Layout

```mermaid
flowchart TB
    subgraph eks ["EKS Namespace: ai-tracker-prod"]
        subgraph deploy_api ["Deployment: api"]
            API1["Pod api-xxx"]
            API2["Pod api-yyy"]
        end

        subgraph deploy_worker ["Deployment: celery-worker"]
            W1["Pod worker-ingest"]
            W2["Pod worker-reports"]
        end

        subgraph deploy_beat ["Deployment: celery-beat"]
            B1["Pod beat - replicas 1"]
        end

        subgraph svc ["Services"]
            SVC_API["Service api ClusterIP port 8000"]
        end

        subgraph ingress ["Ingress"]
            ING["AWS Load Balancer Controller<br/>Ingress resource"]
        end

        subgraph config ["Config"]
            CM["ConfigMap<br/>non-secret config"]
            ES["External Secrets<br/>JWT · DB · SMTP"]
        end
    end

    ING --> SVC_API
    SVC_API --> API1
    SVC_API --> API2
    API1 --> CM
    API1 --> ES
    W1 --> ES
```

### Pod Resource Baselines (Starting Point)

| Workload | CPU Request | Memory Request | Replicas |
|----------|-------------|----------------|----------|
| FastAPI | 500m | 512Mi | 2–10 (HPA) |
| Celery ingestion | 1000m | 1Gi | 2–6 (HPA) |
| Celery reports | 1000m | 2Gi | 1–4 (HPA) |
| Celery beat | 100m | 256Mi | 1 |

HPA triggers: CPU >70%, or custom metric `celery_queue_depth` >500.

---

## Network Topology

```mermaid
flowchart LR
    subgraph az_a ["Availability Zone A"]
        PUB_A["Public subnet"]
        APP_A["App private subnet"]
        DATA_A["Data private subnet"]
    end

    subgraph az_b ["Availability Zone B"]
        PUB_B["Public subnet"]
        APP_B["App private subnet"]
        DATA_B["Data private subnet"]
    end

    IGW["Internet Gateway"] --> PUB_A
    IGW --> PUB_B
    PUB_A --> NAT
    PUB_B --> NAT
    NAT --> APP_A
    NAT --> APP_B
    APP_A --> DATA_A
    APP_B --> DATA_B
```

### Security Groups (Summary)

| Source | Target | Port | Purpose |
|--------|--------|------|---------|
| ALB SG | API pods SG | 8000 | HTTP to FastAPI |
| API pods SG | PostgreSQL host / Docker network | 5432 | PostgreSQL container |
| API/Worker SG | Redis SG | 6379 | Cache + broker |
| API/Worker SG | S3 endpoint | 443 | Object storage |
| EKS nodes | ECR endpoint | 443 | Image pull |

No direct internet ingress to application or data subnets (NFR-SEC-002).

---

## Environment Topology

```mermaid
flowchart TB
    subgraph envs ["Environments"]
        DEV["Development<br/>single AZ · smaller instances"]
        STAGE["Staging<br/>production-like · anonymized data"]
        PROD["Production<br/>Multi-AZ · HA"]
    end

    DEV --> STAGE
    STAGE -->|GitHub Actions promote| PROD
```

| Environment | App runtime | PostgreSQL | Redis | Storage | Purpose |
|-------------|-------------|------------|-------|---------|---------|
| Development | Docker Compose | `postgres:15-alpine` + volume | `redis:7-alpine` + volume | Local volume | Local feature development |
| Staging | Docker Compose | PostgreSQL Docker + volume | Redis Docker + volume | Local volume | Integration / load test |
| Production | Docker Compose | PostgreSQL Docker + volume (not RDS) | Redis Docker + volume | Local volume | Live workloads |

Credential environments (sandbox vs production) are **logical** separation within Administration (FR-ADM-003), distinct from deployment environments.

---

## CI/CD Pipeline Topology

```mermaid
flowchart LR
    subgraph gh ["GitHub"]
        CODE["Source Code"]
        PR["Pull Request"]
    end

    subgraph gha ["GitHub Actions"]
        LINT["Lint · Type Check"]
        TEST["Unit · Integration Tests"]
        SAST["Dependency Scan · Bandit"]
        BUILD["Docker Build"]
        PUSH["Push to ECR"]
        DEPLOY_STG["Deploy Staging"]
        DEPLOY_PROD["Deploy Production<br/>manual approval"]
    end

    subgraph k8s ["EKS"]
        ROLL["Rolling Update<br/>maxUnavailable 0"]
        HEALTH["Readiness Probe Gate"]
    end

    CODE --> PR
    PR --> LINT --> TEST --> SAST
    SAST --> BUILD --> PUSH
    PUSH --> DEPLOY_STG --> DEPLOY_PROD
    DEPLOY_PROD --> ROLL --> HEALTH
```

### Deployment Strategy

- **Rolling update** with readiness probes (NFR-AVL-004)
- **Database migrations** via init job or Alembic job before traffic shift
- **Feature flags** for risky features (optional P1)
- **Rollback:** Kubernetes rollout undo; DB migrations require backward-compatible changes (OpenSpec principle)

---

## High Availability and DR

```mermaid
flowchart TB
    subgraph primary ["Primary Deployment"]
        APP_P["App containers<br/>API · Workers"]
        PG_P["PostgreSQL Docker<br/>postgres_data volume"]
        S3_P["S3 Standard"]
    end

    subgraph dr ["DR - Phase 2 optional"]
        PG_R["PostgreSQL streaming replica container"]
        S3_R["S3 Cross-Region Replication"]
    end

    subgraph backup ["Backup"]
        DUMP["pg_dump daily to local volume"]
        WAL["WAL archiving optional PITR"]
    end

    PG_P --> DUMP
    PG_P --> WAL
    PG_P -.->|optional| PG_R
    S3_P -.->|optional| S3_R
```

| Objective | Target | Mechanism |
|-----------|--------|-----------|
| RPO | ≤ 24h (daily dump) | Local `backups_data` volume + off-host rsync |
| RTO | ≤ 4 hours | Restore dump + storage tarball on new Docker host |
| API container failure | ≤ 5 min | Docker restart + healthcheck |
| Monthly uptime | ≥ 99.5% | Multi-replica API/worker containers + volume backups |

---

## Observability Deployment

```mermaid
flowchart LR
    PODS["API + Worker Pods"] -->|OTLP| COL["OTel Collector"]
    COL --> PROM["Prometheus<br/>Amazon Managed or self-hosted"]
    PROM --> GRAF["Grafana"]
    COL --> LOGS["CloudWatch / Loki"]
    PROM --> ALERT["Alertmanager<br/>PagerDuty / Slack"]
```

Key dashboards: API latency p95, error rate, Celery queue depth, PostgreSQL connections, Redis memory, ingestion throughput.

---

## Static Frontend Delivery (Phase 1)

| Pattern | Description | Phase 1 |
|---------|-------------|---------|
| **A: frontend + nginx containers** | React build in `frontend` image; `nginx` reverse proxy | **Used** |
| **B: Embedded in API** | FastAPI serves static build | Dev only |
| ~~C: S3 + CloudFront~~ | ~~CDN static hosting~~ | **Deferred Phase 2** |

---

## Cost Optimization (Phase 1 Docker host)

| Resource | Optimization |
|----------|--------------|
| Docker host | Right-size CPU/RAM/disk for Postgres + storage volumes |
| PostgreSQL | Tune container resources; daily pg_dump to local backup volume |
| Local storage | Monitor disk usage; retention jobs purge old uploads/reports |
| Redis | Single container with AOF volume; scale vertically if needed |

---

## Deployment Checklist (MVP Go-Live)

See [deployment-checklist.md](../specifications/deployment-checklist.md). Summary:

- [ ] Docker host with dedicated disk for volumes
- [ ] `docker compose -f docker-compose.yml -f docker-compose.prod.yml up` healthy
- [ ] PostgreSQL + Redis + storage + backup volumes provisioned
- [ ] Host `.env` secured (`chmod 600`); no secrets in Git
- [ ] Daily backup job to `backups_data` volume
- [ ] nginx TLS + frontend container routing
- [ ] OpenTelemetry + Prometheus + Grafana Compose profile
- [ ] GitHub Actions deploy pipeline to Compose host
- [ ] DR restore drill documented (NFR-BKP-005)

<!--
## Phase 2 AWS Checklist (Deferred)

- [ ] EKS cluster with node groups and ALB ingress controller
- [ ] ElastiCache Redis cluster
- [ ] S3 buckets with encryption, versioning, lifecycle rules
- [ ] Secrets Manager entries + External Secrets Operator
-->
