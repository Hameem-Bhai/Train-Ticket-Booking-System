@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================================
echo   Bangladesh Railway V2 - Start Script
echo ================================================================

rem Detect if API already running on port 5001
set "APIPID="
for /f "tokens=5" %%p in ('netstat -ano ^| find ":5001" ^| find "LISTENING"') do (
  set "APIPID=%%p"
)

if defined APIPID (
  echo API V2 already running (PID !APIPID!)
) else (
  echo Starting API V2 server on http://127.0.0.1:5001 ...
  start "API V2 Server" cmd /c python api_server_v2.py

  echo Waiting for API to be ready...
  set COUNT=0
  :waitloop
  set /a COUNT+=1
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $resp=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5001/ -TimeoutSec 1; if ($resp.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
  if %ERRORLEVEL% neq 0 (
    if !COUNT! geq 15 (
      echo API did not start in time. Launching GUI anyway.
      goto launchgui
    )
    timeout /t 1 > nul
    goto waitloop
  )
  echo API is up.
)

:launchgui
echo Launching GUI...
python main_v2.py

endlocal
