# AI Tool Usage Tracker

## Project Overview

AI Tool Usage Tracker is a centralized platform designed to monitor, analyze, and report AI tool consumption across organizations.

Organizations increasingly use multiple AI tools such as ChatGPT, Claude, Gemini, GitHub Copilot, Cursor, and other vendor platforms. This creates fragmented visibility into token consumption, licensing costs, package utilization, and user-level adoption.

The platform provides a unified dashboard that enables administrators, finance teams, and team leaders to understand AI usage patterns, control costs, monitor thresholds, and generate actionable reports.

---

# Vision

Provide organizations with complete visibility into AI tool usage, costs, and adoption through a single self-service platform.

---

# Goals

## Primary Goals

* Track AI tool consumption across teams and users.
* Monitor token utilization and associated costs.
* Attribute costs to teams and business units.
* Generate operational and financial insights.
* Alert stakeholders before budgets or quotas are exceeded.
* Support usage ingestion through APIs and vendor exports.
* Enable self-service administration without engineering support.

## Success Metrics

* Dashboard load time under 3 seconds.
* Support 50+ AI tools.
* Support 200+ teams.
* Support 5,000+ users.
* Report generation under 10 seconds for standard queries.
* 99.5% application uptime.

---

# Users and Roles

## Super Admin

Responsible for:

* Platform administration
* Tool configuration
* Team management
* API key management
* Threshold configuration
* Access to all reports and dashboards

## Team Admin

Responsible for:

* Managing team members
* Viewing team usage
* Configuring team-level alerts
* Reviewing uploaded usage files

## Finance Viewer

Responsible for:

* Monitoring spend
* Reviewing cost reports
* Budget oversight

Read-only access.

## Team Member

Responsible for:

* Viewing personal usage
* Monitoring own consumption

## Auditor

Responsible for:

* Reviewing exported reports
* Compliance validation
* Read-only organizational visibility

---

# Problem Statement

Organizations lack a centralized mechanism to answer questions such as:

* Which teams consume the most AI resources?
* Which AI tools generate the highest spend?
* Are license packages being underutilized?
* Which users are approaching thresholds?
* How can finance forecast AI expenditure?

Current approaches rely on disconnected spreadsheets and vendor-specific dashboards.

---

# Core Modules

## Module 1: Administration

### AI Tool Management

Capabilities:

* Add AI tools
* Edit AI tools
* Deactivate AI tools

Tool configuration includes:

* Tool name
* Vendor
* Pricing model
* Token pricing
* Package allowances
* Overage pricing

---

### Team Management

Capabilities:

* Create teams
* Update teams
* Deactivate teams
* Assign members
* Remove members

Users may belong to multiple teams.

---

### API Key Management

Capabilities:

* Configure vendor credentials
* Team-specific credentials
* Sandbox and production environments
* Key rotation tracking
* Expiration reminders

Security:

* Encrypt credentials at rest
* Mask keys after creation

---

### Threshold Management

Support alerts based on:

* Token count
* Package utilization percentage
* Cost amount

Threshold scope (UI):

* Organization
* Group (member org unit — API `/teams`)
* Team (API connection — API `/tools`, stored as scope `tool`)
* User

Severity:

* Warning
* Critical

Notification channels:

* Email
* In-app notifications

---

## Module 2: Dashboards

### Dashboard Widgets

#### Total Token Usage

Displays:

* Aggregate consumption
* Current period totals

---

#### Cost Overview

Displays:

* Actual spend
* Package allowance
* Overage costs

---

#### Usage by Tool

Displays:

* Consumption by AI tool
* Comparative analysis

---

#### Usage by Team

Displays:

* Team comparison

---

#### Top Consumers

Displays:

* Top teams
* Top users

---

#### Alert Status

Displays:

* Active alerts
* Threshold breaches

---

#### Trend Analysis

Displays:

* Daily trends
* Weekly trends
* Monthly trends

---

#### My Usage

Displays:

* Individual consumption summaries

---

Dashboard Features:

* Custom date filters
* Drill-down capability
* CSV export
* PDF export

---

## Module 3: Usage Tracking

### Team-Level Tracking

Track:

* Input tokens
* Output tokens
* Total tokens
* Package utilization
* Estimated costs
* Overage costs

Support:

* Near real-time synchronization
* Batch ingestion

---

## Module 4: Reporting

Reports include:

### Tool Usage Summary

Filters:

* Period
* Team
* Tool

---

### Team Usage Report

Filters:

* Period
* Team

---

### Cost Report

Filters:

* Period
* Team
* Tool

---

### User Usage Report

Filters:

* Period
* Team
* User

---

### Alert History

Filters:

* Period
* Team
* Tool
* Alert Type

---

### API Key Activity

Filters:

* Period
* Team
* Tool

---

Reporting Features

* CSV export
* PDF export
* Scheduled reports
* Email delivery
* Async report generation

---

## Module 5: Notifications

Capabilities:

* Persistent notification center
* Alert counters
* Email notifications
* Alert history

Notification Payload:

* Alert type
* Tool
* Team
* Threshold
* Current value
* Timestamp
* Deep links

---

## Module 6: Individual Usage Monitoring

Phase 1 ingestion through uploads.

Supported formats:

* CSV
* JSON
* XLSX

Capabilities:

