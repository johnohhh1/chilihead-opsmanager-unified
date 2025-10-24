@echo off
echo ========================================
echo   ChiliHead - WORKING STARTUP SEQUENCE
echo ========================================
echo.

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

REM Step 1: Kill everything
echo [1/5] Stopping all services...
taskkill /F /IM ollama.exe 2>nul
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

REM Step 2: Start Ollama WITH CORRECT PATH
echo [2/5] Starting Ollama with correct models directory...
set OLLAMA_MODELS=C:\Users\John\.ollama
start "Ollama" /MIN cmd /c "set OLLAMA_MODELS=C:\Users\John\.ollama && ollama serve"
timeout /t 3 /nobreak >nul

REM Test Ollama
echo Testing Ollama...
curl -s http://localhost:11434/api/tags | findstr "models"
if errorlevel 1 (
    echo [WARNING] Ollama models not loading properly!
    echo Try running PERMANENT_OLLAMA_FIX.bat first
) else (
    echo [SUCCESS] Ollama models detected!
)

REM Step 3: Start Backend
echo.
echo [3/5] Starting Backend (Python/FastAPI)...
cd server
start "Backend" cmd /c "call .venv\Scripts\activate.bat && python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002"
cd ..
timeout /t 5 /nobreak >nul

REM Test Backend
echo Testing Backend...
curl -s http://localhost:8002/health
if errorlevel 1 (
    echo [ERROR] Backend failed to start!
) else (
    echo [SUCCESS] Backend is running!
)

REM Step 4: Start Frontend  
echo.
echo [4/5] Starting Frontend (Next.js)...
cd client
start "Frontend" cmd /c "npm run dev"
cd ..

echo.
echo [5/5] Starting Docker database...
docker-compose up -d 2>nul

echo.
echo ========================================
echo STARTUP COMPLETE!
echo ========================================
echo.
echo Services:
echo   Ollama:   http://localhost:11434
echo   Backend:  http://localhost:8002  
echo   Frontend: http://localhost:3001
echo   Database: localhost:5432
echo.
echo If Ollama models don't show:
echo   1. Run PERMANENT_OLLAMA_FIX.bat
echo   2. Then run this script again
echo.
echo ========================================
timeout /t 10
