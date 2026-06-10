# CI/CD Skills Reference

**Source:** CI/CD Implementation Guidelines v1.0 (01-Feb-2024)
**Owner:** InAppTMO | **Author:** Nithin Prince John

---

## Core Pipeline Skills

### 1. Pipeline Orchestration
- Use tools such as Jenkins, GitLab CI/CD, CircleCI, or AWS CodePipelines to define and run pipelines.
- Define pipelines as code using Jenkinsfiles or YAML (GitHub Actions / GitLab CI/CD) for versioning and replication.
- Trigger builds automatically on every push to version control.
- Halt the pipeline and notify the team immediately on any build or test failure.

### 2. Version Control & Branching
- Manage all source code with Git.
- Adopt a recognised branching strategy: Gitflow, GitHub Flow, GitLab Flow, or Trunk-Based Development.
- Enforce code reviews before merging into the main branch.

### 3. Automated Build
- Automate builds on every code push using Maven, Gradle, or Webpack as appropriate.
- Store build artifacts (Docker images, JAR files, etc.) in a secure artifact repository such as Docker Hub, Nexus, JFrog Artifactory, or AWS ECR.

### 4. Automated Testing
- Implement a full suite covering unit, integration, and end-to-end tests.
- Run all tests automatically within the pipeline.
- A failing test must block promotion to any downstream environment.

### 5. Containerization
- Package the application and its dependencies using Docker.
- Ensure a consistent runtime environment across dev, staging, and production stages.

### 6. Continuous Integration (CI)
- Trigger CI on every push or pull request.
- Enforce code quality and style rules via static analysis tools (ESLint, SonarQube).
- Reject commits that fail quality gates.

### 7. Continuous Delivery / Deployment (CD)
- Automate deployment to staging after a successful CI run.
- Use feature flags to control which features reach production.
- Apply a progressive promotion strategy: staging → production with automated or manual approvals.

### 8. Deployment Strategies
| Strategy | When to Use |
|---|---|
| **Blue-Green** | Zero-downtime releases; quick rollback by switching traffic |
| **Rolling Update** | Gradual replacement of instances; always partially available |

### 9. Configuration Management
- Never hardcode configuration values in source code.
- Manage configuration dynamically per environment (dev / staging / prod).
- Store secrets (API keys, credentials) in a dedicated vault (HashiCorp Vault, AWS Secrets Manager).

### 10. Infrastructure as Code (IaC)
- Define and version all infrastructure using Terraform, Pulumi, or AWS CloudFormation.
- Treat infrastructure changes with the same review process as application code.

### 11. Monitoring & Logging
- Integrate observability tooling (Prometheus, ELK Stack, AWS CloudWatch) into the pipeline.
- Set up alerts for performance degradation and error spikes immediately after deployment.

### 12. Rollback Strategy
- Every deployment must have a tested rollback path.
- Automate rollback triggers where possible (e.g., failed health checks).

### 13. Security Scanning
- Embed security scanning (OWASP ZAP, Nessus, SCA tools) into the pipeline.
- Run pre-commit hooks for early vulnerability detection.
- Perform Source Composition Analysis (SCA) on all third-party dependencies.

### 14. Environment Isolation
- Maintain isolated, production-like environments for each stage.
- Prevent configuration bleed between environments.

### 15. Compliance & Governance
- Ensure pipeline practices meet applicable security and compliance standards.
- Enforce audit trails for all deployments and approvals.

### 16. Scalability
- Design pipelines to scale with application growth.
- Leverage cloud-native auto-scaling for pipeline agents/runners.

### 17. Feedback Loop & Continuous Improvement
- Collect feedback from end-users and stakeholders to drive improvements.
- Conduct regular retrospectives to review and update pipeline processes.
- Document all pipeline configurations and deployment procedures.

---

## Quick Checklist

- [ ] Pipeline defined as code and version-controlled
- [ ] Automated build triggered on every push
- [ ] Unit, integration, and e2e tests run automatically
- [ ] Code quality gate enforced (linting + static analysis)
- [ ] Artifacts stored in a secure repository
- [ ] Deployment to staging automated post-CI
- [ ] Secrets stored in a vault — never in source code
- [ ] IaC used for all infrastructure
- [ ] Security scanning embedded in pipeline
- [ ] Rollback procedure documented and tested
- [ ] Monitoring and alerting active post-deployment
- [ ] Environments isolated and production-like