* Auto-detect file format
* Parse vendor exports
* Match users by email
* Flag unmatched users
* Preview imports
* Reprocess uploads
* Delete uploads

Supported vendor exports include:

* OpenAI
* Anthropic
* Azure AI
* Cursor
* Other configurable providers

Individual views include:

* Total usage
* Usage by tool
* Trends
* Team comparisons

---

# Non-Functional Requirements

## Performance

* Dashboard response under 3 seconds.
* Standard report generation under 10 seconds.

## Availability

* 99.5% uptime SLA.

## Security

* AES-256 encryption at rest.
* Role-based access control.
* Audit logging.
* Secure credential handling.

## Scalability

Support:

* 50 AI tools
* 200 teams
* 5,000 users

## Data Retention

* Retain usage data for minimum 24 months.
* Configurable retention policies.

## File Uploads

* Maximum 50 MB per upload.
* Batch processing support.

---

# Phase Strategy

## Phase 1 (MVP)

Deliver:

* Administration
* Dashboarding
* Team-level tracking
* Reporting
* Alerts
* File upload ingestion
* Individual usage monitoring

---

## Phase 2

Potential Enhancements:

* Vendor billing integrations
* SSO/SAML authentication
* Mobile applications
* Automated vendor synchronization
* Predictive cost forecasting
* AI-driven optimization recommendations

---

# Technical Direction

Recommended Stack:

Frontend:

* React
* TypeScript
* Material UI
* TanStack Query
* Recharts

Backend:

* Python
* FastAPI

Database:

* PostgreSQL

Caching:

* Redis

Background Jobs:

* Celery

Storage:

* **Local Docker volumes** (uploads, reports, backups) — see ADR-013

Authentication:

* JWT
* RBAC

Infrastructure:

* **Docker Compose** (all environments — dev, staging, production)
* PostgreSQL, Redis, API, workers, frontend as containers
* Optional private Docker registry for image distribution

Observability:

* OpenTelemetry
* Grafana
* Prometheus

CI/CD:

* GitHub Actions

---

# OpenSpec Principles

* API-first design.
* Modular architecture.
* Domain-driven specifications.
* Backward-compatible schema evolution.
* Security by default.
* Testability for all features.
* AI-assisted specification generation.

---

# Out of Scope

Phase 1 excludes:

* Vendor procurement workflows
* Contract management
* Direct billing reconciliation
* Mobile-native applications
* Full SSO/SAML implementation
* SDK-level AI integrations

---

# Future Vision

Become the organization's system of record for AI consumption, enabling governance, budgeting, optimization, and strategic decision-making across all AI investments.

---

# Frontend Application (Implemented — 2026-06-15)

The React SPA lives in `frontend/`. Production is served from the `frontend` Docker container (nginx) with optional dev Vite profile.

## UI terminology vs API

| UI label | Route | Backend API | Purpose |
|----------|-------|-------------|---------|
| **Teams** | `/admin/teams` | `/api/v1/tools` | Vendor API connections (Cursor, OpenAI, …) |
| **Groups** | `/admin/groups` | `/api/v1/teams` | Member org units, budgets, tool access |
| **Members** | `/admin/members` | `/api/v1/members` | Platform users |
| **Credentials** | `/admin/credentials` | `/api/v1/credentials` | Encrypted vendor keys |

Legacy redirect: `/admin/tools` → `/admin/teams`.

## Active routes

| Route | Page | Access |
|-------|------|--------|
| `/login` | Login | Public |
| `/insights` | Insights hub (Overview, By Team, Reports) | Authenticated |
| `/alerts`, `/alerts/history` | Alerts | Super Admin, Team Admin |
| `/uploads`, `/uploads/:uploadId/preview` | Uploads + preview | Authenticated |
| `/admin/teams` | Teams (API connections) | Super Admin |
| `/admin/groups` | Groups | Super Admin |
| `/admin/providers` | Providers | Super Admin |
| `/admin/members` | Members | Super Admin |
| `/admin/credentials` | Credentials | Super Admin |
| `/admin/audit-log` | Audit log | Super Admin |

## Redirects

| From | To |
|------|-----|
| `/` | `/insights` if authenticated, else `/login` |
| `/dashboard`, `/usage/*`, `/reports/*` | `/insights` |
| `/admin/tools` | `/admin/teams` |
| `*` (unknown) | `/insights` |

## Insights hub

- **Overview** — stats, cost-by-team chart, top users, recent alerts
- **By Team** — usage table from `GET /dashboard/usage-by-team` (API team / tool metrics)
- **Reports** — generate, download, subscribe, delete

Team filter on Insights lists **API teams** (`/tools`), not member groups.

## Auth behaviour

- Tokens persisted in `sessionStorage`; session restored on reload via `/auth/me`
- Default landing after login or restore: `/insights`
- Router basename from `VITE_BASE_PATH` (e.g. `/aitool` in production)

## Production URLs (foundry.inapp.com)

| URL | Purpose |
|-----|---------|
| `https://foundry.inapp.com/aitool/` | SPA |
| `https://foundry.inapp.com/aitool/api/v1/` | API (proxied by frontend nginx) |

Host port: `4501` (`APP_PORT`). See repository `README.md` and `openspec/specifications/deployment.md`.

## OpenSpec change

Detailed delta specs: `openspec/changes/frontend-ux-deployment-alignment/`
