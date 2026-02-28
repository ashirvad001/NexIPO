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

REM ── Check frontend node_modules ──
if not exist "%ROOT%frontend\node_modules" (
    echo  [INFO] Frontend dependencies not installed. Installing...
    start "Installing Frontend Deps" /wait cmd /c "cd /d "%ROOT%frontend" && npm install"
)
echo  [OK] Frontend dependencies ready
echo.

REM ── Step 1: Start Backend ──
echo  [STEP 1/2] Starting Backend API (FastAPI + Uvicorn)...
start "NexIPO Backend" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate.bat && python main.py"
echo           Waiting for backend to initialize...
timeout /t 6 /nobreak >nul
echo           Backend should be live at http://localhost:8000
echo.

REM ── Step 2: Start Frontend ──
echo  [STEP 2/2] Starting Frontend (Next.js)...
start "NexIPO Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"
echo           Waiting for frontend to compile...
timeout /t 5 /nobreak >nul
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
echo   Two terminal windows are open:
echo     1. "NexIPO Backend"  - Python/FastAPI server
echo     2. "NexIPO Frontend" - Next.js dev server
echo.
echo   To stop: press Ctrl+C in each terminal window.
echo  =============================================
echo.
pause
