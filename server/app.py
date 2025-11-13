from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, Response
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
from routes.inbox import router as inbox_router  # NEW: Inbox feature
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
app.include_router(inbox_router, prefix="")  # NEW: Inbox feature

@app.get("/api/attachments/{attachment_id}")
async def get_attachment(attachment_id: str, db: Session = Depends(get_db)):
    """
    Serve email attachment by ID
    Used for inline images (replacing cid: references) and regular attachments
    """
    from models import EmailAttachment
    import base64

    attachment = db.query(EmailAttachment).filter(
        EmailAttachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(404, "Attachment not found")

    # Update last accessed timestamp
    from datetime import datetime
    attachment.last_accessed_at = datetime.now()
    db.commit()

    # Decode base64 data
    try:
        # Gmail API returns base64url, convert to bytes
        data_bytes = base64.urlsafe_b64decode(
            attachment.data.replace('-', '+').replace('_', '/')
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to decode attachment: {str(e)}")

    return Response(
        content=data_bytes,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{attachment.filename}"'
        }
    )

@app.get("/api/attachments/by-cid/{thread_id}/{content_id}")
async def get_attachment_by_cid(
    thread_id: str,
    content_id: str,
    db: Session = Depends(get_db)
):
    """
    Serve attachment by Content-ID (for cid: references in HTML emails)
    """
    from models import EmailAttachment
    import base64

    attachment = db.query(EmailAttachment).filter(
        EmailAttachment.thread_id == thread_id,
        EmailAttachment.content_id == content_id
    ).first()

    if not attachment:
        raise HTTPException(404, f"Attachment with cid:{content_id} not found")

    # Update last accessed timestamp
    from datetime import datetime
    attachment.last_accessed_at = datetime.now()
    db.commit()

    # Decode base64 data
    try:
        data_bytes = base64.urlsafe_b64decode(
            attachment.data.replace('-', '+').replace('_', '/')
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to decode attachment: {str(e)}")

    return Response(
        content=data_bytes,
        media_type=attachment.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{attachment.filename}"'
        }
    )

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
        from models import ChatSession
        from datetime import datetime

        # Ensure clean database state
        db.rollback()

        # Generate the digest
        result = daily_digest(model=model, db=db)

        # Create a chat session for this digest
        session = ChatSession(
            context_snapshot={"daily_digest": result.get("digest", "")},
            title=f"Daily Brief - {datetime.now().strftime('%b %d, %Y')}"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Add session_id to result
        result["session_id"] = session.id

        return result
    except Exception as e:
        db.rollback()
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

@app.get("/api/parse-portal-email")
async def parse_portal_email(thread_id: str = None, db: Session = Depends(get_db)):
    """
    Manually trigger portal results parsing from BI email
    If thread_id not provided, searches for today's BI email
    """
    try:
        from services.gmail import get_thread_messages, get_user_threads
        from services.portal_parser import PortalResultsParser

        # If no thread_id, search for BI email from today
        if not thread_id:
            threads = get_user_threads(max_results=20, query=f"from:{PortalResultsParser.BI_EMAIL_SENDER} newer_than:1d")
            if not threads:
                return {"error": "No BI email found in last 24 hours", "searched_for": PortalResultsParser.BI_EMAIL_SENDER}

            # Use the first (most recent) BI email
            thread_id = threads[0].get("id")
            msgs = threads[0].get("messages", [])
        else:
            # Get specific thread
            msgs = get_thread_messages(thread_id)

        if not msgs:
            raise HTTPException(404, "Thread not found or has no messages")

        # Parse the email
        metrics = PortalResultsParser.process_bi_email(msgs, db)

        if not metrics:
            return {
                "success": False,
                "message": "Could not parse portal metrics. Check that Tesseract OCR is installed.",
                "thread_id": thread_id
            }

        return {
            "success": True,
            "thread_id": thread_id,
            "metrics": metrics,
            "message": "Portal metrics parsed and stored successfully!"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error parsing portal email: {str(e)}")

@app.get("/api/portal-dashboard")
async def get_portal_dashboard(db: Session = Depends(get_db)):
    """
    Extract metrics from RAP Mobile dashboard using vision AI
    Returns structured metric data for display in custom dashboard
    """
    try:
        from services.gmail import get_user_threads, get_service
        from services.ai_triage import extract_attachments_with_images
        from models import PortalMetrics
        import base64
        import httpx
        from datetime import datetime

        # Search for RAP Mobile email
        threads = get_user_threads(max_results=1, query='subject:"RAP Mobile"')

        if not threads:
            return {"success": False, "error": "No RAP Mobile email found"}

        msg = threads[0].get('messages', [{}])[0]
        msg_id = msg.get('id')
        thread_id = threads[0].get('id')
        headers = {h['name'].lower(): h['value']
                  for h in msg.get('payload', {}).get('headers', [])}

        # Get email date
        email_date = headers.get('date', 'Unknown date')

        # Extract images
        body, images = extract_attachments_with_images(msg.get('payload', {}))

        if not images:
            return {"success": False, "error": "No images found in RAP Mobile email"}

        # Find the RAP Mobile dashboard image
        dashboard_image = None
        for img in images:
            filename = img.get('filename', '').lower()
            if 'rap mobile' in filename or 'rap_mobile' in filename:
                dashboard_image = img
                break

        if not dashboard_image:
            dashboard_image = images[0]

        # Get image data
        image_data = dashboard_image.get('data')

        # If not inline, download attachment
        if not image_data and dashboard_image.get('attachment_id'):
            service = get_service()
            attachment = service.users().messages().attachments().get(
                userId='me',
                messageId=msg_id,
                id=dashboard_image.get('attachment_id')
            ).execute()
            image_data = attachment.get('data')

        if not image_data:
            return {"success": False, "error": "Could not retrieve dashboard image"}

        # Save image to temp file
        import base64
        import tempfile
        import json
        from pathlib import Path

        # Decode base64 (Gmail uses URL-safe base64)
        image_data_clean = image_data.replace('-', '+').replace('_', '/')
        missing_padding = len(image_data_clean) % 4
        if missing_padding:
            image_data_clean += '=' * (4 - missing_padding)

        image_bytes = base64.b64decode(image_data_clean)

        # Save to temp file
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        image_path = temp_dir / "rap_mobile_dashboard.png"
        image_path.write_bytes(image_bytes)

        # Use OpenAI Vision API with file upload
        openai_key = os.getenv("OPENAI_API_KEY")

        vision_prompt = """Extract ALL numeric metrics from this RAP Mobile restaurant dashboard.

Return ONLY a JSON object (no markdown):
{
  "comp_sales_day": -30.1,
  "comp_sales_ptd": -0.5,
  "comp_sales_vs_plan_ptd": -8.2,
  "dine_in_gwap_day": 0.0,
  "dine_in_gwap_ltd": 0.0,
  "dine_in_gwap_r4w": 0.0,
  "to_go_gwap_day": 0.0,
  "to_go_gwap_ltd": 0.0,
  "to_go_gwap_r4w": 0.0,
  "labor_percent": 25.5,
  "guest_satisfaction": 85.0,
  "food_cost": 28.5,
  "speed_of_service": 12.5
}

Use null if metric not visible. Extract percentages as decimals (e.g., -30.1% becomes -30.1)."""

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Read image file
            with open(image_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')

            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
            )

            if response.status_code != 200:
                error_detail = response.text
                print(f"OpenAI Error: {error_detail}")
                raise HTTPException(500, f"OpenAI API error: {error_detail[:200]}")

            result = response.json()

        extracted_text = result['choices'][0]['message']['content'].strip()

        # Parse JSON
        if extracted_text.startswith("```"):
            extracted_text = extracted_text.split("```")[1]
            if extracted_text.startswith("json"):
                extracted_text = extracted_text[4:]

        metrics_data = json.loads(extracted_text.strip())

        # Store in database
        portal_metric = PortalMetrics(
            email_thread_id=thread_id,
            email_date=email_date,
            comp_sales_day=metrics_data.get('comp_sales_day'),
            comp_sales_ptd=metrics_data.get('comp_sales_ptd'),
            comp_sales_vs_plan_ptd=metrics_data.get('comp_sales_vs_plan_ptd'),
            dine_in_gwap_day=metrics_data.get('dine_in_gwap_day'),
            dine_in_gwap_ltd=metrics_data.get('dine_in_gwap_ltd'),
            dine_in_gwap_r4w=metrics_data.get('dine_in_gwap_r4w'),
            to_go_gwap_day=metrics_data.get('to_go_gwap_day'),
            to_go_gwap_ltd=metrics_data.get('to_go_gwap_ltd'),
            to_go_gwap_r4w=metrics_data.get('to_go_gwap_r4w'),
            labor_percent=metrics_data.get('labor_percent'),
            guest_satisfaction=metrics_data.get('guest_satisfaction'),
            food_cost=metrics_data.get('food_cost'),
            speed_of_service=metrics_data.get('speed_of_service'),
            raw_image_data=None  # Don't store large binary data
        )

        db.add(portal_metric)
        db.commit()
        db.refresh(portal_metric)

        return {
            "success": True,
            "email_date": email_date,
            "extracted_at": datetime.now().isoformat(),
            "metrics": metrics_data
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error extracting metrics: {str(e)}")

# Dismiss digest items
class DismissItemRequest(BaseModel):
    item_type: str  # 'email', 'urgent_item', 'deadline', 'pattern'
    identifier: str  # Email thread_id or description hash
    dismiss_reason: str  # 'resolved', 'not_relevant', 'already_handled'
    original_text: str = None
    email_thread_id: str = None
    email_subject: str = None
    notes: str = None
    is_permanent: bool = False
    days_to_hide: int = None  # Optional: auto-expire after N days

@app.post("/dismiss-item")
async def dismiss_item(payload: DismissItemRequest, db: Session = Depends(get_db)):
    """Dismiss an item from daily digest to prevent re-flagging"""
    try:
        from models import DismissedItem
        from datetime import datetime, timedelta

        # Calculate expiry if temporary
        expires_at = None
        if not payload.is_permanent and payload.days_to_hide:
            expires_at = datetime.now() + timedelta(days=payload.days_to_hide)

        dismissed = DismissedItem(
            item_type=payload.item_type,
            identifier=payload.identifier,
            original_text=payload.original_text,
            email_thread_id=payload.email_thread_id,
            email_subject=payload.email_subject,
            dismiss_reason=payload.dismiss_reason,
            notes=payload.notes,
            is_permanent=payload.is_permanent,
            expires_at=expires_at
        )

        db.add(dismissed)
        db.commit()
        db.refresh(dismissed)

        return {
            "success": True,
            "dismissed_id": dismissed.id,
            "message": f"Item dismissed successfully ({payload.dismiss_reason})"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@app.get("/dismissed-items")
async def get_dismissed_items(db: Session = Depends(get_db)):
    """Get all active dismissed items"""
    try:
        from models import DismissedItem
        from datetime import datetime

        # Get non-expired dismissed items
        dismissed = db.query(DismissedItem).filter(
            (DismissedItem.is_permanent == True) |
            (DismissedItem.expires_at > datetime.now()) |
            (DismissedItem.expires_at == None)
        ).order_by(DismissedItem.dismissed_at.desc()).all()

        return {
            "dismissed_items": [
                {
                    "id": d.id,
                    "item_type": d.item_type,
                    "identifier": d.identifier,
                    "original_text": d.original_text,
                    "email_subject": d.email_subject,
                    "dismiss_reason": d.dismiss_reason,
                    "dismissed_at": d.dismissed_at.isoformat(),
                    "is_permanent": d.is_permanent,
                    "expires_at": d.expires_at.isoformat() if d.expires_at else None
                }
                for d in dismissed
            ]
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.delete("/dismissed-item/{item_id}")
async def undismiss_item(item_id: str, db: Session = Depends(get_db)):
    """Remove a dismissed item (un-dismiss it)"""
    try:
        from models import DismissedItem

        dismissed = db.query(DismissedItem).filter(DismissedItem.id == item_id).first()
        if not dismissed:
            raise HTTPException(404, "Dismissed item not found")

        db.delete(dismissed)
        db.commit()

        return {"success": True, "message": "Item restored - will appear in future digests"}
    except Exception as e:
        db.rollback()
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
