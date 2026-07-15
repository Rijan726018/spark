@echo off
title NEXUS ALGO TERMINAL — Launcher
cd /d C:\Users\rijan\Claude

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          NEXUS ALGO TERMINAL v3.0                         ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  [1] Desktop App  (Electron — recommended)                ║
echo  ║  [2] Web Browser  (Dash — legacy, port 8050)              ║
echo  ║  [3] Dev Mode     (Vite HMR + Electron, port 3000/8000)   ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
set /p CHOICE= Enter choice [1/2/3]:

if "%CHOICE%"=="1" goto DESKTOP
if "%CHOICE%"=="2" goto BROWSER
if "%CHOICE%"=="3" goto DEVMODE

:: Default to desktop
:DESKTOP
echo.
echo  [*] Starting Desktop App...
call ktop.bat
goto END

:BROWSER
echo.
echo  [*] Starting Web Browser mode (Dash on port 8050)...
echo  [*] Browser will open automatically...

:: Kill old instances
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8050 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
start "" /b cmd /c "timeout /t 3 >nul && start http://localhost:8050"
.venv312\Scripts\python.exe dashboard.py
pause
goto END

:DEVMODE
echo.
echo  [*] Starting Dev Mode (Vite HMR + FastAPI + Electron)...
echo  [*] Vite dev server on http://localhost:3000
echo  [*] FastAPI backend on http://localhost:8000
echo.

:: Kill stale processes
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: Start Python backend in a new window
start "FastAPI Backend" .venv312\Scripts\python.exe server\main.py

:: Start Vite dev server + Electron concurrently
node_modules\.bin\concurrently ^
  --names "VITE,ELECTRON" ^
  --prefix-colors "cyan,green" ^
  "cd frontend && npm run dev" ^
  "node_modules\.bin\wait-on http://localhost:3000 && node_modules\.bin\electron . --dev"

pause
goto END

:END
