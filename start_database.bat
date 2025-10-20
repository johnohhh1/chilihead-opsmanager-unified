@echo off
echo ========================================
echo  Starting OpenInbox PostgreSQL Database
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking for existing database...
docker ps -a | findstr openinbox-postgres >nul
if errorlevel 1 (
    echo No existing database found. Creating new one...
) else (
    echo Found existing database.
)

echo.
echo [2/3] Starting PostgreSQL container...
docker-compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start database!
    pause
    exit /b 1
)

echo.
echo [3/3] Waiting for database to be ready...
timeout /t 3 /nobreak >nul

docker exec openinbox-postgres pg_isready -U openinbox >nul 2>&1
if errorlevel 1 (
    echo Database is starting up... (this may take 10-15 seconds)
    timeout /t 10 /nobreak >nul
)

echo.
echo ========================================
echo  PostgreSQL Database is READY!
echo ========================================
echo.
echo Connection Details:
echo   Host:     localhost
echo   Port:     5432
echo   Database: openinbox_dev
echo   User:     openinbox
echo   Password: devpass123
echo.
echo Connection String:
echo   postgresql://openinbox:devpass123@localhost:5432/openinbox_dev
echo.
echo ========================================
echo.
echo Useful Commands:
echo   - Stop database:    docker-compose down
echo   - View logs:        docker-compose logs -f
echo   - Restart fresh:    docker-compose down -v ^&^& docker-compose up -d
echo.
pause
