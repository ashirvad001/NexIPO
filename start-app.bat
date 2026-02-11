@echo off
echo ========================================
echo NexIPO
echo Complete Application Startup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [Step 1] Starting Backend API...
echo.
start "IPO Backend API" cmd /k "cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

echo [Step 2] Starting Frontend...
echo.
start "IPO Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo ========================================
echo Application is starting...
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo API Docs:    http://localhost:8000/api/docs
echo Frontend:    http://localhost:3000
echo.
echo Two terminal windows will open:
echo 1. Backend API (Python/FastAPI)
echo 2. Frontend (Next.js)
echo.
echo Press Ctrl+C in each window to stop
echo ========================================
echo.
pause
