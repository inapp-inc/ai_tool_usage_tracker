param(
    [Parameter(Mandatory = $true)]
    [string]$RootDir
)

$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

function Write-LfFile {
    param(
        [string]$Path,
        [string]$Content
    )
    $normalized = ($Content -replace "`r`n", "`n") -replace "`r", "`n"
    [IO.File]::WriteAllText($Path, $normalized, $Utf8NoBom)
}

function Convert-ShFilesToLf {
    param([string]$BaseDir)
    Get-ChildItem -Path $BaseDir -Recurse -Filter '*.sh' -File -ErrorAction SilentlyContinue | ForEach-Object {
        $text = [IO.File]::ReadAllText($_.FullName)
        if ($text -match "`r") {
            Write-LfFile -Path $_.FullName -Content $text
            Write-Host "LF normalized: $($_.FullName)"
        }
    }
    $entrypoint = Join-Path $BaseDir 'backend\docker-entrypoint.sh'
    if (Test-Path $entrypoint) {
        $text = [IO.File]::ReadAllText($entrypoint)
        if ($text -match "`r") {
            Write-LfFile -Path $entrypoint -Content $text
            Write-Host "LF normalized: $entrypoint"
        }
    }
}

$dockerignore = @'
.git
.env
*.env
!*.env.example
!deploy/.env.example
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

$deployNotes = @'
AI Tool Usage Tracker - Production Deploy
=========================================

Linux deploy (recommended):
  sudo bash deploy-production.sh ai-tools-token-tracker.zip

The zip contains frontend SOURCE; Docker rebuilds the SPA on the server.
Do NOT use ./scripts/deploy-docker.sh if you see bash\r errors — use bash instead.
'@

$deployProduction = @'
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
'@

Write-LfFile -Path (Join-Path $RootDir '.dockerignore') -Content $dockerignore
Write-LfFile -Path (Join-Path $RootDir 'DEPLOY.txt') -Content $deployNotes
Write-LfFile -Path (Join-Path $RootDir 'deploy-production.sh') -Content $deployProduction

$legacyDockerfile = Join-Path $RootDir 'Dockerfile'
if (Test-Path $legacyDockerfile) {
    Remove-Item -Force $legacyDockerfile
}

Convert-ShFilesToLf -BaseDir $RootDir

$sidebarPath = Join-Path $RootDir 'frontend\src\components\layout\Sidebar.tsx'
$palettePath = Join-Path $RootDir 'frontend\src\theme\palette.ts'
$sidebarStamp = if (Test-Path $sidebarPath) { (Get-Item $sidebarPath).LastWriteTimeUtc.ToString('o') } else { 'missing' }
$paletteStamp = if (Test-Path $palettePath) { (Get-Item $palettePath).LastWriteTimeUtc.ToString('o') } else { 'missing' }

$packageMeta = @"
Packaged at (UTC): $((Get-Date).ToUniversalTime().ToString('o'))
frontend/src/components/layout/Sidebar.tsx (UTC): $sidebarStamp
frontend/src/theme/palette.ts (UTC): $paletteStamp
frontend/dist: excluded (rebuilt on server via docker compose build frontend)
Deploy: bash deploy-production.sh ai-tools-token-tracker.zip
"@

Write-LfFile -Path (Join-Path $RootDir 'PACKAGE_BUILD.txt') -Content $packageMeta
Write-Host "Package metadata written to PACKAGE_BUILD.txt"
