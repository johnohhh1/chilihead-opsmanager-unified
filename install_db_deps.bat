@echo off
echo ========================================
echo  Installing Database Dependencies
echo ========================================
echo.

cd server

echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Installing SQLAlchemy, psycopg2, and Alembic...
pip install sqlalchemy==2.0.23 psycopg2-binary==2.9.9 alembic==1.13.1

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Dependencies installed successfully!
echo ========================================
echo.
echo Next steps:
echo   1. Make sure Docker is running
echo   2. Run: start_database.bat
echo   3. Run: setup_alembic.bat
echo.
pause
