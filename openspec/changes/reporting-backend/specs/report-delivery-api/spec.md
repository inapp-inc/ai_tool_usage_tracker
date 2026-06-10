# Report Delivery API — Delta Specification

## ADDED Requirements

### Requirement: Synchronous report generation

The system SHALL implement `POST /api/v1/reports/generate` returning 200 with report body when generation completes within the standard performance budget.

#### Scenario: Sync JSON report within budget

- **GIVEN** a standard-sized dataset and `async: false`
- **WHEN** a report is requested with format `json`
- **THEN** the response status is 200 within 10 seconds
- **AND** the body contains report data matching requested filters

#### Scenario: Sync CSV download

- **GIVEN** `async: false` and format `csv`
- **WHEN** generation completes within budget
- **THEN** the response status is 200 with `text/csv` body

### Requirement: Asynchronous report generation

The system SHALL queue large or forced-async reports via Celery and return 202 with a job identifier.

#### Scenario: Async job queued

- **GIVEN** `async: true` or result set exceeds sync threshold
- **WHEN** `POST /reports/generate` is called
- **THEN** the response status is 202
- **AND** the body includes `job_id` and status `queued`

#### Scenario: Async job completes with artifact

- **GIVEN** a queued async job
- **WHEN** the Celery worker finishes successfully
- **THEN** job status becomes `completed`
- **AND** artifact is written to local storage
- **AND** a completion notification hook is invoked

### Requirement: Report job status

The system SHALL implement `GET /api/v1/reports/jobs/{jobId}` returning job status for the requesting user within the organization.

#### Scenario: Poll job until completed

- **GIVEN** an async job owned by the caller
- **WHEN** `GET /reports/jobs/{jobId}` is called after completion
- **THEN** status is `completed`
- **AND** `download_url` or equivalent local download path is present

#### Scenario: Job not found for other org

- **GIVEN** a job id belonging to another organization
- **WHEN** the caller requests job status
- **THEN** the response status is 404 Not Found

### Requirement: Report artifact download

The system SHALL implement `GET /api/v1/reports/jobs/{jobId}/download` for completed jobs using local storage per ADR-013.

#### Scenario: Download completed report

- **GIVEN** a completed job with stored artifact
- **WHEN** download is requested by the job owner
- **THEN** the client receives the report file with correct content type

#### Scenario: Download before completion rejected

- **GIVEN** a job with status `queued` or `processing`
- **WHEN** download is requested
- **THEN** the response status is 409 Conflict with Problem Details

### Requirement: Exported data respects RBAC

The system SHALL ensure sync responses and downloaded artifacts contain only data the requester is authorized to view.

#### Scenario: Unauthorized team filter denied

- **GIVEN** a Team Admin not member of team T
- **WHEN** generate is called with `team_id` for T
- **THEN** the response status is 403 Forbidden
