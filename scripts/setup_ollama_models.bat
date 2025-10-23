@echo off
echo ========================================
echo   Ollama Model Setup for ChiliHead
echo ========================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is not installed!
    echo Please install Ollama from: https://ollama.ai
    pause
    exit /b 1
)

echo Make sure Ollama is running first...
start "Ollama Server" /MIN cmd /c "ollama serve"
timeout /t 3 /nobreak >nul

echo.
echo Pulling recommended models for ChiliHead OpsManager...
echo This may take a few minutes depending on your internet speed.
echo.

echo [1/3] Pulling Llama 3.2 3B (fast, good for quick tasks)...
ollama pull llama3.2:3b
if errorlevel 1 (
    echo [WARNING] Failed to pull llama3.2:3b
) else (
    echo [SUCCESS] Llama 3.2 3B installed!
)

echo.
echo [2/3] Pulling Mistral 7B (balanced performance)...
ollama pull mistral:7b
if errorlevel 1 (
    echo [WARNING] Failed to pull mistral:7b
) else (
    echo [SUCCESS] Mistral 7B installed!
)

echo.
echo [3/3] Pulling Qwen 2.5 3B (good for structured outputs)...
ollama pull qwen2.5:3b
if errorlevel 1 (
    echo [WARNING] Failed to pull qwen2.5:3b
) else (
    echo [SUCCESS] Qwen 2.5 3B installed!
)

echo.
echo ========================================
echo Checking installed models...
echo ========================================
ollama list

echo.
echo ========================================
echo Setup complete! Models are ready to use.
echo ========================================
pause
