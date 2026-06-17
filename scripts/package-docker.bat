@echo off
setlocal EnableExtensions

rem Package AI Tools Token Tracker for Docker Compose deployment
rem Stack: Python FastAPI backend + React frontend + PostgreSQL
rem Usage: package-docker.bat [archive-path]

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"

if "%~1"=="" (
  set "ARCHIVE_PATH=%ROOT_DIR%\ai-tools-token-tracker.zip"
) else (
  for %%I in ("%~1") do set "ARCHIVE_PATH=%%~fI"
)

where tar >nul 2>&1
if errorlevel 1 (
  echo tar is required to create the deployment archive. >&2
  echo Use Windows 10+ built-in tar or install tar for Windows. >&2
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0package-docker.write.ps1" -RootDir "%ROOT_DIR%"
if errorlevel 1 (
  echo Failed to write deployment files. >&2
  exit /b 1
)

if exist "%ARCHIVE_PATH%" del /f /q "%ARCHIVE_PATH%"

pushd "%ROOT_DIR%"
tar -a -c -f "%ARCHIVE_PATH%" ^
  --exclude=.git ^
  --exclude=.env ^
  --exclude=*.env ^
  --exclude=*/.env ^
  --exclude=*/*/.env ^
  --exclude=.DS_Store ^
  --exclude=*/.DS_Store ^
  --exclude=node_modules ^
  --exclude=frontend/node_modules ^
  --exclude=frontend/dist ^
  --exclude=backend/data ^
  --exclude=backend/__pycache__ ^
  --exclude=backend/.pytest_cache ^
  --exclude=*.zip ^
  --exclude=presales.pem ^
  --exclude=agent-transcripts ^
  --exclude=.cursor ^
  .
set "TAR_ERROR=%ERRORLEVEL%"
popd

if not "%TAR_ERROR%"=="0" (
  echo Failed to create archive: %ARCHIVE_PATH% >&2
  exit /b 1
)

echo Created %ARCHIVE_PATH%
echo.
echo Package includes:
echo   docker-compose.yml  (postgres + api + frontend^)
echo   backend/            (Python FastAPI^)
echo   frontend/           (React Vite^)
echo   deploy/.env.example (production env template^)
echo   deploy/nginx.example.conf  (host nginx template^)
echo   DEPLOY.txt          (deployment instructions^)
echo.
echo Linux deploy: ./scripts/deploy-docker.sh ai-tools-token-tracker.zip
exit /b 0
