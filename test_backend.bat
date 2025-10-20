@echo off
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Checking Python version...
python --version
echo.
echo Checking if FastAPI is installed...
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
echo.
echo Starting server...
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
pause
