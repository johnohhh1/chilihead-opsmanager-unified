"""
Enhanced AI-powered email summarization following the Ops Email Triage prompt
"""

import os
import httpx
from dotenv import load_dotenv
from .gmail import get_thread_messages
import json
from datetime import datetime, timedelta
import re

# Load environment variables
load_dotenv()

def get_openai_config():
    """Get OpenAI configuration"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o",  # UPGRADED to GPT-4 for better understanding
        "project_id": os.getenv("OPENAI_PROJECT_ID"),
        "org_id": os.getenv("OPENAI_ORG_ID")
    }

# The ACTUAL prompt from your instructions
OPS_TRIAGE_PROMPT = """
You are John's operations email triage assistant for Chili's Auburn Hills #605.

CRITICAL CONTEXT:
- Location: Orchard Lake, MI (America/Detroit timezone)
- Store: Chili's Auburn Hills #605
- Your role: Extract ONLY actionable items and produce detailed analysis

SCOPE & ANALYSIS WINDOWS:
1. HotSchedules/911 (last 12 hours): Coverage issues, call-offs, no-shows
2. Brinker/Leadership (last 24 hours): Deadlines, reports, schedule submissions
3. Vendors/Alerts (last 24 hours): Securitas, Cintas, Oracle, Fourth

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

For Action Items:
- SPECIFIC ACTION (not vague - what exactly must John do)
- CONTEXT (why this matters, impact if not done)
- DEPENDENCIES (what's needed before this can be done)
- PRIORITY RATIONALE (why urgent/high/normal)

OUTPUT FORMAT:

Provide a comprehensive analysis with:

1. EXECUTIVE SUMMARY (2-3 sentences max)
   - Most critical item requiring immediate attention
   - Total actionable items found

2. 🚨 911/EMERGENCY ITEMS
   - Detailed breakdown per incident
   - Specific coverage gaps
   - Recommended actions

3. 📅 DEADLINES & SUBMISSIONS
   - Table format with columns: Item | Due Date | Time Needed | Status
   - Calendar-ready entries with reminders

4. ✓ ACTION ITEMS
   - Prioritized list with time estimates
   - Clear next steps for each

5. 📊 OPERATIONAL INSIGHTS
   - Patterns detected (frequent call-offs, recurring issues)
   - Recommendations for prevention

6. 🔗 QUICK LINKS & REFERENCES
   - Important thread IDs
   - Key contacts mentioned

Remember: Be specific, actionable, and time-aware. Convert all relative dates to absolute dates in ET.
"""

def summarize_thread_advanced(thread_id: str) -> dict:
    """
    Advanced summarization using the full Ops Triage prompt
    Returns structured data for both display and todo list creation
    """
    
    # Get all messages in thread
    msgs = get_thread_messages(thread_id)
    
    if not msgs:
        return {
            "summary": "No messages found in thread",
            "structured_data": None
        }
    
    # Extract full email content
    email_content = []
    for msg in msgs:
        headers = msg.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}
        
        # Extract body
        body = extract_message_body(msg.get("payload", {}))
        
        email_content.append({
            "from": header_dict.get("from", ""),
            "to": header_dict.get("to", ""),
            "date": header_dict.get("date", ""),
            "subject": header_dict.get("subject", ""),
            "body": body
        })
    
    # Build context for AI
    thread_context = json.dumps(email_content, indent=2)
    
    # Add current time context
    current_time = datetime.now()
    time_context = f"""
Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S ET')}
Day of Week: {current_time.strftime('%A')}
    """
    
    # Build the full prompt
    full_prompt = f"""{OPS_TRIAGE_PROMPT}

{time_context}

THREAD TO ANALYZE:
{thread_context}

Provide both:
1. A detailed human-readable summary following the format above
2. A JSON structure with extracted tasks for the todo system
"""

    # Call OpenAI with the full prompt
    config = get_openai_config()
    
    if not config["api_key"]:
        return {
            "summary": "[No API Key] Would analyze: " + thread_context[:500],
            "structured_data": None
        }
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    
    if config["project_id"]:
        headers["OpenAI-Project"] = config["project_id"]
    
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are an expert operations manager assistant. Provide detailed, actionable analysis."
            },
            {
                "role": "user",
                "content": full_prompt
            }
        ],
        "temperature": 0.3,  # Lower temperature for more consistent extraction
        "max_tokens": 2000   # Increased for detailed summaries
    }
    
    try:
        with httpx.Client(base_url=config["base_url"], timeout=60) as client:
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
        
        return {
            "summary": content,
            "structured_data": structured_data
        }
        
    except httpx.HTTPStatusError as e:
        return {
            "summary": f"[API Error {e.response.status_code}]: {e.response.text}",
            "structured_data": None
        }
    except Exception as e:
        return {
            "summary": f"[Error]: {str(e)}",
            "structured_data": None
        }

def extract_message_body(payload: dict) -> str:
    """Extract the full body text from email payload"""
    body = ""
    
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    import base64
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif "parts" in part:
                body += extract_message_body(part)
    else:
        if payload.get("body", {}).get("data"):
            import base64
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode('utf-8', errors='ignore')
    
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
    
    for thread_id in thread_ids:
        result = summarize_thread_advanced(thread_id)
        all_summaries.append({
            "thread_id": thread_id,
            "summary": result["summary"]
        })
        
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
        "total_actionable": len(emergency_items) + len(deadlines) + len(all_tasks)
    }

# Keep the original simple function for backward compatibility
def summarize_thread(thread_id: str) -> str:
    """Simple summary for backward compatibility"""
    result = summarize_thread_advanced(thread_id)
    return result["summary"]
