@echo off
echo ========================================
echo   ChiliHead Backend Diagnostic
echo ========================================
echo.

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"

echo Checking Python installation...
python --version

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Checking dependencies...
pip list | findstr "fastapi uvicorn"

echo.
echo Testing backend startup...
echo Starting server on port 8002...
python -m uvicorn app:app --host 127.0.0.1 --port 8002

pause
