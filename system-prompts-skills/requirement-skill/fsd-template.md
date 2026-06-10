# Functional Specification Template

Use this template as your structural guide. Adapt it — add sub-sections, merge thin sections, or drop sections that genuinely have no content. The goal is a document that is useful, not one that is complete for its own sake.

**Spec-driven workflow:** When following spec-driven development (SDD), the FSD should be created from a **filled gaps questionnaire**. The preferred workflow is:

- Project root convention: `<projectDir>` is the folder directly under the repo root (`Presales/<ProjectName>`). The **project name** is `<ProjectName>`.
- Project layout: `<projectDir>/{Discovery and Design, Docs, codebase}/`
- Gaps source-of-truth JSON: `<projectDir>/Discovery and Design/gap-questionnaire.json`
- Review artifacts (generated): `<projectDir>/Docs/SDD_Gaps_Questionnaire.md` and `<projectDir>/Docs/SDD_Gaps_Answers.md`

Fill the questionnaire in the portal (`requirement-skill/gaps-questionnaire-web/`), then generate the reviewable Markdown artifacts from the JSON and use those as the primary input. For features that expose or consume APIs, the design phase will produce an **OpenAPI specification**; the FSD’s integration and data contract details should align with that spec, and implementation and testing will reference it (including API contract validation, e.g. with Zod).

---

