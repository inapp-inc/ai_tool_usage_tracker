# Data Flow

End-to-end data movement from ingestion through aggregation to consumption.

---

## Data Flow Overview

```mermaid
flowchart TB
    subgraph sources ["Data Sources - Phase 1"]
        UPLOAD["Vendor File Upload<br/>CSV · JSON · XLSX"]
        API_INGEST["Usage API Ingestion<br/>batch / near-real-time"]
    end

    subgraph ingest_pipeline ["Ingestion Pipeline"]
        S3_RAW[("S3 Raw Files")]
        STAGE["Staging Tables<br/>parsed_rows · unmatched"]
        NORMALIZE["Normalization<br/>UsageRecord canonical form"]
    end

    subgraph core_store ["Core Data Store - PostgreSQL"]
        EVENTS[("usage_events<br/>append-only facts")]
        AGG[("usage_aggregates<br/>daily · team · tool · user")]
        CONFIG[("config tables<br/>tools · teams · thresholds")]
        AUDIT_T[("audit_log<br/>append-only")]
        NOTIF_T[("notifications · alerts")]
    end

    subgraph processing ["Processing"]
        COST["Cost Calculator<br/>pricing · overage"]
        THRESH["Threshold Evaluator"]
        AGG_JOB["Aggregation Refresh Job"]
    end

    subgraph consumption ["Consumption"]
        CACHE[("Redis Cache")]
        DASH["Dashboard API"]
        REPORT["Reporting API"]
        EMAIL["Email Notifications"]
    end

    UPLOAD --> S3_RAW
    S3_RAW --> STAGE
    API_INGEST --> NORMALIZE
    STAGE --> NORMALIZE
    NORMALIZE --> EVENTS

    EVENTS --> COST
    COST --> AGG
    CONFIG --> COST
    EVENTS --> AGG_JOB
    AGG_JOB --> AGG

    AGG --> THRESH
    CONFIG --> THRESH
    THRESH --> NOTIF_T
    THRESH --> EMAIL

    AGG --> CACHE
    CACHE --> DASH
    AGG --> REPORT
    EVENTS --> REPORT

    CONFIG --> AUDIT_T
    ingest_pipeline --> AUDIT_T
```

---

