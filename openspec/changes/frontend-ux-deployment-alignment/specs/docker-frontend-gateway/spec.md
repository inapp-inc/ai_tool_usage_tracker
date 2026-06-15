# Delta Spec: Docker Frontend Gateway

## ADDED Requirements

### Requirement: Production frontend container

The stack SHALL serve the React SPA and proxy API traffic through the `frontend` container in production Compose profiles.

#### Scenario: Single public port

- **GIVEN** `docker compose -f docker-compose.yml -f docker-compose.prod.yml up`
- **WHEN** the stack is healthy
- **THEN** host port `${APP_PORT:-4501}` SHALL expose the frontend nginx listener
- **AND** the API container SHALL NOT publish a public host port in production override

#### Scenario: SPA base path

- **GIVEN** production build with `VITE_BASE_PATH=/aitool`
- **WHEN** a user opens `https://foundry.inapp.com/aitool/`
- **THEN** the SPA SHALL load with router basename `/aitool`

#### Scenario: API reverse proxy

- **GIVEN** nginx config in `frontend/nginx.conf`
- **WHEN** the client calls `/aitool/api/v1/*`
- **THEN** nginx SHALL proxy to the internal `api` service at `/api/v1/*`

#### Scenario: Dev Vite profile

- **GIVEN** Compose profile `frontend-dev`
- **WHEN** developers run Vite locally or via `frontend-dev` service
- **THEN** hot reload remains available on port `5173` without nginx gateway
