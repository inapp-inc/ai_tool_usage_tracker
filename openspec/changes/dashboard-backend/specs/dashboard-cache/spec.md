# Dashboard Cache — Delta Specification

## ADDED Requirements

### Requirement: Cache-aside for dashboard reads

The system SHALL cache dashboard widget responses in Redis using cache-aside pattern per ADR-008 with configurable TTL between 1 and 5 minutes.

#### Scenario: Cache miss loads from database

- **GIVEN** no cached entry for a dashboard query key
- **WHEN** a dashboard widget endpoint is called
- **THEN** the response is computed from `usage.usage_aggregates`
- **AND** the serialized response is stored in Redis with TTL

#### Scenario: Cache hit returns stored response

- **GIVEN** a valid cached entry for the query key
- **WHEN** the same dashboard widget request is repeated within TTL
- **THEN** the response is served from Redis without querying aggregates

### Requirement: Tenant-safe cache keys

The system SHALL include organization id, RBAC scope hash, endpoint name, and normalized filter parameters in cache keys.

#### Scenario: Cross-tenant cache isolation

- **GIVEN** cached dashboard data for organization A
- **WHEN** a user from organization B requests the same widget with identical date filters
- **THEN** organization B receives data computed for organization B only
- **AND** organization A cache entry is not returned

### Requirement: Cache invalidation on data changes

The system SHALL invalidate affected dashboard cache keys when usage aggregates refresh, tool pricing changes, or team membership changes.

#### Scenario: Invalidation after aggregate refresh

- **GIVEN** cached token widget data for an organization
- **WHEN** usage aggregates are refreshed for that organization
- **THEN** affected cache keys are deleted
- **AND** the next request recomputes from updated aggregates
