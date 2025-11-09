@echo off
echo ========================================
echo   ChiliHead OpsManager - COMPLETE FIX
echo ========================================
echo.

REM Kill any existing processes
echo [1/7] Cleaning up old processes...
taskkill /F /IM ollama.exe 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

REM Check Docker
echo [2/7] Checking Docker...
docker ps >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker Desktop is not running!
    echo Please start Docker Desktop for database support.
    echo Continuing without database...
    echo.
) else (
    echo Docker is running. Starting database...
    cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"
    docker-compose up -d
    timeout /t 3 /nobreak >nul
)

REM Start Ollama with correct path
echo [3/7] Starting Ollama with correct models path...
set OLLAMA_MODELS=C:\Users\John\.ollama
start "Ollama Server" /MIN cmd /c "ollama serve"
timeout /t 3 /nobreak >nul

REM Test Ollama
echo [4/7] Testing Ollama connection...
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not responding
) else (
    echo Ollama is running!
)

REM Start Backend with explicit venv activation
echo [5/7] Starting Backend Server...
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"
start "ChiliHead Backend" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002"
timeout /t 5 /nobreak >nul

REM Test Backend
echo [6/7] Testing Backend connection...
curl -s http://localhost:8002/health
if errorlevel 1 (
    echo.
    echo [ERROR] Backend not responding. Check the backend window for errors.
) else (
    echo.
    echo Backend is running!
)

REM Start Frontend
echo [7/7] Starting Frontend...
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\client"
start "ChiliHead Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo STARTUP COMPLETE! 
echo ========================================
echo.
echo Services should be available at:
echo   Ollama:   http://localhost:11434
echo   Backend:  http://localhost:8002
echo   Frontend: http://localhost:3001
echo.
echo Three command windows are open:
echo   1. Ollama Server
echo   2. Backend Server (Python/FastAPI)
echo   3. Frontend (Next.js)
echo.
echo If backend fails, check for missing dependencies:
echo   cd server
echo   .venv\Scripts\activate
echo   pip install -r requirements.txt
echo.
echo ========================================
pause
