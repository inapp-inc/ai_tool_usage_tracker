# Component Diagram

Logical and physical component views for the AI Tool Usage Tracker.

**Phase 1 runtime:** All components below deploy as **Docker Compose services** on a single host (ADR-013). Object storage is a **local volume**, not S3.

---

## Logical Component Diagram

High-level application components and their relationships.

```mermaid
flowchart TB
    subgraph clients ["Clients"]
        WEB["Web Browser<br/>React SPA"]
    end

    subgraph edge ["Edge Layer - Docker"]
        PROXY["nginx<br/>TLS Termination"]
        FE["frontend<br/>React SPA static"]
    end

    subgraph app ["Application Tier - Docker Compose"]
        API["FastAPI Application<br/>Modular Monolith"]
        WORKER["Celery Workers<br/>Ingestion · Reports · Alerts"]
        BEAT["Celery Beat<br/>Scheduled Jobs"]
    end

    subgraph modules ["FastAPI Domain Modules"]
        M_AUTH["Identity & Access"]
        M_ADMIN["Administration"]
        M_INGEST["Ingestion"]
        M_USAGE["Usage Tracking"]
        M_DASH["Analytics & Dashboard"]
        M_RPT["Reporting"]
        M_NTF["Notifications"]
        M_AUDIT["Audit"]
    end

    subgraph data ["Data Tier"]
        PG[("PostgreSQL<br/>Docker container")]
        REDIS[("Redis<br/>Cache · Broker")]
        STORE_LOCAL[("Local Volume<br/>uploads · reports")]
    end

    subgraph external ["External Systems"]
        SMTP["Email Provider<br/>SMTP"]
        ENV["Host .env / Compose secrets<br/>JWT · DB · Encryption Keys"]
        VENDOR["AI Vendor APIs<br/>Phase 2 sync"]
    end

    subgraph observability ["Observability"]
        OTEL["OpenTelemetry Collector"]
        PROM["Prometheus"]
        GRAF["Grafana"]
    end

    WEB --> PROXY
    PROXY --> FE
    PROXY -->|HTTPS REST| API

    API --> M_AUTH
    API --> M_ADMIN
    API --> M_INGEST
    API --> M_USAGE
    API --> M_DASH
    API --> M_RPT
    API --> M_NTF
    API --> M_AUDIT

    API --> PG
    API --> REDIS
    API --> STORE_LOCAL
    API -->|enqueue| REDIS

    WORKER --> PG
    WORKER --> REDIS
    WORKER --> STORE_LOCAL
    WORKER --> SMTP
    BEAT --> REDIS

    M_ADMIN --> ENV
    M_INGEST --> STORE_LOCAL
    M_USAGE --> PG
    WORKER -.->|future| VENDOR

    API --> OTEL
    WORKER --> OTEL
    OTEL --> PROM
    PROM --> GRAF
```

---

## FastAPI Internal Module Structure

```mermaid
flowchart TB
    subgraph api_layer ["API Layer - Routers"]
        R_AUTH["/auth"]
        R_TOOLS["/tools"]
        R_TEAMS["/teams"]
        R_KEYS["/credentials"]
        R_THRESH["/thresholds"]
        R_UPLOAD["/uploads"]
        R_DASH["/dashboard"]
        R_REPORTS["/reports"]
        R_NOTIF["/notifications"]
        R_AUDIT["/audit-logs"]
    end

    subgraph app_layer ["Application Layer - Use Cases"]
        UC_AUTH["AuthenticateUser<br/>AuthorizeAction"]
        UC_ADMIN["ManageTool<br/>ManageTeam<br/>ManageCredential"]
        UC_INGEST["UploadFile<br/>PreviewImport<br/>ProcessImport"]
        UC_USAGE["RecordUsage<br/>AggregateUsage<br/>CalculateCost"]
        UC_DASH["GetWidgetData"]
        UC_RPT["GenerateReport<br/>ScheduleReport"]
        UC_NTF["EvaluateThresholds<br/>SendNotification"]
        UC_AUDIT["RecordAuditEvent"]
    end

    subgraph domain_layer ["Domain Layer"]
        D_TOOL["Tool · PricingModel"]
        D_TEAM["Team · Membership"]
        D_USAGE["UsageEvent · Aggregate"]
        D_THRESH["Threshold · Alert"]
        D_NOTIF["Notification"]
    end

    subgraph infra_layer ["Infrastructure Adapters"]
        REPO["PostgreSQL Repositories"]
        CACHE["Redis Cache Adapter"]
        STORE["Local Storage Adapter<br/>filesystem volume"]
        PARSER["Vendor Parser Adapters<br/>OpenAI · Anthropic · Azure · Cursor"]
        MAIL["Email Adapter"]
        CRYPTO["Encryption Adapter<br/>AES-256"]
    end

    R_AUTH --> UC_AUTH
    R_TOOLS --> UC_ADMIN
    R_TEAMS --> UC_ADMIN
    R_KEYS --> UC_ADMIN
    R_THRESH --> UC_ADMIN
    R_UPLOAD --> UC_INGEST
    R_DASH --> UC_DASH
    R_REPORTS --> UC_RPT
    R_NOTIF --> UC_NTF
    R_AUDIT --> UC_AUDIT

    UC_ADMIN --> D_TOOL
    UC_ADMIN --> D_TEAM
    UC_INGEST --> PARSER
    UC_INGEST --> UC_USAGE
    UC_USAGE --> D_USAGE
    UC_NTF --> D_THRESH
    UC_NTF --> D_NOTIF

    UC_AUTH --> REPO
    UC_ADMIN --> REPO
    UC_ADMIN --> CRYPTO
    UC_USAGE --> REPO
    UC_DASH --> REPO
    UC_DASH --> CACHE
    UC_RPT --> REPO
    UC_RPT --> STORE
    UC_NTF --> REPO
    UC_NTF --> MAIL
    UC_AUDIT --> REPO
    UC_INGEST --> STORE
```

