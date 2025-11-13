"""
Enhanced AI-powered email summarization with image analysis support
Includes Aubs (Auburn Hills Assistant) persona
Now records to centralized agent memory for coordination
"""

import os
import httpx
from dotenv import load_dotenv
from .gmail import get_thread_messages
import json
from datetime import datetime, timedelta
import re
import base64
from sqlalchemy.orm import Session
from typing import Optional

# Load environment variables
load_dotenv()

def get_openai_config():
    """Get OpenAI configuration"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o",  # GPT-4o supports vision
        "project_id": os.getenv("OPENAI_PROJECT_ID"),
        "org_id": os.getenv("OPENAI_ORG_ID")
    }

# The AUBS PERSONA - Auburn Hills Assistant
AUBS_PERSONA = """
You are AUBS (Auburn Hills Assistant) - John's operations AI for Chili's #605.

PERSONALITY:
- Supportive partner focused on making John's job easier
- Clear and direct without being preachy or condescending
- Helpful problem-solver, not a lecturer
- Respects that John knows his team and business
- Focuses on facts and solutions, not explanations of why things matter

COMMUNICATION STYLE:
- State the facts clearly
- Provide specific details (who, what, when, where)
- Suggest solutions when helpful
- Skip the lectures about why something is important
- Trust John to prioritize and make decisions

EXAMPLES:
✓ "Hannah's pay card failed - she hasn't been paid in 48 hours. Payroll: 555-0123"
✗ "Real talk, John. This is about recordkeeping and could lead to bigger headaches..."

✓ "Blake called off for tonight 5-10pm. Sarah and Mike are available."
✗ "Here's the deal, you're in the weeds on coverage..."

✓ "P5 schedule due Friday 5pm. Takes about 30 minutes."
✗ "Let's knock this out before it becomes a problem..."

PRIORITIES:
1. Guest safety & experience (health dept, quality issues)
2. Team member wellbeing (payroll, scheduling, harassment)
3. Business continuity (coverage, equipment, supplies)
4. Corporate compliance (reports, deadlines, audits)
5. Everything else
"""

# The ACTUAL prompt from your instructions with AUBS persona
OPS_TRIAGE_PROMPT = f"""
{AUBS_PERSONA}

CRITICAL CONTEXT:
- Location: Orchard Lake, MI (America/Detroit timezone)
- Store: Chili's Auburn Hills #605
- Your role: Extract ONLY actionable items and produce detailed analysis

SCOPE & ANALYSIS WINDOWS:
1. HotSchedules/911 (last 12 hours): Coverage issues, call-offs, no-shows
2. Brinker/Leadership (last 24 hours): Deadlines, reports, schedule submissions
3. Vendors/Alerts (last 24 hours): Securitas, Cintas, Oracle, Fourth
4. RAP Mobile/Tableau Reports: Analyze dashboard images for KPI trends, issues, and opportunities

**IMPORTANT: If you see images (especially from RAP Mobile/Tableau):**
- Analyze charts, tables, and KPIs carefully
- Call out concerning trends (sales drops, labor spikes, waste increases)
- Identify opportunities (high performers, efficiency gains)
- Convert visual data into actionable insights

EXTRACTION REQUIREMENTS:

