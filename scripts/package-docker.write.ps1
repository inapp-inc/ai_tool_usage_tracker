param(

    [Parameter(Mandatory = $true)]

    [string]$RootDir

)



$dockerignore = @'

.git

.env

*.env

!*.env.example

**/.env

**/*.env

.DS_Store

**/.DS_Store

node_modules

**/node_modules

frontend/dist

frontend/node_modules

backend/data

backend/__pycache__

backend/**/__pycache__

backend/.pytest_cache

**/*.pyc

**/*.pyo

**/*.log

*.zip

presales.pem

agent-transcripts

.cursor

'@



$envExample = @'

POSTGRES_USER=tokentracker

POSTGRES_PASSWORD=tokentracker

POSTGRES_DB=tokentracker

APP_SECRET_KEY=change-me-in-production

APP_ENV=production

APP_LOG_LEVEL=INFO

FRONTEND_URL=https://foundry.inapp.com/aitool

VITE_BASE_PATH=/aitool/

BACKEND_PORT=4500

APP_PORT=4501

'@



$deployNotes = @'

AI Tools Token Tracker - Docker Deployment Package

==================================================



Stack:

  - PostgreSQL 16 (postgres)

  - Python FastAPI backend (BACKEND_PORT, default 4500)

  - React Vite frontend (APP_PORT, default 4501)

  - Host nginx on server routes /aitool/ (see deploy/nginx.example.conf)



Quick start (Linux):

  1. ./scripts/deploy-docker.sh ai-tools-token-tracker-docker.zip



Manual start:

  1. Copy .env.example to .env and update secrets/passwords

  2. Set APP_ENV=production, BACKEND_PORT and APP_PORT (4500+ range)

  3. docker compose up --build -d

  4. Open http://localhost:4501/aitool (frontend) and http://localhost:4500/health (backend)



Default demo login (after seed):

  admin@demo.com / demo1234



Services:

  postgres   - database

  bootstrap  - one-shot DB init + seed

  backend    - FastAPI API (BACKEND_PORT -> container 8000)

  frontend   - React app (APP_PORT -> container 80)



Production env (.env):

  APP_ENV=production

  BACKEND_PORT=4500

  APP_PORT=4501

  VITE_BASE_PATH=/aitool/



Host nginx (production):

  deploy/nginx.example.conf



Useful commands:

  docker compose logs -f backend

  docker compose down

  docker compose down -v   (reset database)

'@



[IO.File]::WriteAllText((Join-Path $RootDir '.dockerignore'), $dockerignore)

[IO.File]::WriteAllText((Join-Path $RootDir '.env.example'), $envExample)

[IO.File]::WriteAllText((Join-Path $RootDir 'DEPLOY.txt'), $deployNotes)



# Remove obsolete single-container Dockerfile from older packaging scripts

$legacyDockerfile = Join-Path $RootDir 'Dockerfile'

if (Test-Path $legacyDockerfile) {

    Remove-Item -Force $legacyDockerfile

}

