# ADR-017: Local Report Artifact Storage

**Status:** Accepted  
**Date:** 2026-06-10

---

## Context

OpenAPI describes report download via presigned S3 URLs (legacy from pre-ADR-013 design). ADR-013 mandates Phase 1 artifacts on **local Docker volumes** at `LOCAL_STORAGE_ROOT/reports/`. Report jobs must persist retrievable paths with 90-day retention per database.md.

---

## Decision

Store generated report files on the **local filesystem** inside the shared `storage_data` volume:

- Path pattern: `{LOCAL_STORAGE_ROOT}/reports/{organization_id}/{job_id}/report.{json|csv|pdf}`
- Persist relative path in `reporting.report_jobs.storage_key`
- API download endpoint streams the file after auth check — no S3 presigned URLs in Phase 1
- Celery worker and API containers MUST mount the same storage volume

Async job `download_url` in API responses MAY be the authenticated API download path, not an external presigned URL.

---

## Consequences

### Positive

- Aligns reporting with ADR-013 deployment model.
- Simpler Phase 1 ops on single-host Compose.
- Retention job deletes files alongside `report_jobs` rows.

### Negative

- No CDN edge delivery for large PDFs.
- Horizontal scaling requires shared volume or future object storage migration.

### Neutral

- S3 adapter can supersede this ADR in Phase 2 cloud migration.

---

## Alternatives

| Alternative | Why Not Chosen |
|-------------|----------------|
| **S3 presigned URLs (OpenAPI default)** | Contradicts ADR-013 Phase 1 |
| **Store PDF in PostgreSQL BYTEA** | Poor fit for large files and retention |
| **Ephemeral container filesystem** | Artifacts lost on restart |

**Supersedes:** None (operational interpretation of OpenAPI download for Phase 1)  
**Superseded by:** Future object-storage ADR for Phase 2  
**Related:** ADR-013, ADR-004, FR-RPT-007
