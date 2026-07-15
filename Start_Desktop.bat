@echo off
title NEXUS ALGO TERMINAL v3.0 — Desktop
cd /d C:\Users\rijan\Claude

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║    NEXUS ALGO TERMINAL v3.0  [DESKTOP MODE]               ║
echo  ║    Electron + FastAPI + NinjaTrader Bridge                ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Kill any stale backend processes ──────────────────────────────────────────
echo  [*] Clearing stale processes on ports 8000 / 9090...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":9090 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: ── Verify node_modules ───────────────────────────────────────────────────────
if not exist "node_modules\electron" (
    echo  [!] Electron not found. Installing npm dependencies...
    npm install
    if errorlevel 1 (
        echo  [ERROR] npm install failed. Ensure Node.js is installed.
        pause
        exit /b 1
    )
)

:: ── Launch Electron (it spawns Python internally) ─────────────────────────────
echo  [*] Launching Nexus Algo Terminal desktop app...
echo.
node_modules\.bin\electron .

:: If Electron exits abnormally, pause so the user can see the error
if errorlevel 1 (
    echo.
    echo  [ERROR] Electron exited with error code %errorlevel%
    pause
)
