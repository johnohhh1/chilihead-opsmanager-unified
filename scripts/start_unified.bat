@echo off
echo ========================================
echo Starting ChiliHead OpsManager Unified
echo ========================================
echo.

REM Change to the project directory
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

echo Starting Backend Server (FastAPI) on port 8002...
start "ChiliHead Backend" cmd /k "cd server && .venv\Scripts\activate && python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend (Next.js)...
start "ChiliHead Frontend" cmd /k "cd client && npm run dev"

echo.
echo ========================================
echo ChiliHead OpsManager is starting!
echo ========================================
echo Backend:  http://localhost:8002
echo Frontend: http://localhost:3001
echo.
echo Two command windows will open.
echo Close this window or press any key to exit.
echo ========================================
pause
