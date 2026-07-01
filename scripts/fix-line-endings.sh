#!/usr/bin/env bash
# Fix Windows CRLF in shell scripts on Linux/macOS.
# Always invoke explicitly (works even when this file has CRLF):
#   bash scripts/fix-line-endings.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixed=0

while IFS= read -r -d '' script; do
  if grep -q $'\r' "$script" 2>/dev/null; then
    if sed -i 's/\r$//' "$script" 2>/dev/null; then
      :
    else
      sed -i '' 's/\r$//' "$script"
    fi
    chmod +x "$script" 2>/dev/null || true
    echo "Fixed: $script"
    fixed=$((fixed + 1))
  fi
done < <(find "$ROOT_DIR" -name '*.sh' -type f -print0)

if [[ "$fixed" -eq 0 ]]; then
  echo "All shell scripts already use Unix (LF) line endings."
else
  echo "Normalized $fixed script(s). You can now run ./scripts/deploy-docker.sh"
fi
