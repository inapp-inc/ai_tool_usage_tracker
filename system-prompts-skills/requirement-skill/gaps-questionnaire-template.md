# Gaps Questionnaire: [Project / Feature Name]

**Purpose:** Capture unknowns, assumptions, and gaps between stated needs and current system behavior before writing the Functional Specification Document (FSD). Once filled, this questionnaire is the primary input for FSD creation.

**Version:** 1.0  
**Date:** [YYYY-MM-DD]  
**Status:** Draft / In progress / Complete

---

## How to use

1. **Generate** this questionnaire during the requirement analysis phase (e.g., from user stories, discovery notes, or stakeholder input).
2. **Fill** each section: add answers, owner, and confidence where applicable.
3. **Use** the filled questionnaire to create or update the FSD (`requirement-skill/fsd-template.md`).
4. Keep the questionnaire and FSD traceable (e.g., reference questionnaire section IDs in FSD requirements).

---

## 1. Functional gaps

| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |
|----|----------------|--------|-------|--------------------|
| F1 | [e.g., Which user roles must be supported in v1?] | | | |
| F2 | [e.g., Is approval workflow required or optional?] | | | |
| F3 | | | | |

*Add rows as needed. Confidence: H = decided/verified, M = assumed, L = unknown.*

---

## 2. Data and domain gaps

| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |
|----|----------------|--------|-------|--------------------|
| D1 | [e.g., What is the source of truth for customer data?] | | | |
| D2 | [e.g., Retention and archival rules for generated reports?] | | | |
| D3 | | | | |

---

## 3. Integration and API gaps

| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |
|----|----------------|--------|-------|--------------------|
| I1 | [e.g., Which external systems must we integrate with, and which endpoints?] | | | |
| I2 | [e.g., Auth mechanism for third-party API (OAuth, API key)?] | | | |
| I3 | [e.g., Sync frequency and error handling for each integration?] | | | |

---

## 4. Non-functional and constraints

| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |
|----|----------------|--------|-------|--------------------|
| N1 | [e.g., Performance targets (latency, throughput)?] | | | |
| N2 | [e.g., Security and compliance requirements (RBAC, encryption, audit)?] | | | |
| N3 | [e.g., Scalability or availability targets?] | | | |
| N4 | [e.g., Hard constraints: budget, timeline, tech stack?] | | | |

---

## 5. Scope and out-of-scope

| ID | Question / Gap | Answer | Owner | Confidence (H/M/L) |
|----|----------------|--------|-------|--------------------|
| S1 | [e.g., Explicitly out of scope for this phase?] | | | |
| S2 | [e.g., Deferred to a later release?] | | | |

---

## 6. Open decisions

| ID | Decision needed | Options | Owner | Due |
|----|-----------------|---------|-------|-----|
| O1 | [e.g., Migrate existing data vs. greenfield?] | [Option A; Option B] | | |
| O2 | | | | |

---

## 7. Traceability to FSD

After FSD creation, optionally link questionnaire items to FSD sections:

| Questionnaire ID | FSD section / requirement |
|------------------|---------------------------|
| F1, F2 | Section 5, Epic 1 |
| D1 | Section 7, Data model |
| I1, I2 | Section 7, Integration points; OpenAPI spec |

---

*Keep this document updated when answers change so the FSD and implementation stay aligned.*
