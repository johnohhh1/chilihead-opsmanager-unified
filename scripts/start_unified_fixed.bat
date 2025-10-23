@echo off
echo ========================================
echo Starting ChiliHead OpsManager Unified
echo ========================================
echo.

REM Change to the project directory
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

REM Check if Ollama is installed and try to start it
echo Checking Ollama...
where ollama >nul 2>&1
if errorlevel 1 (
    echo [SKIP] Ollama not found in PATH. Install from: https://ollama.ai
    echo OpenAI models will still work!
) else (
    echo [INFO] Starting Ollama serve in background...
    start "Ollama Server" /MIN cmd /c "ollama serve"
    echo Waiting 3 seconds for Ollama to initialize...
    timeout /t 3 /nobreak > nul
    echo [SUCCESS] Ollama started (or already running)
)

echo.
echo Starting Backend Server (FastAPI) on port 8002...
start "ChiliHead Backend" cmd /k "cd server && call .venv\Scripts\activate.bat && python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak > nul

echo.
echo Starting Frontend (Next.js)...
start "ChiliHead Frontend" cmd /k "cd client && npm run dev"

echo.
echo ========================================
echo ChiliHead OpsManager is starting!
echo ========================================
echo Ollama:   http://localhost:11434
echo Backend:  http://localhost:8002
echo Frontend: http://localhost:3001
echo.
echo Three command windows will open:
echo   1. Ollama Server (minimized)
echo   2. ChiliHead Backend (Python in venv)
echo   3. ChiliHead Frontend (Next.js)
echo.
echo Close this window or press any key to exit.
echo ========================================
pause
