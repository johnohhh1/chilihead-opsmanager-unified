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

**CRITICAL: RAP Mobile Dashboard Image Analysis**
When you see dashboard images (RAP Mobile, Tableau), you MUST:
1. **READ ALL VISIBLE METRICS** - Extract exact numbers, percentages, dollar amounts
2. **COMPARE TO TARGETS** - Green vs Red indicators, variance percentages
3. **IDENTIFY TRENDS** - Week-over-week, day-over-day, period comparisons
4. **EXTRACT TABLE DATA** - Read all rows/columns in data tables
5. **REPORT SPECIFIC NUMBERS** - Don't say "sales are down", say "Sales: $15,234 (-8.2% vs target)"

Examples of what to extract:
- Sales metrics (actual vs budget, variance %)
- Labor percentages (actual vs target)
- Food/beverage costs (COGS %)
- Guest counts and check averages
- Waste amounts and percentages
- Any red/yellow/green indicators and what they mean

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
YOU MUST EXTRACT AND REPORT ACTUAL NUMBERS FROM IMAGES:
- **SALES METRICS**: Actual $ amount, Budget/Target $, Variance % and $, Period comparison
- **LABOR METRICS**: Labor % actual vs target, dollar amounts, variance
- **FOOD COST**: Food cost %, beverage cost %, COGS actual vs target
- **GUEST METRICS**: Guest count, check average, per-person-average
- **OPERATIONAL METRICS**: Waste $, comps %, voids %, any other visible KPIs
- **TRENDS**: Read trend arrows, percentage changes, period-over-period data
- **STATUS INDICATORS**: What's green (good), yellow (warning), red (problem)
- **TABLE DATA**: Extract all visible rows and columns from data tables

Format: "Metric Name: $X,XXX (Target: $Y,YYY, Variance: +/-Z%)"
Example: "Net Sales: $47,892 (Budget: $52,000, -7.9% unfavorable)"

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

