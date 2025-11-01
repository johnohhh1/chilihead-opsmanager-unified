from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from routes.oauth import router as oauth_router
from routes.mail import router as mail_router
from routes.state import router as state_router
from routes.delegations import router as delegations_router
from routes.tasks import router as tasks_router  # NEW
from routes.email_state import router as email_state_router  # NEW
from routes.operations_chat import router as operations_chat_router  # NEW
from routes.calendar import router as calendar_router  # NEW: Google Calendar
from routes.models import router as models_router  # NEW: Models listing
from routes.sms import router as sms_router  # NEW: SMS messaging
from services.summarize import summarize_thread
from services.ai_triage import summarize_thread_advanced, batch_summarize_threads
from services.smart_assistant import smart_triage, daily_digest
from services.state_manager import state_manager
from services.model_provider import ModelProvider

load_dotenv()

app = FastAPI(title="OpenInbox OpsManager AI", version="2.0.0")

@app.get("/health")
async def health():
    return {"ok": True, "app": "OpenInbox OpsManager AI", "database": "connected"}

# Include routers
app.include_router(oauth_router, prefix="")
app.include_router(mail_router, prefix="")
app.include_router(state_router, prefix="/state")
app.include_router(delegations_router, prefix="")  # ChiliHead Delegations
app.include_router(tasks_router, prefix="")  # NEW: Tasks/Todo List
app.include_router(email_state_router, prefix="")  # NEW: Email State Tracking
app.include_router(operations_chat_router, prefix="")  # NEW: Operations Chat
app.include_router(calendar_router, prefix="")  # NEW: Google Calendar
app.include_router(models_router, prefix="")  # NEW: Models listing
app.include_router(sms_router, prefix="")  # NEW: SMS messaging

class SummarizeIn(BaseModel):
    thread_id: str
    model: str = "gpt-4o"  # Default AI model

@app.post("/summarize")
async def summarize(payload: SummarizeIn):
    try:
        summary = summarize_thread(payload.thread_id)
        return {"thread_id": payload.thread_id, "summary": summary}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/ai-triage")
async def ai_triage(payload: SummarizeIn):
    """Advanced AI triage with structured extraction"""
    try:
        result = summarize_thread_advanced(payload.thread_id)
        # Mark as analyzed
        state_manager.mark_analyzed(payload.thread_id)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

class BatchTriageIn(BaseModel):
    thread_ids: list[str]
    mode: str = "full"  # full, quick

@app.post("/ai-triage/batch")
async def batch_triage(payload: BatchTriageIn):
    """Batch process multiple threads"""
    try:
        result = batch_summarize_threads(payload.thread_ids)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/smart-triage")
async def smart_analysis(payload: SummarizeIn):
    """Smart context-aware analysis that actually understands emails"""
    try:
        result = smart_triage(payload.thread_id, model=payload.model)
        # Mark as analyzed
        state_manager.mark_analyzed(payload.thread_id)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/daily-digest")
async def get_daily_digest(model: str = "gpt-4o"):
    """Get daily operations brief"""
    try:
        result = daily_digest(model=model)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/deadline-scan")
async def deadline_scan(model: str = "gpt-4o"):
    """Run Brinker/Allen deadline scanner"""
    try:
        from services.deadline_scanner import scan_deadlines
        result = scan_deadlines(model=model)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

# Model provider endpoints
@app.get("/models/list")
async def list_models():
    """List all available AI models (OpenAI + Ollama)"""
    try:
        # Get Ollama models with connection status
        ollama_result = await ModelProvider.list_ollama_models()

        # Check if ollama_result is a dict with status (new format) or list (old format)
        if isinstance(ollama_result, dict):
            ollama_models = ollama_result.get("models", [])
            ollama_status = ollama_result.get("status", "unknown")
        else:
            ollama_models = ollama_result
            ollama_status = "connected" if ollama_models else "unavailable"

        # Add OpenAI models
        openai_models = [
            {"id": "gpt-4o", "name": "GPT-4o (OpenAI)", "provider": "openai", "default": True},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini (OpenAI)", "provider": "openai"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo (OpenAI)", "provider": "openai"},
        ]

        response = JSONResponse(
            content={
                "models": openai_models + ollama_models,
                "default": "gpt-4o",
                "ollama_status": ollama_status
            },
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        return response
    except Exception as e:
        raise HTTPException(500, str(e))

# Database health check
@app.get("/db/health")
async def database_health():
    """Check database connection"""
    try:
        from database import engine
        with engine.connect() as conn:
            return {"status": "connected", "database": "openinbox_dev"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
