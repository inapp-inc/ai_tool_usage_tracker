# OpenSpec Functional Requirements

Functional requirements for the **AI Tool Usage Tracker** platform, derived from [project.md](../../Source-code/project.md) and [openspec/project.md](../project.md).

## Document Structure

| Document | Module | Feature IDs |
|----------|--------|-------------|
| [01-administration.md](./01-administration.md) | Administration | FR-ADM-001 – FR-ADM-004 |
| [02-dashboards.md](./02-dashboards.md) | Dashboards | FR-DSH-001 – FR-DSH-009 |
| [03-usage-tracking.md](./03-usage-tracking.md) | Usage Tracking | FR-USG-001 – FR-USG-002 |
| [04-reporting.md](./04-reporting.md) | Reporting | FR-RPT-001 – FR-RPT-007 |
| [05-notifications.md](./05-notifications.md) | Notifications | FR-NTF-001 – FR-NTF-003 |
| [06-usage-ingestion.md](./06-usage-ingestion.md) | Individual Usage Monitoring | FR-ING-001 – FR-ING-004 |
| [07-platform-security.md](./07-platform-security.md) | Platform, Security & NFRs | FR-PLT-001 – FR-PLT-004 |
| [NFR.md](./NFR.md) | Non-Functional Specifications | NFR-SEC / PER / SCL / AVL / MON / AUD / ACC / CMP / BKP / LOC |

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Must-have for Phase 1 (MVP); release blocker |
| **P1** | Should-have for Phase 1; required for full MVP scope |
| **P2** | Phase 2 or deferred enhancement |

## Roles Reference

| Role | Abbreviation |
|------|--------------|
| Super Admin | SA |
| Team Admin | TA |
| Finance Viewer | FV |
| Team Member | TM |
| Auditor | AU |

## Traceability

Each feature includes user stories mapped to roles, testable acceptance criteria (Given/When/Then), explicit business rules, and upstream/downstream dependencies for OpenSpec spec and SEED unit decomposition.

**Test strategy:** [../specifications/testing.md](../specifications/testing.md) · **Traceability index:** [../specifications/testing-traceability.md](../specifications/testing-traceability.md)

**Dynamic providers:** [../specifications/provider-creation.md](../specifications/provider-creation.md) — configure vendor HTTP integrations in Settings without new adapter code.

## Implementation Specifications

| Feature | Document |
|---------|----------|
| Authentication | [authentication.md](../specifications/features/authentication.md) |

**Deployment:** [../specifications/deployment.md](../specifications/deployment.md) · [deployment-checklist.md](../specifications/deployment-checklist.md) · **ADR-013** Docker Compose + local storage

## Related Architecture

- Solution architecture: [../architecture/README.md](../architecture/README.md)
- Architecture decisions (ADRs): [../decisions/README.md](../decisions/README.md)
- Implementation tasks: [../tasks/README.md](../tasks/README.md)
