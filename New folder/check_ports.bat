@echo off
echo ========================================
echo   ChiliHead Port Status Check
echo ========================================
echo.

echo Checking all service ports...
echo.

echo [1] Database (PostgreSQL) - Port 5432:
netstat -an | findstr :5432 | findstr LISTENING
if errorlevel 1 (
    echo    [OFFLINE] Database not running - Start Docker Desktop!
) else (
    echo    [ONLINE] Database is listening
)

echo.
echo [2] Backend (FastAPI) - Port 8002:
netstat -an | findstr :8002 | findstr LISTENING
if errorlevel 1 (
    echo    [OFFLINE] Backend not running - This is your problem!
) else (
    echo    [ONLINE] Backend is listening
)

echo.
echo [3] Frontend (Next.js) - Port 3001:
netstat -an | findstr :3001 | findstr LISTENING
if errorlevel 1 (
    echo    [OFFLINE] Frontend not running
) else (
    echo    [ONLINE] Frontend is listening
)

echo.
echo [4] Ollama (Optional) - Port 11434:
netstat -an | findstr :11434 | findstr LISTENING
if errorlevel 1 (
    echo    [OFFLINE] Ollama not running (optional - OpenAI will still work)
) else (
    echo    [ONLINE] Ollama is listening
)

echo.
echo ========================================
echo Quick Fix Commands:
echo ========================================
echo.
echo If Database is OFFLINE:
echo   - Start Docker Desktop
echo   - Run: docker-compose up -d
echo.
echo If Backend is OFFLINE (most likely issue):
echo   cd server
echo   .venv\Scripts\activate
echo   python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002
echo.
echo If Frontend is OFFLINE:
echo   cd client
echo   npm run dev
echo.
pause
