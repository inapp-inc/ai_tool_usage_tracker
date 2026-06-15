# Delta Spec: Auth Session Persistence

## MODIFIED Requirements

### Requirement: Session restore on reload

The SPA SHALL restore an authenticated session after full page reload when valid tokens exist in tab-scoped storage.

#### Scenario: Reload with valid tokens

- **GIVEN** access and refresh tokens in `sessionStorage`
- **WHEN** the user reloads the application
- **THEN** `AuthProvider` SHALL bootstrap auth state via `GET /api/v1/auth/me`
- **AND** the user SHALL remain on protected routes without re-entering credentials

#### Scenario: Invalid tokens cleared

- **GIVEN** expired or invalid tokens in `sessionStorage`
- **WHEN** bootstrap fails with 401
- **THEN** tokens SHALL be cleared and the user redirected to `/login`

#### Scenario: Token storage

- **GIVEN** successful login or refresh
- **WHEN** tokens are persisted
- **THEN** access and refresh tokens MAY be stored in `sessionStorage` (tab-scoped)
- **AND** `localStorage` SHALL NOT be used for production token storage

#### Scenario: Authenticated root redirect

- **GIVEN** an authenticated user navigates to `/`
- **WHEN** `RootRedirect` runs
- **THEN** the browser SHALL navigate to `/insights`
