@echo off
title NexIPO - Application Launcher
color 0B

echo.
echo  =============================================
echo       NexIPO - ML-Powered IPO Platform
echo       Complete Application Startup
echo  =============================================
echo.

REM ── Resolve project root (wherever this .bat lives) ──
set "ROOT=%~dp0"

REM ── Pre-flight checks ──
echo  [CHECK] Verifying prerequisites...
echo.

REM ── Check for processes on port 3000 and 8000 ──
echo  [INFO] Checking for existing processes on ports 3000 and 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo  [INFO] Killing process %%a on port 3000...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo  [INFO] Killing process %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo          Download from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python found

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js is not installed or not in PATH.
    echo          Download from https://nodejs.org/
    pause
    exit /b 1
)
echo  [OK] Node.js found

REM ── Check backend virtual environment ──
if not exist "%ROOT%backend\venv\Scripts\activate.bat" (
    echo  [ERROR] Backend virtual environment not found.
    echo          Run:  cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)
echo  [OK] Backend venv found

REM ── Check backend .env ──
if not exist "%ROOT%backend\.env" (
    echo  [ERROR] Backend .env file missing in %ROOT%backend
    echo          Please create one based on .env.example
    pause
    exit /b 1
)
echo  [OK] Backend .env found

REM ── Check frontend node_modules ──
if not exist "%ROOT%frontend\node_modules" (
    echo  [INFO] Frontend dependencies not installed. Installing...
    start "Installing Frontend Deps" /wait cmd /c "cd /d "%ROOT%frontend" && npm install"
)
echo  [OK] Frontend dependencies ready

REM ── Check Docker ──
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARNING] Docker is not installed or not in PATH. Database services will be skipped.
) else (
    echo  [OK] Docker found
)
echo.

REM ── Step 1: Initialize Database ──
echo  [STEP 1/3] Using local SQLite database (no Docker required)...
echo.

REM ── Step 2: Start Backend ──
echo  [STEP 2/3] Starting NexIPO Backend API...
start "NexIPO API Server" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate.bat && python main.py"
echo           Waiting for backend to initialize (approx 8s)...
timeout /t 8 /nobreak >nul
echo           Backend should be live at http://localhost:8000
echo.

REM ── Step 3: Start Frontend ──
echo  [STEP 3/3] Starting NexIPO Frontend UI...
start "NexIPO Web Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"
echo           Waiting for frontend to compile...
timeout /t 6 /nobreak >nul
echo           Frontend should be live at http://localhost:3000
echo.

REM ── Open browser ──
echo  [INFO] Opening application in your browser...
timeout /t 3 /nobreak >nul
start "" http://localhost:3000

echo.
echo  =============================================
echo       NexIPO is running!
echo  =============================================
echo.
echo   Frontend:    http://localhost:3000
echo   Backend:     http://localhost:8000
echo   API Docs:    http://localhost:8000/api/docs
echo.
echo   Active components:
echo     1. Databases       - Docker (PostgreSQL, Redis, MongoDB)
echo     2. "NexIPO Backend"  - Python/FastAPI server (Terminal)
echo     3. "NexIPO Frontend" - Next.js dev server (Terminal)
echo.
echo   To stop: press Ctrl+C in each terminal window.
echo  =============================================
echo.
exit /b 0