## Entity Relationship (Conceptual)

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ TEAM : has
    ORGANIZATION ||--o{ TOOL : configures
    TEAM ||--o{ TEAM_MEMBERSHIP : contains
    USER ||--o{ TEAM_MEMBERSHIP : belongs
    TOOL ||--o{ CREDENTIAL : secures
    TEAM ||--o{ CREDENTIAL : scopes
    TOOL ||--o{ THRESHOLD : limits
    TEAM ||--o{ THRESHOLD : limits
    USER ||--o{ THRESHOLD : limits
    UPLOAD ||--o{ PARSED_ROW : contains
    PARSED_ROW ||--o| USAGE_EVENT : commits_to
    TOOL ||--o{ USAGE_EVENT : tracks
    TEAM ||--o{ USAGE_EVENT : attributes
    USER ||--o{ USAGE_EVENT : attributes
    USAGE_EVENT }o--|| USAGE_AGGREGATE : rolls_up
    THRESHOLD ||--o{ ALERT : triggers
    ALERT ||--o{ NOTIFICATION : generates
    USER ||--o{ NOTIFICATION : receives

    ORGANIZATION {
        uuid id PK
        string name
        string timezone
        json retention_policy
    }

    TOOL {
        uuid id PK
        uuid organization_id FK
        string name
        string vendor
        json pricing_model
        decimal token_price
        bigint package_allowance
        decimal overage_price
        boolean active
    }

    USAGE_EVENT {
        uuid id PK
        uuid organization_id FK
        uuid tool_id FK
        uuid team_id FK
        uuid user_id FK
        timestamp occurred_at
        bigint input_tokens
        bigint output_tokens
        decimal estimated_cost
        decimal overage_cost
        string vendor_event_id
    }

    USAGE_AGGREGATE {
        uuid id PK
        date period_date
        string granularity
        uuid scope_tool_id
        uuid scope_team_id
        uuid scope_user_id
        bigint total_tokens
        decimal total_cost
        decimal package_utilization_pct
    }
```

---

## Ingestion Data Flow (Detail)

### Stage 1: Capture

| Step | Data | Storage |
|------|------|---------|
| Upload received | Raw bytes | S3 `org/{id}/uploads/` |
| Metadata recorded | filename, size, uploader, team, status | PostgreSQL `uploads` |
| Audit | upload initiated | PostgreSQL `audit_log` |

### Stage 2: Parse and Match

| Step | Data | Storage |
|------|------|---------|
| Format detection | MIME, extension, header sniff | Worker memory |
| Vendor parse | Raw rows → `UsageRecord` | PostgreSQL `parsed_rows` staging |
| User match | email → `user_id` | Update staging; flag `unmatched` |
| Preview | counts, samples | API read from staging |

### Stage 3: Commit

| Step | Data | Storage |
|------|------|---------|
| Idempotency check | `vendor_event_id` or hash | PostgreSQL unique index |
| Persist facts | `UsageEvent` rows | PostgreSQL `usage_events` |
| Cost calculation | pricing from `tools` | Computed columns on event |
| Aggregate refresh | rollups | PostgreSQL `usage_aggregates` |
| Cache invalidation | org/team keys | Redis DEL pattern |
| Threshold queue | evaluation task | Redis Celery queue |

---

## Read Path Data Flow (Dashboard)

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Redis
    participant PG

    Client->>API: GET /dashboard/tokens?from=&to=
    API->>Redis: GET agg:org:team:period
    alt Hit
        Redis-->>API: JSON blob
    else Miss
        API->>PG: SELECT FROM usage_aggregates<br/>WHERE period BETWEEN from AND to
        PG-->>API: Rows
        API->>Redis: SETEX 300
    end
    API-->>Client: Widget JSON
```

**Consistency model:** Eventual consistency — aggregates may lag ingestion by near-real-time SLA (≤5 min, NFR-PER-004). Dashboard SHOULD display `last_updated_at` timestamp.

---

## Write Path Data Flow (Administration)

Configuration changes follow **transactional write + audit + cache invalidation**.

```mermaid
flowchart LR
    A["Admin API Request"] --> B["RBAC Check"]
    B --> C["Domain Validation"]
    C --> D["DB Transaction<br/>update config"]
    D --> E["Insert audit_log"]
    E --> F["Invalidate Redis keys"]
    F --> G["Response 200"]
```

Pricing changes do NOT retroactively alter stored `usage_events` unless explicit **reprocess** job is triggered (FR-ADM-001 business rule).

---

## Cost Calculation Data Flow

```mermaid
flowchart TD
    E["UsageEvent<br/>input + output tokens"] --> P["Load Tool Pricing"]
    P --> C1["estimated_cost =<br/>tokens × token_price"]
    P --> U{"tokens > package_allowance?"}
    U -->|No| C2["overage_cost = 0<br/>utilization = tokens / allowance"]
    U -->|Yes| C3["overage_cost =<br/>overage_tokens × overage_price"]
    C1 --> S["Store on event + aggregate"]
    C2 --> S
    C3 --> S
```

Pricing model variants (per-tool `pricing_model` JSON) use **Strategy pattern** — e.g., flat token rate, tiered, seat-based placeholder for Phase 2.

---

## Alert Data Flow

```mermaid
flowchart TD
    AGG["usage_aggregates<br/>current period"] --> EV["Threshold Evaluator"]
    TH["thresholds table"] --> EV
    EV --> D{"metric vs limit"}
    D -->|breach| AL["Insert alert active"]
    D -->|resolved| RS["Update alert resolved"]
    AL --> NI["In-app notification"]
    AL --> EM["Email task queue"]
    RS --> AH["Alert history for reports"]
```

Alert deduplication: one active alert per `(threshold_id, period_window)`.

---

## Report Data Flow

| Report Type | Primary Tables | Output |
|-------------|----------------|--------|
| Tool Usage Summary | `usage_aggregates`, `tools` | CSV/PDF |
| Team Usage | `usage_aggregates`, `teams` | CSV/PDF |
| Cost Report | `usage_aggregates`, `tools` | CSV/PDF |
| User Usage | `usage_aggregates`, `users` | CSV/PDF |
| Alert History | `alerts`, `thresholds` | CSV/PDF |
| API Key Activity | `audit_log`, `credentials` metadata | CSV/PDF |

Large reports: query → stream to temp file → S3 → presigned download URL.

---

## Data Retention Flow

```mermaid
flowchart TD
    BEAT["Daily retention job"] --> POL["Load org retention_policy"]
    POL --> PURGE["Delete usage_events older than policy"]
    PURGE --> ARCH["Optional S3 archive export"]
    ARCH --> AUDIT["Audit log retention entry"]
    POL --> AUDIT_KEEP["audit_log min 24 months"]
```

Default: 24 months minimum (FR-PLT-004, NFR-CMP-001). Purge is hard delete from active tables; archive optional Phase 2.

---

## Data Classification

| Classification | Examples | Controls |
|----------------|----------|----------|
| **Restricted** | API credentials ciphertext | AES-256, Secrets Manager, no logs |
| **Confidential** | Usage per user, cost data | RBAC, encryption at rest |
| **Internal** | Team aggregates, tool config | RBAC |
| **Public** | None in Phase 1 | N/A |

---

## Data Volume Estimates (Reference Scale)

| Entity | Estimated Volume (24 mo) |
|--------|--------------------------|
| Users | 5,000 |
| Teams | 200 |
| Tools | 50 |
| Usage events | ~50M (NFR-SCL-001) |
| Aggregates (daily) | ~18M rows (50 tools × 200 teams × 365 × est. users factor reduced by rollup) |
| Uploads | ~10K files/year (assumption) |
| Audit log | ~500K events/year |

Partitioning strategy: `usage_events` partitioned by `occurred_at` monthly (PostgreSQL declarative partitioning) when row count exceeds 10M.
