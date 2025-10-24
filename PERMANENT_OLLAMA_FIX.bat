@echo off
echo ========================================
echo   PERMANENT Ollama Fix
echo ========================================
echo.

REM Kill Ollama
taskkill /F /IM ollama.exe 2>nul
timeout /t 2 /nobreak >nul

echo Setting OLLAMA_MODELS environment variable permanently...
setx OLLAMA_MODELS "C:\Users\John\.ollama"

echo.
echo Starting Ollama with correct path...
set OLLAMA_MODELS=C:\Users\John\.ollama
start "Ollama" ollama serve

timeout /t 3 /nobreak >nul

echo.
echo Testing Ollama models...
curl http://localhost:11434/api/tags

echo.
echo ========================================
echo If models show above, the fix worked!
echo.
echo IMPORTANT: The environment variable is now set permanently.
echo Future Ollama starts will use the correct path.
echo ========================================
pause