For 911/Emergency Items:
- WHO called off/didn't show (full name + role)
- WHEN exactly (shift date/time in ET)
- COVERAGE STATUS (who's covering, gaps remaining)
- ACTION REQUIRED (specific steps John needs to take)

For Deadlines/Deliverables:
- WHAT exactly is due (be specific - "P5 Manager Schedule" not just "schedule")
- WHEN due (convert "by Friday" → actual date like "Fri Oct 18, 2024")
- WHO requested it (name + email)
- SUBMISSION METHOD (where/how to submit)
- TIME ESTIMATE (how long this will take)

For Dashboard/Report Analysis (RAP Mobile, Tableau, etc.):
- KEY METRICS: What numbers stand out (good or bad)
- TRENDS: Week-over-week, day-over-day changes
- RED FLAGS: Problem areas needing immediate attention
- OPPORTUNITIES: Areas performing well or opportunities to improve
- CONTEXT: Compare to goals, benchmarks, or historical performance

For Action Items:
- SPECIFIC ACTION (not vague - what exactly must John do)
- CONTEXT (why this matters, impact if not done)
- DEPENDENCIES (what's needed before this can be done)
- PRIORITY RATIONALE (why urgent/high/normal)

OUTPUT FORMAT:

Provide a comprehensive analysis with:

1. EXECUTIVE SUMMARY (2-3 sentences max, in AUBS voice)
   - Most critical item requiring immediate attention
   - Total actionable items found

2. 🚨 911/EMERGENCY ITEMS
   - Detailed breakdown per incident
   - Specific coverage gaps
   - Recommended actions (AUBS style)

3. 📊 DASHBOARD INSIGHTS (if images present)
   - Key metrics and trends from visual data
   - Performance against targets
   - Red flags and opportunities
   - Specific recommendations based on numbers

4. 📅 DEADLINES & SUBMISSIONS
   - Table format with columns: Item | Due Date | Time Needed | Status
   - Calendar-ready entries with reminders

5. ✓ ACTION ITEMS (prioritized, AUBS voice)
   - Prioritized list with time estimates
   - Clear next steps for each
   - "Real talk" on consequences if ignored

6. 📊 OPERATIONAL INSIGHTS
   - Patterns detected (frequent call-offs, recurring issues)
   - Recommendations for prevention
   - AUBS-style reality check

7. 🔗 QUICK LINKS & REFERENCES
   - Important thread IDs
   - Key contacts mentioned
   - Dashboard/report links

Remember: Channel AUBS - be specific, actionable, time-aware, and real. Convert all relative dates to absolute dates in ET.
"""

def extract_attachments_with_images(payload: dict) -> tuple:
    """
    Extract both text body AND images from email payload
    Returns: (body_text, image_data_list)
    """
    body = ""
    images = []
    
    def process_part(part):
        nonlocal body, images
        
        mime_type = part.get("mimeType", "")
        
        # Handle text
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        # Handle images (JPEG, PNG, GIF, WebP)
        elif mime_type.startswith("image/"):
            attachment_id = part.get("body", {}).get("attachmentId")
            data = part.get("body", {}).get("data")
            
            if data:  # Inline image
                images.append({
                    "mime_type": mime_type,
                    "data": data,  # Already base64
                    "filename": part.get("filename", "image"),
                    "size": part.get("body", {}).get("size", 0)
                })
            elif attachment_id:  # Attached image (would need separate API call)
                images.append({
                    "mime_type": mime_type,
                    "attachment_id": attachment_id,
                    "filename": part.get("filename", "image"),
                    "size": part.get("body", {}).get("size", 0)
                })
        
        # Recursive for multipart
        if "parts" in part:
            for subpart in part["parts"]:
                process_part(subpart)
    
    if "parts" in payload:
        for part in payload["parts"]:
            process_part(part)
    else:
        # Single part message
        if payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode('utf-8', errors='ignore')
    
    return body, images

def summarize_thread_advanced(thread_id: str, use_vision: bool = True, db: Optional[Session] = None) -> dict:
    """
    Advanced summarization using AUBS persona and vision analysis
    Returns structured data for both display and todo list creation
    Now records to centralized agent memory!

    Args:
        thread_id: Gmail thread ID
        use_vision: Whether to analyze images (default True for RAP Mobile emails)
        db: Database session for recording to agent memory (optional)
    """

    # Get all messages in thread
    msgs = get_thread_messages(thread_id)

    if not msgs:
        return {
            "summary": "No messages found in thread",
            "structured_data": None,
            "has_images": False
        }

    # Extract full email content WITH images
    email_content = []
    all_images = []

    for msg in msgs:
        headers = msg.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        # Extract body and inline images from payload
        body, inline_images = extract_attachments_with_images(msg.get("payload", {}))

        email_content.append({
            "from": header_dict.get("from", ""),
            "to": header_dict.get("to", ""),
            "date": header_dict.get("date", ""),
            "subject": header_dict.get("subject", ""),
            "body": body,
            "image_count": len(inline_images)
        })

        all_images.extend(inline_images)

    # Fetch stored attachments from database if available
    if db:
        from models import EmailAttachment
        stored_attachments = db.query(EmailAttachment).filter(
            EmailAttachment.thread_id == thread_id,
            EmailAttachment.mime_type.like('image/%')
        ).all()

        # Add stored attachments that aren't already in all_images
        for att in stored_attachments:
            # Check if already included (by checking if data matches)
            if not any(img.get('data') == att.data for img in all_images):
                all_images.append({
                    'mime_type': att.mime_type,
                    'data': att.data,
                    'filename': att.filename,
                    'size': att.size_bytes,
                    'from_db': True
                })
    
    # Check if this is a RAP Mobile or dashboard email
    is_dashboard_email = any(
        "rap mobile" in email.get("subject", "").lower() or
        "tableau" in email.get("subject", "").lower() or
        "dashboard" in email.get("subject", "").lower()
        for email in email_content
    )
    
    # Build context for AI
    thread_context = json.dumps(email_content, indent=2)
    
    # Add current time context
    current_time = datetime.now()
    time_context = f"""
Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S ET')}
Day of Week: {current_time.strftime('%A')}
"""
    
    # Build messages for GPT-4o Vision
    messages = [
        {
            "role": "system",
            "content": "You are AUBS - Auburn Hills Assistant. Direct, helpful, restaurant-savvy. Analyze text AND images."
        }
    ]
    
    # Build user message with text and images
    user_content = [
        {
            "type": "text",
            "text": f"""{OPS_TRIAGE_PROMPT}

{time_context}

THREAD TO ANALYZE:
{thread_context}

{"📊 IMAGES ATTACHED: Analyze the dashboard/report images carefully for KPIs, trends, and actionable insights." if all_images else ""}

Provide both:
1. A detailed human-readable summary following the format above (use AUBS voice)
2. A JSON structure with extracted tasks for the todo system
"""
        }
    ]
    
    # Add images if present and vision is enabled
    if use_vision and all_images:
        for img in all_images[:5]:  # Limit to 5 images to stay within token limits
            if img.get("data"):  # Only inline images (no attachment_id fetching yet)
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['data']}"
                    }
                })
    
    messages.append({
        "role": "user",
        "content": user_content
    })
    
    # Call OpenAI with vision support
    config = get_openai_config()
    
    if not config["api_key"]:
        return {
            "summary": "[No API Key] Would analyze: " + thread_context[:500],
            "structured_data": None,
            "has_images": len(all_images) > 0
        }
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    
    if config["project_id"]:
        headers["OpenAI-Project"] = config["project_id"]
    
    payload = {
        "model": "gpt-4o",  # GPT-4o supports vision
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 3000  # Increased for image analysis
    }
    
    try:
        with httpx.Client(base_url=config["base_url"], timeout=120) as client:
            response = client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
        content = data["choices"][0]["message"]["content"].strip()

        # Try to extract JSON if present
        structured_data = None
        if "```json" in content:
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                try:
                    structured_data = json.loads(json_match.group(1))
                    # Remove JSON from summary
                    content = content.replace(json_match.group(0), "").strip()
                except:
                    pass

        # Record to agent memory if database session provided
        if db:
            try:
                from services.agent_memory import AgentMemoryService

                # Extract key findings from structured data
                key_findings = {}
                if structured_data:
                    if 'urgent_items' in structured_data:
                        key_findings['urgent_items'] = structured_data['urgent_items']
                    if 'deadlines' in structured_data:
                        key_findings['deadlines'] = structured_data['deadlines']

                # Get subject from email content
                subject = email_content[0].get('subject', 'Unknown') if email_content else 'Unknown'

                # Extract key entities/names from the analysis for better searchability
                import re
                entities = []
                # Look for proper names (capitalized words) in the AI's analysis
                names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', content)
                # Common names to include
                common_names = {'Pedro', 'Hannah', 'Blake', 'Sarah', 'Mike', 'Zimmerman'}
                entities = [n for n in names if n in common_names][:3]  # Top 3

                # Build searchable summary
                entity_str = f" (re: {', '.join(entities)})" if entities else ""
                priority_str = ""
                if structured_data and structured_data.get('priority') == 'urgent':
                    priority_str = "[URGENT] "

                # Record the analysis
                AgentMemoryService.record_event(
                    db=db,
                    agent_type='triage',
                    event_type='email_analyzed',
                    summary=f"{priority_str}{subject[:60]}{entity_str}",
                    context_data={
                        'email_subject': subject,
                        'sender': email_content[0].get('from', '') if email_content else '',
                        'has_images': len(all_images) > 0,
                        'analysis_summary': content[:500]
                    },
                    key_findings=key_findings,
                    related_entities={
                        'emails': [thread_id]
                    },
                    email_id=thread_id,
                    model_used=config["model"],
                    confidence_score=85 if structured_data else 70
                )
            except Exception as mem_error:
                # Don't fail email analysis if memory recording fails
                print(f"Warning: Failed to record to agent memory: {mem_error}")

        return {
            "summary": content,
            "structured_data": structured_data,
            "has_images": len(all_images) > 0,
            "images_analyzed": len(all_images) if use_vision else 0
        }
        
    except httpx.HTTPStatusError as e:
        return {
            "summary": f"[API Error {e.response.status_code}]: {e.response.text}",
            "structured_data": None,
            "has_images": len(all_images) > 0
        }
    except Exception as e:
        return {
            "summary": f"[Error]: {str(e)}",
            "structured_data": None,
            "has_images": len(all_images) > 0
        }

def extract_message_body(payload: dict) -> str:
    """Extract the full body text from email payload (legacy function)"""
    body, _ = extract_attachments_with_images(payload)
    return body

def batch_summarize_threads(thread_ids: list) -> dict:
    """
    Batch summarize multiple threads and extract all tasks
    Perfect for the daily triage view
    """
    all_summaries = []
    all_tasks = []
    emergency_items = []
    deadlines = []
    total_images = 0
    
    for thread_id in thread_ids:
        result = summarize_thread_advanced(thread_id)
        all_summaries.append({
            "thread_id": thread_id,
            "summary": result["summary"],
            "has_images": result.get("has_images", False)
        })
        
        if result.get("has_images"):
            total_images += result.get("images_analyzed", 0)
        
        if result.get("structured_data"):
            data = result["structured_data"]
            if data.get("emergency_items"):
                emergency_items.extend(data["emergency_items"])
            if data.get("deadlines"):
                deadlines.extend(data["deadlines"])
            if data.get("tasks"):
                all_tasks.extend(data["tasks"])
    
    return {
        "summaries": all_summaries,
        "emergency_items": emergency_items,
        "deadlines": deadlines,
        "tasks": all_tasks,
        "total_actionable": len(emergency_items) + len(deadlines) + len(all_tasks),
        "images_analyzed": total_images
    }

# Keep the original simple function for backward compatibility
def summarize_thread(thread_id: str) -> str:
    """Simple summary for backward compatibility"""
    result = summarize_thread_advanced(thread_id)
    return result["summary"]
