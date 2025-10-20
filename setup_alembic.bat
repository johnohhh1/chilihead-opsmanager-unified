@echo off
echo ========================================
echo  Setting up Alembic for Database Migrations
echo ========================================
echo.

cd server
call .venv\Scripts\activate

echo [1/4] Installing dependencies...
pip install alembic sqlalchemy psycopg2-binary

echo.
echo [2/4] Initializing Alembic...
alembic init alembic

echo.
echo [3/4] Configuration complete!
echo.
echo Next: Run create_initial_migration.bat to create database schema
echo.
pause