---

## Worker Component Diagram

Celery task routing and worker specialization.

```mermaid
flowchart LR
    subgraph producers ["Task Producers"]
        API_P["FastAPI API"]
        BEAT_P["Celery Beat"]
    end

    subgraph broker ["Redis Broker"]
        Q_INGEST["Queue: ingestion"]
        Q_REPORT["Queue: reports"]
        Q_ALERT["Queue: alerts"]
        Q_EMAIL["Queue: email"]
        Q_MAINT["Queue: maintenance"]
    end

    subgraph workers ["Celery Workers"]
        W_INGEST["Ingestion Worker<br/>parse · match · persist"]
        W_REPORT["Report Worker<br/>PDF · CSV · large queries"]
        W_ALERT["Alert Worker<br/>threshold evaluation"]
        W_EMAIL["Email Worker<br/>SMTP delivery"]
        W_MAINT["Maintenance Worker<br/>retention · aggregation refresh"]
    end

    subgraph stores ["Data Stores"]
        PG_W[("PostgreSQL")]
        STORE_W[("Local Volume")]
    end

    API_P --> Q_INGEST
    API_P --> Q_REPORT
    API_P --> Q_ALERT
    BEAT_P --> Q_ALERT
    BEAT_P --> Q_MAINT

    Q_INGEST --> W_INGEST
    Q_REPORT --> W_REPORT
    Q_ALERT --> W_ALERT
    Q_ALERT --> Q_EMAIL
    Q_EMAIL --> W_EMAIL
    Q_MAINT --> W_MAINT

    W_INGEST --> PG_W
    W_INGEST --> STORE_W
    W_REPORT --> PG_W
    W_REPORT --> STORE_W
    W_ALERT --> PG_W
    W_EMAIL --> PG_W
    W_MAINT --> PG_W
```

---

## Component Responsibilities

| Component | Responsibility | Scaling |
|-----------|----------------|---------|
| React SPA | UI rendering, client state, TanStack Query cache | `frontend` container behind nginx |
| nginx | TLS, routing, health checks | Single container; scale via second host (P2) |
| FastAPI | Sync REST API, auth, enqueue async jobs | Scale `api` service replicas in Compose |
| Celery Workers | Background processing | Scale `worker` service replicas |
| Celery Beat | Scheduled threshold scans, retention, reports | **Single** container |
| PostgreSQL | Transactional data, aggregates, audit | Docker volume; vertical scale |
| Redis | Cache, Celery broker, rate limit counters | Docker container + AOF volume |
| Local storage | Uploads, generated reports on `storage_data` volume | Expand host disk |
| Host secrets | JWT keys, DB creds, encryption keys in `.env` | Per-environment file |
| OpenTelemetry | Trace/metric export | OTel Collector container |

---

## Security Component Boundaries

```mermaid
flowchart TB
    subgraph public ["Public Zone"]
        USER["End Users"]
        PROXY_S["nginx - HTTPS only"]
    end

    subgraph compose ["Docker Compose Network"]
        API_S["api containers"]
        WORK_S["worker containers"]
        PG_S["postgres container"]
        REDIS_S["redis container"]
        STORE_S["storage_data volume"]
        ENV_S[".env / secrets"]
    end

    USER -->|TLS 1.2+| PROXY_S
    PROXY_S --> API_S
    API_S --> PG_S
    API_S --> REDIS_S
    API_S --> STORE_S
    API_S --> ENV_S
    WORK_S --> PG_S
    WORK_S --> REDIS_S
    WORK_S --> STORE_S
    WORK_S --> ENV_S
```

Credentials decrypted in worker/API memory only at point of use (NFR-SEC-005). No secrets in container images or Git (NFR-SEC-008).