3. 📊 DASHBOARD INSIGHTS (RAP Mobile/Tableau Dashboard Images)
   🚨 MANDATORY: EXTRACT EVERY SINGLE NUMBER FROM THE DASHBOARD IMAGE 🚨

   DO NOT SKIP THIS SECTION IF IMAGES ARE PRESENT!
   YOU MUST LOOK AT THE IMAGE AND REPORT THESE METRICS:

   **Sales Performance:**
   - Net Sales: $[EXACT AMOUNT] ([+/-X.X%] vs LY, [+/-$XXX] vs budget)
   - Comp Sales: [+/-X.X%]
   - Traffic: [+/-X.X%]

   **Labor Performance:**
   - Labor Cost %: [XX.X%] (target: [XX%], variance: [+/-X.Xpp])
   - Labor $: $[EXACT AMOUNT]
   - Productivity: [X.X] covers per server

   **Cost Management:**
   - Food Cost: [XX.X%] ($[AMOUNT]) vs [XX%] target
   - Bar Cost: [XX.X%] ($[AMOUNT]) vs [XX%] target
   - Total COGS: [XX.X%] ($[AMOUNT])

   **Guest Metrics:**
   - Guest Count: [EXACT NUMBER] ([+/-X.X%] vs LY)
   - Check Average: $[XX.XX] ([+/-X.X%] vs LY)
   - Table Turns: [X.X]

   **Other Visible KPIs:**
   - [LIST EVERY OTHER METRIC YOU SEE WITH EXACT NUMBERS]

   **Performance Flags:**
   - 🔴 Below Target: [List metrics in RED with exact variance]
   - 🟢 Above Target: [List metrics exceeding target with numbers]

   ⚠️ FAILURE TO EXTRACT METRICS = UNACCEPTABLE ANALYSIS ⚠️

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

        print(f"[Vision] Found {len(stored_attachments)} image attachments in database for thread {thread_id}")

        # Add stored attachments that aren't already in all_images
        for att in stored_attachments:
            # Check if already included (by checking if data matches)
            if not any(img.get('data') == att.data for img in all_images):
                # Check if attachment has data
                if att.data:
                    print(f"[Vision] Adding DB attachment: {att.filename} ({att.mime_type}, {len(att.data)} bytes)")
                    all_images.append({
                        'mime_type': att.mime_type,
                        'data': att.data,
                        'filename': att.filename,
                        'size': att.size_bytes,
                        'from_db': True
                    })
                else:
                    print(f"[Vision] WARNING: DB attachment {att.filename} has no data! ID: {att.id}")
    
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
            "content": "You are AUBS - Auburn Hills Assistant. Direct, helpful, restaurant-savvy. YOU MUST analyze text AND images, extracting SPECIFIC METRICS from dashboards."
        }
    ]

    # Build custom prompt for RAP Mobile dashboards
    dashboard_extraction_prompt = ""
    if is_dashboard_email and all_images:
        dashboard_extraction_prompt = """
🚨🚨🚨 CRITICAL: RAP MOBILE DASHBOARD DETECTED 🚨🚨🚨

THIS IS NOT A SUBSCRIPTION EMAIL! This is a PERFORMANCE DASHBOARD with critical business metrics.

YOU MUST EXTRACT ALL VISIBLE NUMBERS FROM THE DASHBOARD IMAGE:
1. Look at EVERY metric shown in the image
2. Report EXACT numbers, percentages, and dollar amounts
3. Include variance from target/budget/LY (Last Year)
4. Note any RED indicators or below-target metrics
5. DO NOT say "the dashboard shows performance" - GIVE ME THE ACTUAL NUMBERS!

Example of what I expect:
❌ WRONG: "Sales are below target"
✅ RIGHT: "Sales: $47,892 (-7.9% vs LY, -$4,108 vs budget)"

❌ WRONG: "Labor costs are high"
✅ RIGHT: "Labor: 34.2% ($16,421) vs 31% target (+3.2pp, +$1,542 over)"

EXTRACT THESE SPECIFIC METRICS FROM THE IMAGE:
- Net Sales: $ amount, % vs LY, $ vs budget
- Labor Cost: % and $ amount, variance from target
- Food Cost: % and $ amount, variance from target
- Bar Cost: % and $ amount, variance from target
- Guest Count: actual number, % change vs LY
- Check Average: $ amount, % change vs LY
- Server Productivity: covers per server
- Any other KPIs visible in the dashboard

THIS IS YOUR PRIMARY JOB - EXTRACT THE METRICS!
"""

    # Build user message with text and images
    user_content = [
        {
            "type": "text",
            "text": f"""{OPS_TRIAGE_PROMPT}

{time_context}

THREAD TO ANALYZE:
{thread_context}

{dashboard_extraction_prompt if dashboard_extraction_prompt else ""}

{"📊 IMAGES ATTACHED: Extract ALL metrics, numbers, percentages from the dashboard images!" if all_images else ""}

Provide both:
1. A detailed human-readable summary following the format above (use AUBS voice)
2. A JSON structure with extracted tasks for the todo system
"""
        }
    ]
    
    # Add images if present and vision is enabled
    if use_vision and all_images:
        print(f"[Vision] Processing {len(all_images)} images for vision analysis")
        print(f"[Vision] Dashboard email detected: {is_dashboard_email}")
        images_added = 0
        for idx, img in enumerate(all_images[:5]):  # Limit to 5 images to stay within token limits
            if img.get("data"):
                # Log what we're sending
                filename = img.get('filename', 'unknown')
                print(f"[Vision] Adding image {idx+1}: {filename} ({img.get('mime_type', 'unknown')}, {len(img['data'])} bytes)")

                # Extra logging for RAP Mobile images
                if is_dashboard_email:
                    print(f"[Vision] 🎯 RAP MOBILE IMAGE: {filename} - AI MUST extract metrics from this!")

                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{img['mime_type']};base64,{img['data']}"
                    }
                })
                images_added += 1
            else:
                print(f"[Vision] Skipping image {idx+1}: {img.get('filename', 'unknown')} - no data field")

        # Log summary
        print(f"[Vision] Sent {images_added} images to GPT-4o vision API")
        if is_dashboard_email:
            print("[Vision] 🚨 DASHBOARD MODE: AI should extract specific metrics!")
    
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

        # Log if this was a dashboard analysis
        if is_dashboard_email:
            print("[Vision] 📊 Dashboard Analysis Response Received")
            # Check if metrics were extracted
            metrics_found = any(char in content for char in ['$', '%'] if char in content)
            if metrics_found:
                # Count how many dollar amounts and percentages
                dollar_count = content.count('$')
                percent_count = content.count('%')
                print(f"[Vision] ✅ Metrics found: {dollar_count} dollar amounts, {percent_count} percentages")
            else:
                print("[Vision] ⚠️ WARNING: No metrics ($, %) found in response!")
                print("[Vision] AI may have ignored dashboard extraction instructions!")

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
                # Use structured entity extraction to avoid example names
                from services.entity_schema import extract_entity_names
                entities = extract_entity_names(content, source='email')

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
