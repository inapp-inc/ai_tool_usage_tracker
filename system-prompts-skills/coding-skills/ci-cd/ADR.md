# Architectural Decision Records — CI/CD

**Project:** InAppTMO CI/CD Implementation
**Document Version:** 1.0 | **Date:** 01-Feb-2024
**Author:** Nithin Prince John | **Reviewer:** Mohamed Rijaz

---

## ADR-001: Adopt Pipeline-as-Code

**Status:** Accepted

**Context:**
CI/CD pipelines configured via GUI tools are not version-controlled, difficult to audit, and hard to replicate across teams or environments.

**Decision:**
All CI/CD pipelines must be defined as code (Jenkinsfile for Jenkins, YAML for GitHub Actions / GitLab CI/CD) and committed alongside the application source.

**Consequences:**
- Pipelines are versioned, reviewable, and reproducible.
- Changes to pipeline logic require the same code review process as application changes.
- Onboarding new environments is faster and less error-prone.

---

## ADR-002: Automate All Build, Test, and Deployment Steps

**Status:** Accepted

**Context:**
Manual build and deployment steps introduce human error, slow delivery, and inconsistency across environments.

**Decision:**
Every stage of the software delivery lifecycle — build (Maven/Gradle/Webpack), test (unit/integration/e2e), and deploy — must be fully automated within the pipeline.

**Consequences:**
- Developers are freed from repetitive manual tasks.
- Failures are detected earlier and more consistently.
- Requires investment in writing and maintaining automated tests.

---

## ADR-003: Use Containerisation for Environment Consistency

**Status:** Accepted

**Context:**
"Works on my machine" issues arise from environment differences between developer laptops, CI runners, staging, and production.

**Decision:**
All application workloads must be containerised with Docker. Container images are the deployable artifact promoted through each environment stage.

**Consequences:**
- Consistent runtime across all stages.
- Build once, deploy anywhere.
- Teams must be proficient in Docker and container best practices.

---

## ADR-004: Store Secrets in a Dedicated Vault

**Status:** Accepted

**Context:**
Hardcoding secrets (API keys, database credentials, tokens) in source code or pipeline YAML files creates significant security risk.

**Decision:**
All sensitive configuration must be stored in HashiCorp Vault or AWS Secrets Manager and injected at runtime. No secret may appear in version-controlled files.

**Consequences:**
- Significantly reduced risk of credential exposure.
- Requires vault infrastructure setup and access policy management.
- Slightly increases pipeline complexity during initial setup.

---

## ADR-005: Implement Blue-Green Deployment for Production

**Status:** Accepted

**Context:**
Rolling deployments that update in place carry the risk of partial failures visible to end-users and slower rollback times.

**Decision:**
Production deployments use blue-green strategy: a parallel "green" environment is prepared and tested, then traffic is switched from "blue" (current) to "green" (new). The previous blue environment is retained briefly for rapid rollback.

**Consequences:**
- Zero-downtime deployments.
- Instant rollback by redirecting traffic.
- Requires maintaining two full production environments simultaneously (higher short-term cost).

---

## ADR-006: Embed Security Scanning in the Pipeline

**Status:** Accepted

**Context:**
Security vulnerabilities discovered late in the delivery lifecycle are expensive to fix and may block releases.

**Decision:**
Security scanning (OWASP ZAP, Nessus, SCA tools) must run as a mandatory pipeline stage. Pre-commit hooks perform lightweight checks locally. Builds that introduce high-severity vulnerabilities are blocked.

**Consequences:**
- Security issues are surfaced early ("shift left").
- Initial pipeline execution time increases slightly.
- Teams must triage and remediate scanner findings as part of the development workflow.

---

## ADR-007: Manage Infrastructure with IaC

**Status:** Accepted

**Context:**
Manually provisioned infrastructure is not reproducible, difficult to audit, and prone to configuration drift.

**Decision:**
All infrastructure (servers, networking, storage, cloud resources) must be defined and managed using Infrastructure as Code tools — Terraform, Pulumi, or AWS CloudFormation.

**Consequences:**
- Infrastructure is versioned and auditable.
- Environments can be recreated reliably from code.
- Requires IaC skills within the team.

---

## ADR-008: Isolate Environments (Dev / Staging / Production)

**Status:** Accepted

**Context:**
Shared or poorly isolated environments cause test contamination, accidental data mutation, and unpredictable deployment behaviour.

**Decision:**
Each environment (development, staging, production) must be fully isolated with its own configuration, secrets, and compute resources. Staging must mirror production as closely as possible.

**Consequences:**
- Reliable pre-production validation.
- Higher infrastructure cost due to environment duplication.
- Clearer blast radius if an environment has an incident.