```markdown
# Functional Specification: [Project / Feature Name]

**Version:** 1.0
**Date:** [YYYY-MM-DD]
**Status:** Draft
**Author:** [Author or "AI-Generated Draft"]
**Stakeholders:** [Names / roles if known]

---

## 1. Executive Summary

A 2–4 sentence overview: what is being built, why it matters, and who it serves.
Keep this punchy — someone reading only this section should understand the project.

---

## 2. Background & Problem Statement

Why does this project exist? What pain, gap, or opportunity is it addressing?
Include relevant context: current state, what's broken or missing, how users are coping today.

---

## 3. Goals & Success Criteria

What does success look like? Be specific.

| Goal | Success Metric |
|------|----------------|
| [Goal 1] | [Measurable outcome] |
| [Goal 2] | [Measurable outcome] |

**Out of scope:** List explicitly what this project will NOT address to prevent scope creep.

---

## 4. Stakeholders & User Personas

### Stakeholders
| Role | Name / Team | Interest |
|------|-------------|----------|
| Sponsor | | Funding / strategic alignment |
| Product Owner | | Prioritization and acceptance |
| End Users | | Day-to-day usage |

### User Personas

**Persona 1: [Name / Role]**
- Description: Who they are and what they do
- Goals: What they're trying to accomplish
- Pain points: What frustrates them today
- Key scenarios: When and how they'll use this system

*(Repeat for each distinct persona)*

---

## 5. Functional Requirements

Organize by Epic. Each Epic contains User Stories, each story has Acceptance Criteria.

### Epic 1: [Name — e.g., User Authentication]

> Brief description of this capability area.

#### Story 1.1: [Short title]
**As a** [persona], **I want** [capability] **so that** [benefit].

**Acceptance Criteria:**
- [ ] Given [context], when [action], then [outcome]
- [ ] Given [context], when [action], then [outcome]
- [ ] [Additional criteria as needed]

**Notes / Edge cases:** [Optional — anything that complicates this story]

---

#### Story 1.2: [Short title]
...

---

### Epic 2: [Name]

*(Continue pattern)*

---

## 6. Non-Functional Requirements

### Performance
- [e.g., Page load < 2s under normal load (< 500 concurrent users)]
- [e.g., API responses < 300ms at p95]

### Security & Access Control
- [e.g., Role-based access control with at least 3 roles: Admin, Editor, Viewer]
- [e.g., All data in transit encrypted via TLS 1.2+]
- [e.g., Authentication via SSO / OAuth 2.0]

### Reliability & Availability
- [e.g., 99.5% uptime SLA]
- [e.g., Graceful degradation if external service is unavailable]

### Scalability
- [e.g., Must support up to 10,000 active users in Year 1]

### Compliance & Data
- [e.g., GDPR-compliant data handling]
- [e.g., Audit log of all user actions retained for 90 days]

### Usability & Accessibility
- [e.g., Responsive design for mobile and desktop]
- [e.g., WCAG 2.1 AA compliance]

---

## 7. System & Data Architecture (High-Level)

Describe the high-level architecture or data model if relevant. Use prose or a simple
diagram description. This section can be skipped for small features or expanded
significantly for greenfield systems.

### Key Entities / Data Model

| Entity | Key Attributes | Relationships |
|--------|---------------|---------------|
| [Entity 1] | id, name, ... | belongs to [Entity 2] |
| [Entity 2] | id, ... | has many [Entity 1] |

### Integration Points

For each external system, provide a table covering the specific endpoints or operations involved, not just a high-level mention. A developer reading this should be able to scope the integration work without further research.

| System | Endpoint / Operation | Direction | Trigger | Data Exchanged | Auth | Sync Frequency | Error Handling |
|--------|---------------------|-----------|---------|----------------|------|----------------|----------------|
| [System] | `GET /resource` | Outbound | [User action / schedule / webhook] | [Key fields in/out] | OAuth 2.0 / API key | On-demand / Daily | [Fallback behavior] |
| [System] | `POST /resource` | Outbound | [Trigger] | [Fields] | [Auth] | Real-time | [Retry / queue] |

Add prose below the table to explain any nuance: field mapping decisions, known limitations of the external API, data transformation needed, or sequencing dependencies between calls.

**If the exact endpoint is unknown:** use the most likely endpoint based on the platform's documented API, and mark it as an assumption (e.g., "Assumed — confirm against Salesforce sandbox"). A named placeholder is always more useful than "TBD".

**OpenAPI alignment:** For APIs owned by this project, the authoritative contract is the **OpenAPI specification** (e.g., `openapi.yaml`). This section should be consistent with that spec; the spec is the source of truth for frontend and backend implementation and for API contract tests (e.g., Zod-based validation).

---

## 8. User Flows (Key Scenarios)

Describe the 2–3 most important end-to-end workflows in plain language or numbered steps.
Focus on the happy path; note key error states at the end of each flow.

### Flow 1: [Name — e.g., New User Onboarding]
1. User arrives at...
2. User enters...
3. System validates...
4. System creates...
5. User is redirected to...

**Error states:** What happens if [X fails]?

---

## 9. Assumptions

List all assumptions made during spec creation. Be specific — each assumption is
something the reviewer should explicitly validate or correct.

- **[A1]** [e.g., Single-tenant architecture; multi-tenancy is out of scope for v1]
- **[A2]** [e.g., Users will authenticate via an existing SSO provider; no standalone auth system needed]
- **[A3]** [e.g., Mobile support means responsive web, not native apps]
- **[A4]** [e.g., Data volume is moderate; no big-data or distributed processing required]

---

## 10. Constraints

Hard limits the solution must respect.

- **Technical:** [e.g., Must integrate with existing Salesforce instance]
- **Budget / Time:** [e.g., MVP must ship within 3 months]
- **Regulatory:** [e.g., Data must remain in EU region]
- **Organizational:** [e.g., Engineering team is 4 developers, all fullstack]

---

## 11. Open Questions

Items that need a decision or more information before or during development.

| # | Question | Owner | Due |
|---|----------|-------|-----|
| 1 | [e.g., Should existing records be migrated or users start fresh?] | Product | Before Sprint 1 |
| 2 | [e.g., What is the retention policy for deleted records?] | Legal / Compliance | Before Sprint 2 |

---

## 12. Out of Scope (Parking Lot)

Ideas or features that came up but are explicitly deferred to a later phase.

- [Feature / idea] — reason for deferral

---

## 13. Glossary

Define domain-specific or project-specific terms to ensure consistent interpretation.

| Term | Definition |
|------|------------|
| [Term] | [Plain-language definition] |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Author] | Initial draft |
```

---

## Section guidance

### When to keep vs. drop sections

| Section | Keep when... | Drop when... |
|---------|-------------|--------------|
| Background | Context isn't obvious | It's a trivial internal task |
| Personas | Multiple distinct user types | Single, obvious user type |
| Data Architecture | Greenfield system or complex data model | Small feature with no new data |
| Integration Points | External systems involved | Self-contained feature |
| User Flows | Complex multi-step workflows | Simple CRUD operations |
| Glossary | Domain has specialized terminology | Common everyday terms only |

### Calibrating detail level

- **One-liner or 3-bullet input** → 1–2 page spec, 2–4 epics, light non-functional requirements
- **Meeting transcript or feature list** → 3–6 page spec, full epics with stories, all sections
- **Detailed ADR or technical brief** → Full spec, deep data model, explicit integration specs, risk section