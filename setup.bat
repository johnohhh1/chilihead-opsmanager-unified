@echo off
echo ========================================
echo ChiliHead OpsManager Unified Setup
echo ========================================
echo.

REM Step 1: Copy all server files from openinbox-opsmanager
echo [1/5] Copying server files...
xcopy "C:\Users\John\Desktop\openinbox-opsmanager\server\*" "C:\Users\John\Desktop\chilihead-opsmanager-unified\server\" /E /I /H /Y /EXCLUDE:exclude.txt

REM Step 2: Copy all client files from openinbox-opsmanager  
echo [2/5] Copying client files...
xcopy "C:\Users\John\Desktop\openinbox-opsmanager\client\*" "C:\Users\John\Desktop\chilihead-opsmanager-unified\client\" /E /I /H /Y

REM Step 3: Setup Python virtual environment
echo [3/5] Setting up Python virtual environment...
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"
python -m venv .venv

REM Step 4: Install Python dependencies
echo [4/5] Installing Python dependencies...
call .venv\Scripts\activate
pip install -r requirements.txt

REM Step 5: Install Node dependencies
echo [5/5] Installing Node dependencies...
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\client"
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Copy your .env file to the server folder
echo 2. Run git init and connect to your repo
echo 3. Use start_unified.bat to launch the app
echo.
pause
