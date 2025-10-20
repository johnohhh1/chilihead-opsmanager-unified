@echo off
echo.
echo ========================================
echo   ChiliHead OpsManager - Quick Start
echo ========================================
echo.

REM Check if Docker Desktop is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop first, then run this script again.
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting PostgreSQL database...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start database!
    pause
    exit /b 1
)

echo [2/3] Waiting for database to be ready...
timeout /t 5 /nobreak >nul

echo [3/3] Starting backend and frontend...
echo.
echo ========================================
echo   Backend: http://localhost:8002
echo   Frontend: http://localhost:3001
echo ========================================
echo.
echo Press Ctrl+C in this window to stop everything
echo.

call scriptsstart_unified.bat
