# Sequence Diagrams

Key interaction flows for the AI Tool Usage Tracker.

---

## 1. User Authentication and Dashboard Load

Authenticated dashboard access with cached aggregate reads.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SPA as React SPA
    participant ALB as ALB
    participant API as FastAPI
    participant Auth as Identity Module
    participant Dash as Dashboard Module
    participant Redis as Redis Cache
    participant PG as PostgreSQL

    User->>SPA: Enter credentials
    SPA->>ALB: POST /auth/login
    ALB->>API: Forward request
    API->>Auth: Validate credentials
    Auth->>PG: Query user + roles
    PG-->>Auth: User record
    Auth-->>API: JWT access token
    API-->>SPA: 200 OK + JWT

    User->>SPA: Open dashboard
    SPA->>ALB: GET /dashboard/widgets?period=current_month<br/>Authorization: Bearer JWT
    ALB->>API: Forward request
    API->>Auth: Validate JWT + RBAC scope
    Auth-->>API: Authorized context

    API->>Dash: GetWidgetData(org, team scope, period)
    Dash->>Redis: GET cache key
    alt Cache hit
        Redis-->>Dash: Cached aggregates
    else Cache miss
        Dash->>PG: Query usage_aggregates
        PG-->>Dash: Aggregate rows
        Dash->>Redis: SET cache TTL 5min
    end

    Dash-->>API: Widget payload
    API-->>SPA: 200 OK JSON
    SPA-->>User: Render dashboard under 3s p95
```

**NFR traceability:** NFR-PER-001 (dashboard ≤3s), NFR-SEC-003/004 (JWT + RBAC)

---

## 2. Vendor File Upload and Ingestion

Phase 1 primary ingestion path via file upload (FR-ING-001, FR-ING-002).

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Team Admin
    participant SPA as React SPA
    participant API as FastAPI
    participant Ingest as Ingestion Module
    participant S3 as AWS S3
    participant PG as PostgreSQL
    participant Redis as Redis Broker
    participant Worker as Celery Ingestion Worker
    participant Parser as Vendor Parser Adapter
    participant Usage as Usage Module
    participant Audit as Audit Module

    Admin->>SPA: Upload vendor export file
    SPA->>API: POST /uploads multipart file + team_id<br/>Authorization: Bearer JWT
    API->>API: Validate size <= 50MB, RBAC
    API->>S3: PutObject encrypted
    S3-->>API: s3_key
    API->>PG: Insert upload record status=pending
    API->>Audit: Log upload initiated
    API->>Redis: enqueue ingest_file task
    API-->>SPA: 202 Accepted upload_id

    Redis->>Worker: ingest_file(upload_id)
    Worker->>S3: GetObject
    S3-->>Worker: File bytes
    Worker->>Parser: detect_format + parse
    Parser-->>Worker: Normalized usage rows

    Worker->>PG: Stage parsed rows
    Worker->>PG: Match users by email
    Worker->>PG: Update upload status=preview_ready

    Admin->>SPA: Open import preview
    SPA->>API: GET /uploads/{id}/preview
    API->>PG: Fetch staged rows + unmatched flags
    API-->>SPA: Preview summary

    Admin->>SPA: Confirm import
    SPA->>API: POST /uploads/{id}/commit
    API->>Redis: enqueue commit_import task
    Redis->>Worker: commit_import(upload_id)

    loop Each normalized row
        Worker->>Usage: RecordUsage event idempotent
        Usage->>PG: Insert usage_event + update aggregates
    end

    Worker->>PG: Update upload status=completed
    Worker->>Redis: enqueue evaluate_thresholds
    Worker->>Audit: Log import committed
```

**FR traceability:** FR-ING-001, FR-ING-002, FR-USG-001, FR-USG-002

---

## 3. Threshold Evaluation and Alert Notification

Post-ingestion and scheduled threshold breach flow (FR-NTF-003).

```mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat
    participant Redis as Redis Broker
    participant AlertW as Alert Worker
    participant Usage as Usage Module
    participant PG as PostgreSQL
    participant NTF as Notification Module
    participant EmailW as Email Worker
    participant SMTP as Email Provider
    participant SPA as React SPA
    actor Admin as Team Admin

    Beat->>Redis: schedule evaluate_thresholds hourly
    Redis->>AlertW: evaluate_thresholds org_id

    AlertW->>PG: Load active thresholds
    loop Each threshold
        AlertW->>Usage: GetCurrentMetric tool/team/user scope
        Usage->>PG: Query aggregates
        PG-->>Usage: Current value
        Usage-->>AlertW: Metric value

        alt Value >= critical limit AND no active alert
            AlertW->>PG: Insert alert status=active severity=critical
            AlertW->>NTF: CreateInAppNotification
            NTF->>PG: Insert notification
            AlertW->>Redis: enqueue send_alert_email
        else Value >= warning limit AND no active warning
            AlertW->>PG: Insert alert status=active severity=warning
            AlertW->>NTF: CreateInAppNotification
        else Value < threshold AND active alert exists
            AlertW->>PG: Update alert status=resolved
        end
    end

    Redis->>EmailW: send_alert_email alert_id
    EmailW->>PG: Load alert + recipients
    EmailW->>SMTP: Send email with deep link
    SMTP-->>EmailW: Delivery accepted

    Admin->>SPA: Open notification center
    SPA->>NTF: GET /notifications
    NTF->>PG: Query unread notifications
    PG-->>SPA: Alert payload with deep link
    Admin->>SPA: Click deep link to dashboard
```

