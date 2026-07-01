@echo off
setlocal EnableExtensions

rem Package for Linux production deploy.
rem Usage: scripts\package-docker.bat [archive-path]
rem Deploy on server: sudo bash deploy-production.sh ai-tools-token-tracker.zip

set "ROOT_DIR=%~dp0.."
for %%I in ("%ROOT_DIR%") do set "ROOT_DIR=%%~fI"

if "%~1"=="" (
  set "ARCHIVE_PATH=%ROOT_DIR%\ai-tools-token-tracker.zip"
) else (
  for %%I in ("%~1") do set "ARCHIVE_PATH=%%~fI"
)

where tar >nul 2>&1
if errorlevel 1 (
  echo tar is required. Use Windows 10+ built-in tar. >&2
  exit /b 1
)

echo.
echo Step 1: Normalize shell scripts to LF and write deploy metadata...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\deploy\package-docker.prep.ps1" -RootDir "%ROOT_DIR%"
if errorlevel 1 (
  echo Failed to prepare deployment files. >&2
  exit /b 1
)

echo.
echo Step 2: Creating archive (frontend/src included, frontend/dist excluded)...
if exist "%ARCHIVE_PATH%" del /f /q "%ARCHIVE_PATH%"

pushd "%ROOT_DIR%"
tar -a -c -f "%ARCHIVE_PATH%" ^
  --exclude=.git ^
  --exclude=.env ^
  --exclude=*.env ^
  --exclude=*/.env ^
  --exclude=*/*/.env ^
  --exclude=.DS_Store ^
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

echo.
echo Step 3: Verifying archive...
set "VERIFY_OK=1"

tar -tf "%ARCHIVE_PATH%" | findstr /i /c:"frontend/src/components/layout/Sidebar.tsx" >nul
if errorlevel 1 (
  echo ERROR: Sidebar.tsx missing - save all files in your editor and re-run package. >&2
  set "VERIFY_OK=0"
)

tar -tf "%ARCHIVE_PATH%" | findstr /i /c:"deploy-production.sh" >nul
if errorlevel 1 (
  echo ERROR: deploy-production.sh missing from zip. >&2
  set "VERIFY_OK=0"
)

tar -tf "%ARCHIVE_PATH%" | findstr /i /c:"scripts/deploy-docker.sh" >nul
if errorlevel 1 (
  echo ERROR: scripts/deploy-docker.sh missing from zip. >&2
  set "VERIFY_OK=0"
)

powershell -NoProfile -Command ^
  "$e=0; tar -xOf '%ARCHIVE_PATH%' scripts/deploy-docker.sh 2>$null | ForEach-Object { if($_ -match \"`r\") { $e=1 } }; if($e){ exit 1 } else { exit 0 }"
if errorlevel 1 (
  echo ERROR: scripts/deploy-docker.sh still has Windows CRLF in zip. Re-run package-docker.bat >&2
  set "VERIFY_OK=0"
)

if "%VERIFY_OK%"=="0" exit /b 1

echo Verification: OK
echo.
type "%ROOT_DIR%\PACKAGE_BUILD.txt"
echo.
echo Created: %ARCHIVE_PATH%
echo.
echo Upload zip to server, then run:
echo   sudo bash deploy-production.sh ai-tools-token-tracker.zip
echo.
echo Do NOT use: sudo ./scripts/deploy-docker.sh  (causes bash\r on Windows-packaged zips)
exit /b 0
