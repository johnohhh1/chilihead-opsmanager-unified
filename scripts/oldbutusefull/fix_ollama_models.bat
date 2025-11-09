@echo off
echo ========================================
echo   Fixing Ollama Models Path Issue
echo ========================================
echo.

REM Kill any existing Ollama processes
echo Stopping any running Ollama instances...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

REM Set the correct models path
echo Setting correct models path...
set OLLAMA_MODELS=C:\Users\John\.ollama

REM Start Ollama with the correct path
echo Starting Ollama with correct configuration...
start "Ollama Server" cmd /k "set OLLAMA_MODELS=C:\Users\John\.ollama && ollama serve"

echo Waiting for Ollama to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Testing Ollama API...
curl -s http://localhost:11434/api/tags | findstr "models"

echo.
echo ========================================
echo If you see models above, the fix worked!
echo Now restart your ChiliHead OpsManager.
echo ========================================
pause
