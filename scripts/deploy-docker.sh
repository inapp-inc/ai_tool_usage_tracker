#!/usr/bin/env bash
set -euo pipefail

# Deploy AI Tools Token Tracker on Linux using docker compose.
# Host nginx is configured separately on the server (see deploy/nginx.example.conf).
#
# Usage:
#   ./scripts/deploy-docker.sh [archive-path]
#
# Environment overrides:
#   DEPLOY_ROOT=/var/www/ai-tools-token-tracker
#   APP_NAME=ai-tools-token-tracker
#   PUBLIC_ORIGIN=https://foundry.inapp.com
#   ENV_FILE=/path/to/.env

ARCHIVE_PATH="${1:-ai-tools-token-tracker.zip}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/var/www/ai-tools-token-tracker}"
APP_NAME="${APP_NAME:-ai-tools-token-tracker}"
PUBLIC_ORIGIN="${PUBLIC_ORIGIN:-http://localhost}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$APP_NAME}"

POSTGRES_USER="${POSTGRES_USER:-tokentracker}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-tokentracker}"
POSTGRES_DB="${POSTGRES_DB:-tokentracker}"

PORT_RANGE_START="${PORT_RANGE_START:-4500}"
PORT_RANGE_END="${PORT_RANGE_END:-4599}"

command -v docker >/dev/null 2>&1 || {
  echo "docker is required on the destination host." >&2
  exit 1
}
command -v unzip >/dev/null 2>&1 || {
  echo "unzip is required on the destination host." >&2
  exit 1
}

COMPOSE_CMD=()
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "docker compose (plugin) or docker-compose is required." >&2
  exit 1
fi

env_value() {
  local file="$1"
  local key="$2"
  [[ -f "$file" ]] || return 0
  awk -F= -v key="$key" '
    $0 !~ /^[[:space:]]*#/ && $1 == key {
      sub(/^[^=]*=/, "", $0)
      gsub(/^["'\'']|["'\'']$/, "", $0)
      print $0
      exit
    }
  ' "$file"
}

ensure_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  if [[ -z "$(env_value "$file" "$key" || true)" ]]; then
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

set_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  local tmp="${file}.tmp"
  if [[ -f "$file" ]] && grep -qE "^${key}=" "$file"; then
    awk -v key="$key" -v value="$value" '
      BEGIN { replaced = 0 }
      $0 ~ "^" key "=" {
        print key "=" value
        replaced = 1
        next
      }
      { print }
      END {
        if (!replaced) print key "=" value
      }
    ' "$file" > "$tmp"
    mv "$tmp" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

