#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
find "$ROOT" -name '*.sh' -type f -exec sed -i 's/\r$//' {} + 2>/dev/null || true
chmod +x "$ROOT"/scripts/*.sh "$ROOT"/backend/docker-entrypoint.sh 2>/dev/null || true
ZIP="${1:-}"
if [[ -z "$ZIP" ]]; then
  echo "Usage: sudo bash deploy-production.sh ai-tools-token-tracker.zip" >&2
  exit 1
fi
if [[ ! -f "$ZIP" ]]; then
  echo "Archive not found: $ZIP" >&2
  exit 1
fi
exec bash "$ROOT/scripts/deploy-docker.sh" "$ZIP"