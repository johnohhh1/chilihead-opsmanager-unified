from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session

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
from database import get_db

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
async def ai_triage(payload: SummarizeIn, db: Session = Depends(get_db)):
    """Advanced AI triage with structured extraction - now records to agent memory!"""
    try:
        result = summarize_thread_advanced(payload.thread_id, db=db)
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
async def smart_analysis(
    payload: SummarizeIn,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Smart context-aware analysis with caching
    - Checks cache first (unless force_refresh=True)
    - Uses user-selected model from dropdown
    - Stores analysis for future use
    """
    try:
        from services.email_sync import EmailSyncService

        # Check cache unless user wants fresh analysis
        if not force_refresh:
            cached = EmailSyncService.get_cached_analysis(db, payload.thread_id)
            if cached:
                print(f"[Cache Hit] Returning cached analysis for {payload.thread_id} (model: {cached.model_used})")
                return {
                    **cached.analysis_json,
                    "cached": True,
                    "analyzed_at": cached.analyzed_at.isoformat(),
                    "model_used": cached.model_used,
                    "trust_score": cached.trust_score,
                    "model_tier": cached.model_tier
                }

        # No cache or forced refresh - run fresh analysis
        print(f"[Cache Miss] Running fresh analysis with {payload.model}")
        result = smart_triage(payload.thread_id, model=payload.model, db=db)

        # Cache the result (smart_triage should handle this internally)
        # Mark as analyzed
        state_manager.mark_analyzed(payload.thread_id)

        return {**result, "cached": False}

    except Exception as e:
        raise HTTPException(500, str(e))

class ReanalysisIn(BaseModel):
    thread_id: str
    model: str
    reason: str = "user_requested"

@app.post("/reanalyze-email")
async def reanalyze_email(payload: ReanalysisIn, db: Session = Depends(get_db)):
    """Force re-analysis of an email with a different/better model"""
    try:
        from services.email_sync import EmailSyncService

        # Flag for reanalysis
        EmailSyncService.flag_for_reanalysis(db, payload.thread_id, payload.reason)

        # Run fresh analysis with chosen model
        result = smart_triage(payload.thread_id, model=payload.model, db=db)

        return {
            **result,
            "reanalyzed": True,
            "previous_model": None  # Could fetch from previous_analysis if needed
        }
    except Exception as e:
        raise HTTPException(500, str(e))

class FeedbackIn(BaseModel):
    thread_id: str
    feedback: str  # 'accurate', 'missed_details', 'hallucinated', 'wrong_priority'

@app.post("/analysis-feedback")
async def submit_analysis_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    """Submit feedback on analysis quality (updates trust scores)"""
    try:
        from services.email_sync import EmailSyncService

        result = EmailSyncService.submit_feedback(db, payload.thread_id, payload.feedback)

        return {
            "thread_id": payload.thread_id,
            "feedback_recorded": True,
            "new_trust_score": result.trust_score if result else None,
            "needs_reanalysis": result.needs_reanalysis if result else False
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/cache-stats")
async def get_cache_stats(db: Session = Depends(get_db)):
    """Get email cache statistics"""
    try:
        from services.email_sync import EmailSyncService
        return EmailSyncService.get_cache_stats(db)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/daily-digest")
async def get_daily_digest(model: str = "gpt-4o", db: Session = Depends(get_db)):
    """Get daily operations brief - now with agent memory context!"""
    try:
        result = daily_digest(model=model, db=db)
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

# Model provider endpoints are handled by the models router

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