is_port_free() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ! ss -ltn "( sport = :$port )" | grep -q ":$port"
  elif command -v lsof >/dev/null 2>&1; then
    ! lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v netstat >/dev/null 2>&1; then
    ! netstat -ltn | grep -q ":$port "
  else
    ! (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

choose_port() {
  local preferred="${1:-}"
  local start="${2:-4500}"
  local end="${3:-4599}"
  if [[ -n "$preferred" ]] && is_port_free "$preferred"; then
    echo "$preferred"
    return 0
  fi
  for port in $(seq "$start" "$end"); do
    if is_port_free "$port"; then
      echo "$port"
      return 0
    fi
  done
  echo "No free port found in ${start}-${end}." >&2
  return 1
}

choose_distinct_port() {
  local preferred="${1:-}"
  local start="${2:-4500}"
  local end="${3:-4599}"
  local exclude="${4:-}"
  if [[ -n "$preferred" && "$preferred" != "$exclude" ]] && is_port_free "$preferred"; then
    echo "$preferred"
    return 0
  fi
  for port in $(seq "$start" "$end"); do
    if [[ "$port" == "$exclude" ]]; then
      continue
    fi
    if is_port_free "$port"; then
      echo "$port"
      return 0
    fi
  done
  echo "No free port found in ${start}-${end} (excluding ${exclude})." >&2
  return 1
}

if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Archive not found: $ARCHIVE_PATH" >&2
  exit 1
fi
ARCHIVE_PATH="$(cd "$(dirname "$ARCHIVE_PATH")" && pwd)/$(basename "$ARCHIVE_PATH")"

mkdir -p "$DEPLOY_ROOT"
unzip -oq "$ARCHIVE_PATH" -d "$DEPLOY_ROOT"

if [[ ! -f "$DEPLOY_ROOT/docker-compose.yml" ]]; then
  echo "Invalid archive: docker-compose.yml not found in $DEPLOY_ROOT" >&2
  exit 1
fi

DEST_ENV_FILE="${ENV_FILE:-}"
if [[ -z "$DEST_ENV_FILE" ]]; then
  for candidate in \
    "$DEPLOY_ROOT/.env" \
    "/etc/${APP_NAME}.env" \
    "/etc/tokentracker.env"; do
    if [[ -f "$candidate" ]]; then
      DEST_ENV_FILE="$candidate"
      break
    fi
  done
fi

if [[ -z "$DEST_ENV_FILE" ]]; then
  DEST_ENV_FILE="$DEPLOY_ROOT/.env"
fi

if [[ ! -f "$DEST_ENV_FILE" ]]; then
  if [[ -f "$DEPLOY_ROOT/.env.example" ]]; then
    cp "$DEPLOY_ROOT/.env.example" "$DEST_ENV_FILE"
    echo "Created $DEST_ENV_FILE from .env.example"
  else
    touch "$DEST_ENV_FILE"
    echo "Created empty $DEST_ENV_FILE"
  fi
else
  echo "Using env file: $DEST_ENV_FILE"
fi

APP_SECRET_VALUE="$(env_value "$DEST_ENV_FILE" APP_SECRET_KEY || true)"
if [[ -z "$APP_SECRET_VALUE" || "$APP_SECRET_VALUE" == "change-me-in-production" || "$APP_SECRET_VALUE" == "dev-insecure-change-me" ]]; then
  APP_SECRET_VALUE="$(openssl rand -hex 32 2>/dev/null || date +%s%N)"
  set_env_value "$DEST_ENV_FILE" "APP_SECRET_KEY" "$APP_SECRET_VALUE"
  echo "Generated APP_SECRET_KEY"
fi

ensure_env_value "$DEST_ENV_FILE" "POSTGRES_USER" "$POSTGRES_USER"
ensure_env_value "$DEST_ENV_FILE" "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
ensure_env_value "$DEST_ENV_FILE" "POSTGRES_DB" "$POSTGRES_DB"
set_env_value "$DEST_ENV_FILE" "APP_ENV" "production"
set_env_value "$DEST_ENV_FILE" "APP_LOG_LEVEL" "INFO"

PREFERRED_BACKEND_PORT="$(env_value "$DEST_ENV_FILE" BACKEND_PORT || true)"
BACKEND_PORT="$(choose_port "$PREFERRED_BACKEND_PORT" "$PORT_RANGE_START" "$PORT_RANGE_END")"
set_env_value "$DEST_ENV_FILE" "BACKEND_PORT" "$BACKEND_PORT"

PREFERRED_APP_PORT="$(env_value "$DEST_ENV_FILE" APP_PORT || true)"
APP_PORT="$(choose_distinct_port "$PREFERRED_APP_PORT" "$PORT_RANGE_START" "$PORT_RANGE_END" "$BACKEND_PORT")"
set_env_value "$DEST_ENV_FILE" "APP_PORT" "$APP_PORT"

BASE_PATH="$(env_value "$DEST_ENV_FILE" VITE_BASE_PATH || true)"
BASE_PATH="${BASE_PATH:-/aitool/}"
BASE_PATH="${BASE_PATH%/}"
set_env_value "$DEST_ENV_FILE" "VITE_BASE_PATH" "${BASE_PATH}/"

if [[ "$PUBLIC_ORIGIN" == "http://localhost" ]]; then
  PUBLIC_ORIGIN="http://127.0.0.1:${APP_PORT}${BASE_PATH}"
elif [[ "$PUBLIC_ORIGIN" != *"${BASE_PATH}" ]]; then
  PUBLIC_ORIGIN="${PUBLIC_ORIGIN%/}${BASE_PATH}"
fi
set_env_value "$DEST_ENV_FILE" "FRONTEND_URL" "$PUBLIC_ORIGIN"

if [[ "$DEST_ENV_FILE" != "$DEPLOY_ROOT/.env" ]]; then
  ln -sfn "$DEST_ENV_FILE" "$DEPLOY_ROOT/.env"
  echo "Linked $DEPLOY_ROOT/.env -> $DEST_ENV_FILE"
fi

export COMPOSE_PROJECT_NAME

cd "$DEPLOY_ROOT"
echo "Building and starting stack (postgres + backend + frontend)..."
"${COMPOSE_CMD[@]}" down >/dev/null 2>&1 || true
"${COMPOSE_CMD[@]}" up --build -d

echo "Waiting for backend health on port ${BACKEND_PORT}..."
ready=0
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done

cat <<EOF

Deployed AI Tools Token Tracker
===============================
Project:      $COMPOSE_PROJECT_NAME
Deploy root:  $DEPLOY_ROOT
Env file:     $DEST_ENV_FILE
APP_ENV:      production

Backend:      http://127.0.0.1:${BACKEND_PORT}
Frontend:     http://127.0.0.1:${APP_PORT}${BASE_PATH}/
Health:       http://127.0.0.1:${BACKEND_PORT}/health
API docs:     http://127.0.0.1:${BACKEND_PORT}/api/v1/docs
Public URL:   $PUBLIC_ORIGIN

Default login (seeded):
  admin@demo.com / demo1234

Configure host nginx using:
  $DEPLOY_ROOT/deploy/nginx.example.conf
  (replace BACKEND_PORT=${BACKEND_PORT} and APP_PORT=${APP_PORT})

Useful commands:
  cd $DEPLOY_ROOT
  ${COMPOSE_CMD[*]} ps
  ${COMPOSE_CMD[*]} logs -f backend
  ${COMPOSE_CMD[*]} down
  ${COMPOSE_CMD[*]} down -v    # reset database

Suggested host nginx routes:

  location /aitool/api/ {
    proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }

  location /aitool/health {
    proxy_pass http://127.0.0.1:${BACKEND_PORT}/health;
  }

  location /aitool/ {
    proxy_pass http://127.0.0.1:${APP_PORT}/aitool/;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
  }
EOF

if [[ "$ready" -ne 1 ]]; then
  echo
  echo "Warning: health check did not pass within 120s. Check logs:" >&2
  echo "  cd $DEPLOY_ROOT && ${COMPOSE_CMD[*]} logs" >&2
  exit 1
fi
