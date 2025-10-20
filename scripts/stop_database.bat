@echo off
echo ========================================
echo  Stopping OpenInbox PostgreSQL Database
echo ========================================
echo.

docker-compose down

echo.
echo Database stopped.
echo.
echo To start again: double-click start_database.bat
echo To completely reset database: docker-compose down -v
echo.
pause
