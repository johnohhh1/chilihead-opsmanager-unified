@echo off
echo ========================================
echo  Running Database Migrations
echo ========================================
echo.

cd server
call .venv\Scripts\activate

echo Checking database connection...
python database.py

if errorlevel 1 (
    echo.
    echo [ERROR] Cannot connect to database!
    echo Make sure start_database.bat is running.
    echo.
    pause
    exit /b 1
)

echo.
echo Running migrations...
alembic upgrade head

if errorlevel 1 (
    echo.
    echo [ERROR] Migration failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Database schema created successfully!
echo ========================================
echo.
echo Tables created:
echo   - email_state
echo   - tasks
echo   - delegations
echo   - watch_config
echo   - ai_analysis_cache
echo.
echo Next: Update your API routes to use the database!
echo.
pause
