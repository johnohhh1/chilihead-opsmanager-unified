@echo off
echo ========================================
echo  Testing Database Connection
echo ========================================
echo.

cd server
call .venv\Scripts\activate

python database.py

pause
