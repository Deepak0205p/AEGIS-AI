@echo off
setlocal enabledelayedexpansion
title REVEAL 2.0 - Sovereign AI Workbench Launcher

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

cls
echo ========================================================================
echo   REVEAL 2.0: MRPL Sovereign AI Workbench (SIH26117)
echo   MULTI-SERVICE SYSTEM LAUNCHER
echo ========================================================================
echo.

if exist "C:\Program Files\nodejs" set "PATH=C:\Program Files\nodejs;%PATH%"

where npm.cmd >nul 2>nul
if %errorlevel% neq 0 (
    set "NPM_CMD=npm"
) else (
    set "NPM_CMD=npm.cmd"
)

if exist "%REPO_ROOT%\.venv\Scripts\python.exe" (
    set "PY_CMD=%REPO_ROOT%\.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo Starting services in separate windows...
echo.

:: 1. User Backend Gateway (Port 8000)
echo [1/3] Starting Python Backend Gateway (Port 8000)...
start "REVEAL 2.0: Python Backend Gateway (:8000)" cmd /k ^
"title REVEAL Backend (:8000) && cd /d "%REPO_ROOT%" && set PYTHONPATH=%REPO_ROOT% && "%PY_CMD%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

:: 2. Chat Frontend (Port 3000)
echo [2/3] Starting Public Chat & Canvas UI (Port 3000)...
start "REVEAL 2.0: Chat UI (:3000)" cmd /k ^
"title REVEAL Chat UI (:3000) && cd /d "%REPO_ROOT%\apps\chat-frontend" && %NPM_CMD% run dev:http"

timeout /t 2 /nobreak >nul

:: 3. Admin Frontend (Port 3001)
echo [3/3] Starting Admin Observatory (Port 3001)...
start "REVEAL 2.0: Admin UI (:3001)" cmd /k ^
"title REVEAL Admin UI (:3001) && cd /d "%REPO_ROOT%\apps\admin-frontend" && %NPM_CMD% run dev"

echo.
echo ========================================================================
echo [OK] All services launched!
echo.
echo Access URLs:
echo   - Public Chat & Canvas : http://localhost:3000
echo   - Admin Observatory    : http://localhost:3001
echo   - Backend API Docs     : http://localhost:8000/api/docs
echo ========================================================================
echo.
pause
