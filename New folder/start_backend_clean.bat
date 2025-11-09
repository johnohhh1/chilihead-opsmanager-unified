@echo off
echo Starting backend with clean Ollama configuration...

cd server

REM Set the environment variable explicitly
set OLLAMA_HOST=http://localhost:11434

REM Start the backend
.venv\Scripts\python -m uvicorn app:app --reload --port 8002