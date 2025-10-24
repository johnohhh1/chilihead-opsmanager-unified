@echo off
echo ========================================
echo   OLLAMA COMPLETE RESET AND FIX
echo ========================================
echo.

REM Kill Ollama
echo Stopping Ollama...
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

REM Clear bad environment variables
echo Clearing environment...
set OLLAMA_MODELS=

REM Start Ollama fresh (it will use default paths)
echo Starting Ollama with default configuration...
start "Ollama" ollama serve
timeout /t 3 /nobreak >nul

echo.
echo Testing Ollama...
ollama list

echo.
echo If no models show, try pulling one to reconnect:
echo   ollama pull llama3.2:3b
echo.
echo Your model files are intact in:
echo   C:\Users\John\.ollama\models\manifests\
echo.
pause
