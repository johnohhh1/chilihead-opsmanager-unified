@echo off
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Starting backend on port 8001...
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
pause
