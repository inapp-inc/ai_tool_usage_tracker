# ADR-009: S3 Object Storage for Uploads and Reports

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

Phase 1 ingestion accepts vendor export files up to **50 MB** in CSV, JSON, and XLSX formats (FR-ING-001). Async report generation produces CSV/PDF artifacts that may be large (FR-RPT-007). Storing files on ephemeral container filesystems is incompatible with horizontal scaling and pod restarts. NFR-SEC-001 requires encryption at rest; NFR-SCL-004 requires durable object storage.

---

## Decision

Use **Amazon S3** as the object store for:

| Object Type | Key Pattern | Lifecycle |
|-------------|-------------|-----------|
| Raw uploads | `org/{org_id}/uploads/{upload_id}/{filename}` | IA after 90 days |
| Report artifacts | `org/{org_id}/reports/{job_id}/{name}.pdf\|csv` | Delete per retention policy |
| Optional archive exports | `org/{org_id}/archive/` | Glacier after 24 months (Phase 2) |

**Upload flow (Phase 1):** API-mediated multipart upload to S3 after RBAC and size validation.  
**Download flow:** Time-limited **presigned URLs** (15-minute expiry) after RBAC check—browser downloads directly from S3.

Encryption: **SSE-KMS** or SSE-S3. Versioning enabled on production buckets (NFR-BKP-003).

---

## Consequences

### Positive

- Durable storage independent of pod lifecycle; supports horizontal API scaling.
- Presigned URLs offload large report downloads from API pods.
- S3 lifecycle policies manage cost for aged uploads (NFR-SCL-004).
- Encryption at rest satisfies NFR-SEC-001 for file artifacts.

### Negative

- S3 costs accumulate with upload volume; lifecycle rules required.
- Presigned URL expiry may confuse users on slow downloads—15 minutes generally sufficient.
- API-mediated upload streams file through API pod (bandwidth); presigned POST upload deferred to Phase 2 if needed.

### Neutral

- MinIO viable for local dev; production uses AWS S3 per project direction.
- Virus scanning of uploads not specified in Phase 1; may add in security hardening.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **Store files in PostgreSQL BYTEA** | Poor performance and backup bloat for 50 MB files. |
| **Local/container disk** | Not durable; breaks multi-replica API deployment. |
| **EFS shared filesystem** | Higher cost and complexity vs object storage for immutable files. |
| **Direct browser-to-S3 presigned upload (Phase 1)** | Simpler RBAC validation via API-mediated upload for MVP; presigned POST can be Phase 2 optimization. |
| **Azure Blob / GCS** | Project specifies AWS S3. |

**Supersedes:** None  
**Related:** ADR-004, ADR-007
