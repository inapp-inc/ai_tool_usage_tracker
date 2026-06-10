# JWT Authentication — Delta Specification

## ADDED Requirements

### Requirement: User login with JWT issuance

The system SHALL authenticate users via `POST /api/v1/auth/login` and return a JWT access token on valid credentials per OpenAPI `TokenResponse`.

#### Scenario: Successful login

- **GIVEN** an active user with valid email and password
- **WHEN** the user submits a valid `LoginRequest` to `POST /api/v1/auth/login`
- **THEN** the response status is 200
- **AND** the response body contains `access_token`, `token_type` of `Bearer`, and `expires_in`
- **AND** a refresh token is included when rotation is enabled

#### Scenario: Invalid credentials

- **GIVEN** a login request with incorrect email or password
- **WHEN** `POST /api/v1/auth/login` is called
- **THEN** the response status is 401
- **AND** the response body is RFC 9457 Problem Details with title indicating invalid credentials

#### Scenario: Inactive user login blocked

- **GIVEN** a user account with `active = false`
- **WHEN** valid credentials are submitted to login
- **THEN** the response status is 401

### Requirement: Access token refresh with rotation

The system SHALL support `POST /api/v1/auth/refresh` to exchange a valid refresh token for a new access token and rotated refresh token.

#### Scenario: Successful token refresh

- **GIVEN** a valid, non-revoked refresh token
- **WHEN** `POST /api/v1/auth/refresh` is called with the refresh token
- **THEN** the response status is 200 with a new `TokenResponse`
- **AND** the prior refresh token is revoked in the database

#### Scenario: Invalid refresh token

- **GIVEN** an expired, revoked, or unknown refresh token
- **WHEN** `POST /api/v1/auth/refresh` is called
- **THEN** the response status is 401

### Requirement: Current user profile

The system SHALL expose `GET /api/v1/auth/me` returning the authenticated user's profile including role and team memberships.

#### Scenario: Authenticated profile retrieval

- **GIVEN** a valid JWT access token for an active user
- **WHEN** `GET /api/v1/auth/me` is called with `Authorization: Bearer <token>`
- **THEN** the response status is 200
- **AND** the body matches OpenAPI `UserProfile` with `id`, `email`, `role`, `organization_id`, and `team_ids`

#### Scenario: Unauthenticated profile request

- **GIVEN** no Authorization header or an invalid token
- **WHEN** `GET /api/v1/auth/me` is called
- **THEN** the response status is 401

### Requirement: Expired JWT rejected

The system SHALL reject expired JWT access tokens on protected endpoints.

#### Scenario: Expired access token

- **GIVEN** an access token whose expiry is in the past
- **WHEN** a protected API request is made with that token
- **THEN** the response status is 401 Unauthorized

### Requirement: Login rate limiting

The system SHALL rate-limit failed login attempts to mitigate brute-force attacks per NFR-SEC-003.

#### Scenario: Login throttled after threshold

- **GIVEN** repeated failed login attempts from the same client exceeding the configured threshold
- **WHEN** an additional login attempt is made
- **THEN** the response status is 429
- **AND** subsequent attempts remain throttled until the window expires

### Requirement: JWT signing key from environment

The system SHALL load JWT signing secrets from environment variables or Docker Compose secrets, not from source code.

#### Scenario: Missing JWT secret prevents startup

- **GIVEN** required JWT signing environment variables are unset in non-dev environments
- **WHEN** the API application starts
- **THEN** startup fails with a clear configuration error
