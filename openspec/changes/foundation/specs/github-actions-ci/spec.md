# GitHub Actions CI — Delta Specification

## ADDED Requirements

### Requirement: Pull request pipeline

The system SHALL run automated checks on pull requests per TASK-INF-005 and NFR-SEC-007.

#### Scenario: CI runs lint and tests

- **GIVEN** a pull request modifying backend code
- **WHEN** the CI workflow triggers
- **THEN** ruff, mypy, and pytest jobs execute

#### Scenario: OpenAPI lint in CI

- **GIVEN** changes to OpenAPI specification
- **WHEN** CI runs
- **THEN** Redocly lint passes on `openspec/specifications/apis/openapi.yaml`

### Requirement: Security scanning in CI

The system SHALL run bandit and pip-audit on backend dependencies in CI.

#### Scenario: Security scan job completes

- **GIVEN** a pull request
- **WHEN** security scan job runs
- **THEN** bandit and pip-audit complete without critical findings on baseline