**NFR traceability:** NFR-PER-005 (email ≤5 min p95), FR-NTF-001 – 003

---

## 4. Async Report Generation

Large report offloaded to background worker (FR-RPT-007).

```mermaid
sequenceDiagram
    autonumber
    actor User as Finance Viewer
    participant SPA as React SPA
    participant API as FastAPI
    participant RPT as Reporting Module
    participant PG as PostgreSQL
    participant Redis as Redis Broker
    participant ReportW as Report Worker
    participant S3 as AWS S3
    participant NTF as Notification Module

    User->>SPA: Request Cost Report large date range
    SPA->>API: POST /reports/cost async=true
    API->>API: Estimate query cost / row count

    alt Standard report <= 10s estimate
        API->>RPT: GenerateReport sync
        RPT->>PG: Execute query
        PG-->>RPT: Result set
        RPT-->>API: CSV/PDF bytes
        API-->>SPA: 200 OK file download
    else Large report async required
        API->>PG: Insert report_job status=queued
        API->>Redis: enqueue generate_report job_id
        API-->>SPA: 202 Accepted job_id

        Redis->>ReportW: generate_report job_id
        ReportW->>PG: Update status=processing
        ReportW->>PG: Execute report query
        PG-->>ReportW: Large result set
        ReportW->>ReportW: Render CSV or PDF
        ReportW->>S3: PutObject report artifact
        ReportW->>PG: Update status=completed s3_key

        ReportW->>NTF: CreateInAppNotification report ready
        NTF->>PG: Insert notification

        User->>SPA: Poll or receive notification
        SPA->>API: GET /reports/jobs/{job_id}
        API->>PG: Fetch job status
        API-->>SPA: status=completed download_url

        User->>SPA: Download report
        SPA->>API: GET /reports/jobs/{job_id}/download
        API->>S3: Generate presigned URL
        API-->>SPA: Presigned URL
        SPA-->>User: Download file
    end
```

**NFR traceability:** NFR-PER-002 (standard ≤10s; async fallback)

---

## 5. API Credential Storage and Rotation

Secure credential lifecycle (FR-ADM-003, NFR-SEC-005).

```mermaid
sequenceDiagram
    autonumber
    actor SA as Super Admin
    participant SPA as React SPA
    participant API as FastAPI
    participant Admin as Administration Module
    participant Crypto as Encryption Adapter
    participant SM as Secrets Manager
    participant PG as PostgreSQL
    participant Audit as Audit Module

    SA->>SPA: Create vendor API credential
    SPA->>API: POST /credentials tool_id team_id env key_value
    API->>API: RBAC Super Admin check
    API->>Crypto: encrypt key_value AES-256
    Crypto->>SM: Fetch data encryption key
    SM-->>Crypto: DEK
    Crypto-->>API: ciphertext

    API->>PG: INSERT credential masked_display last4
    API->>Audit: Log credential created
    API-->>SPA: 201 Created masked credential

    Note over SA,SPA: Full secret never returned after creation

    SA->>SPA: Rotate credential
    SPA->>API: POST /credentials/{id}/rotate
    API->>Crypto: encrypt new key
    API->>PG: UPDATE ciphertext rotation_date
    API->>Audit: Log credential rotated
    API-->>SPA: 200 OK

    SA->>SPA: View credential list
    SPA->>API: GET /credentials
    API->>PG: Query metadata only
    API-->>SPA: Masked keys + expiration dates
```

---

## 6. Scheduled Report Email Delivery

Recurring report distribution (FR-RPT-007 P1).

```mermaid
sequenceDiagram
    autonumber
    participant Beat as Celery Beat
    participant Redis as Redis Broker
    participant ReportW as Report Worker
    participant PG as PostgreSQL
    participant S3 as AWS S3
    participant EmailW as Email Worker
    participant SMTP as Email Provider
    actor Recipient as Finance Viewer

    Beat->>Redis: trigger scheduled_reports org timezone
    Redis->>ReportW: run_scheduled_report schedule_id

    ReportW->>PG: Load schedule filters + recipients
    ReportW->>PG: Generate report data
    ReportW->>S3: Store report artifact
    ReportW->>PG: Insert report_job completed

    ReportW->>Redis: enqueue email_report job_id recipients
    Redis->>EmailW: email_report
    EmailW->>S3: GetObject attachment
    EmailW->>SMTP: Send with CSV/PDF attachment
    SMTP-->>Recipient: Scheduled cost report email
```

---

## Sequence Diagram Index

| # | Flow | Primary FRs | Primary NFRs |
|---|------|-------------|--------------|
| 1 | Auth + dashboard load | FR-DSH-009, FR-PLT-001 | NFR-PER-001, NFR-SEC-003 |
| 2 | File upload ingestion | FR-ING-001 – 002, FR-USG-001 | NFR-SEC-006, NFR-PER-004 |
| 3 | Threshold alerts | FR-NTF-001 – 003, FR-ADM-004 | NFR-PER-005 |
| 4 | Async report generation | FR-RPT-007 | NFR-PER-002 |
| 5 | Credential storage | FR-ADM-003 | NFR-SEC-005, NFR-SEC-008 |
| 6 | Scheduled report email | FR-RPT-007 | NFR-PER-002, NFR-CMP-004 |
