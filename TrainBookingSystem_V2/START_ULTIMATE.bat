@echo off
setlocal enabledelayedexpansion
title Bangladesh Railway v2.5 - Ultimate Edition
color 0B

echo ================================================================
echo           BANGLADESH RAILWAY v2.5 - ULTIMATE EDITION
echo ================================================================
echo.
echo     Ultra-Modern GUI • Gmail Auth • 40+ Features • AI Powered
echo.
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking API Server...
echo.

rem Check if API already running on port 5001
set "APIPID="
for /f "tokens=5" %%p in ('netstat -ano ^| find ":5001" ^| find "LISTENING"') do (
  set "APIPID=%%p"
)

if defined APIPID (
  echo      ✓ API Server already running (PID !APIPID!)
  echo.
) else (
  echo      ○ Starting API Server on http://127.0.0.1:5001 ...
  start "Bangladesh Railway API v2.5" cmd /c "color 0A & title API Server v2.5 & python api_server_v2.py & pause"

  echo      ○ Waiting for API to initialize...
  set COUNT=0
  :waitloop
  set /a COUNT+=1
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $resp=Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5001/ -TimeoutSec 1; if ($resp.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" 2>nul
  if %ERRORLEVEL% neq 0 (
    if !COUNT! geq 15 (
      echo      ! API startup timeout - Continuing anyway...
      goto launchgui
    )
    timeout /t 1 /nobreak >nul
    goto waitloop
  )
  echo      ✓ API Server ready!
  echo.
)

:launchgui
echo [2/3] Launching Ultra-Modern GUI...
echo.
echo      ○ Initializing application...
echo      ○ Loading dark theme...
echo      ○ Preparing animations...
echo.

timeout /t 2 /nobreak >nul

python main_v2.py

if %ERRORLEVEL% neq 0 (
  echo.
  echo      ✗ Error launching GUI!
  echo      ✗ Error code: %ERRORLEVEL%
  echo.
  echo      Troubleshooting:
  echo      1. Check if Python is installed: python --version
  echo      2. Install dependencies: pip install -r requirements_v2.txt
  echo      3. Check for errors above
  echo.
  pause
  exit /b 1
)

echo.
echo [3/3] Application closed successfully!
echo.
echo ================================================================
echo     Thank you for using Bangladesh Railway v2.5!
echo     Have a great journey! 🚂✨
echo ================================================================
echo.

endlocal
pause

