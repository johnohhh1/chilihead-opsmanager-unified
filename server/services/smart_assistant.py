"""
AI-powered email triage that actually understands context
Not just pattern matching - real comprehension
"""

import os
import httpx
from dotenv import load_dotenv
from .gmail import get_thread_messages
import json
from datetime import datetime, timedelta
import re
import pytz

load_dotenv()

def get_openai_config():
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o",
        "project_id": os.getenv("OPENAI_PROJECT_ID"),
        "org_id": os.getenv("OPENAI_ORG_ID")
    }

# AUBS PERSONA - Auburn Hills Assistant
AUBS_PERSONA = """
You are AUBS (Auburn Hills Assistant) - John's operations AI for Chili's #605.

PERSONALITY:
- Direct, no-nonsense, like a trusted GM who's seen it all
- Midwest-friendly but gets straight to the point
- Uses restaurant lingo naturally (86'd, in the weeds, BOH, FOH)
- Calls out problems clearly but offers solutions
- Has your back but won't sugarcoat issues

SPEECH PATTERNS:
- "Here's the deal..." when getting to the point
- "Heads up..." for warnings
- "Real talk..." when being blunt
- "You're in the weeds on..." when overwhelmed
- "Let's knock out..." for action items
"""

# More natural, context-aware prompt with AUBS
SMART_ASSISTANT_PROMPT_TEMPLATE = """
{aubs_persona}

You read John's restaurant emails and tell him EXACTLY what he needs to do - in AUBS voice.

Your job is NOT to reformat emails. Your job is to:
1. Understand what's actually happening
2. Figure out what John needs to do about it
3. Tell him straight - like a trusted GM would
4. **EXTRACT specific actionable tasks with deadlines**

Context:
- John manages Chili's Auburn Hills #605
- Current time: {current_time}
- He gets bombarded with corporate emails, many are FYI, some need action

CRITICAL: Be smart about what's actually important. Examples:

BAD: "Follow up with Payroll department regarding pay card registration"
GOOD: "Hannah Zimmerman hasn't been paid in 48 HOURS. Call payroll NOW at xxx-xxx-xxxx to fix her card. This is affecting her ability to pay bills."

BAD: "Review P5 Manager Schedule submission requirements"
GOOD: "Manager schedule for P5 is due Friday Oct 18 by 5pm. Takes about 30 min. Submit through Oracle Portal > Scheduling > P5 Upload"

BAD: "Address coverage needed for shift"
GOOD: "Blake called off for tonight's dinner shift (5-10pm). You need coverage ASAP. Sarah and Mike are off today - try calling them first."

For each email thread, provide:

## Analysis
Write a conversational summary explaining what's happening and why it matters.

## Priority Level
- 🔴 URGENT: Someone's not getting paid, coverage needed TODAY, deadline in <24 hrs
- 🟡 HIGH: Due this week, affects operations
- 🟢 NORMAL: Regular tasks, reports
- ⚪ FYI: No action needed, just awareness

## Action Items
**IMPORTANT**: List SPECIFIC, ACTIONABLE tasks. Each task must include:
- Clear action verb (Call, Email, Submit, Review, etc.)
- WHO/WHAT/WHERE details
- **DUE DATE/TIME** if mentioned (use format: "Due: Friday Oct 18 at 5pm" or "Due: Today by 3pm")
- Time estimate if you can infer it

Format action items as a bulleted list like:
- **[ACTION]**: [Detailed description]. Due: [specific date/time]. Estimate: [time]

Example action items:
- **Call Payroll**: Contact payroll dept at 800-555-1234 to fix Hannah Zimmerman's pay card issue. Due: Today ASAP. Estimate: 15 min
- **Submit P5 Schedule**: Upload manager schedule through Oracle Portal > Scheduling > P5 Upload. Due: Friday Oct 18 at 5pm. Estimate: 30 min
- **Find Coverage**: Call Sarah (555-1234) or Mike (555-5678) to cover Blake's dinner shift tonight 5-10pm. Due: Today by 3pm. Estimate: 20 min

## Calendar Events
If there are meetings, appointments, or time-specific events, list them separately:
- **[EVENT]**: [Description]. When: [Date and time]. Location: [if mentioned]

IMPORTANT:
- ALWAYS extract specific deadlines and due dates/times
- ALWAYS look for "by when" information in the email
- If no specific deadline is mentioned but action is needed, say "Due: ASAP" or "Due: This week"
- Many corporate emails sound urgent but aren't. Use your judgment.

Format your response with clear markdown headings (## Analysis, ## Priority Level, ## Action Items, ## Calendar Events).
"""

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

def smart_triage(thread_id: str, model: str = "gpt-4o", db = None) -> dict:
    """
    Actually understand the email and provide intelligent analysis
    Not just reformatting - real comprehension
    """
    from .model_provider import ModelProvider

    msgs = get_thread_messages(thread_id)
    if not msgs:
        return {"analysis": "No messages found", "tasks": []}

    # Get full thread content
    thread_data = []
    for msg in msgs[-3:]:  # Last 3 messages for context
        headers = msg.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}
        body = extract_message_body(msg.get("payload", {}))

        thread_data.append({
            "from": header_dict.get("from", ""),
            "to": header_dict.get("to", ""),
            "subject": header_dict.get("subject", ""),
            "date": header_dict.get("date", ""),
            "body": body[:2000]  # Limit body length
        })

    current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p ET')

    prompt = SMART_ASSISTANT_PROMPT_TEMPLATE.format(
        aubs_persona=AUBS_PERSONA,
        current_time=current_time
    )
    prompt += "\n\nEMAIL THREAD TO ANALYZE:\n"
    prompt += json.dumps(thread_data, indent=2)
    prompt += "\n\nProvide your analysis and extracted action items in a conversational but structured way."

    messages = [
        {
            "role": "system",
            "content": "You are an intelligent executive assistant. Be practical, specific, and understand context. Don't just reformat - actually comprehend what needs to be done."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        analysis = ModelProvider.chat_completion_sync(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=1500
        )

        # Extract specific tasks if mentioned
        tasks = extract_smart_tasks(analysis, thread_data)

        result = {
            "analysis": analysis,
            "tasks": tasks,
            "thread_id": thread_id
        }

        # Cache email and analysis if database provided
        if db:
            try:
                from services.email_sync import EmailSyncService
                from datetime import datetime

                # Cache the raw email
                EmailSyncService.cache_email(
                    db=db,
                    thread_id=thread_id,
                    gmail_message_id=gmail_message['id'],
                    subject=thread_data[0].get('subject', ''),
                    sender=thread_data[0].get('from', ''),
                    recipients={'to': [thread_data[0].get('to', '')]},
                    body_text=thread_data[0].get('body', ''),
                    body_html='',
                    attachments=[],
                    labels=gmail_message.get('labelIds', []),
                    received_at=datetime.now(),
                    has_images=False
                )

                # Determine priority and category
                priority_score = 70  # Default
                category = 'routine'
                if "🔴" in analysis or "URGENT" in analysis.upper():
                    priority_score = 90
                    category = 'urgent'
                elif "🟡" in analysis or "HIGH" in analysis.upper():
                    priority_score = 75
                    category = 'important'

                # Cache the analysis
                EmailSyncService.cache_analysis(
                    db=db,
                    thread_id=thread_id,
                    analysis_json=result,
                    model_used=model,
                    priority_score=priority_score,
                    category=category,
                    key_entities={'tasks': [t['action'] for t in tasks]},
                    suggested_tasks=tasks,
                    sentiment='neutral',
                    tokens_used=1500  # Estimate
                )
            except Exception as cache_error:
                print(f"Warning: Failed to cache analysis: {cache_error}")

        return result

    except Exception as e:
        return {
            "analysis": f"Error: {str(e)}",
            "tasks": [],
            "thread_id": thread_id
        }

def extract_smart_tasks(analysis: str, thread_data: list) -> list:
    """
    Extract actionable tasks from the AI analysis
    Parse the markdown-formatted Action Items section
    """
    tasks = []

    # Determine overall priority from Priority Level section
    default_priority = "normal"
    if "🔴" in analysis or "URGENT" in analysis.upper():
        default_priority = "urgent"
    elif "🟡" in analysis or "HIGH" in analysis.upper():
        default_priority = "high"

    # Find the Action Items section
    action_items_match = re.search(r'## Action Items\s*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL | re.IGNORECASE)

    if not action_items_match:
        # Fallback: look for bullet points anywhere in analysis
        lines = analysis.split('\n')
        action_items_text = '\n'.join([line for line in lines if line.strip().startswith('-') or line.strip().startswith('*')])
    else:
        action_items_text = action_items_match.group(1)

    # Parse each bullet point as a task
    bullet_pattern = r'[-*]\s*\*\*(.+?)\*\*:?\s*(.+?)(?=\n[-*]|\Z)'
    matches = re.finditer(bullet_pattern, action_items_text, re.DOTALL)

    for match in matches:
        action_title = match.group(1).strip()
        description = match.group(2).strip()
        full_text = f"{action_title}: {description}"

        # Extract due date from "Due: ..." pattern
        due_date = None
        due_match = re.search(r'Due:\s*(.+?)(?:\.|Estimate:|$)', description, re.IGNORECASE)
        if due_match:
            due_text = due_match.group(1).strip().lower()
            due_date = parse_due_date(due_text)

        # Extract time estimate from "Estimate: X min/hour" pattern
        time_estimate = None
        estimate_match = re.search(r'Estimate:\s*(\d+)\s*(min|hour|hr)', description, re.IGNORECASE)
        if estimate_match:
            amount = int(estimate_match.group(1))
            unit = estimate_match.group(2).lower()
            if 'hour' in unit or 'hr' in unit:
                time_estimate = f"{amount} hour" if amount == 1 else f"{amount} hours"
            else:
                time_estimate = f"{amount} min"

        # Determine task priority
        task_priority = default_priority
        description_lower = description.lower()
        if 'urgent' in description_lower or 'asap' in description_lower or 'now' in description_lower:
            task_priority = "urgent"
        elif 'high' in description_lower or 'important' in description_lower:
            task_priority = "high"

        # Create task
        task = {
            "action": full_text,
            "priority": task_priority,
            "due_date": due_date,
            "time_estimate": time_estimate,
            "source": thread_data[0]['from'] if thread_data else "Unknown",
            "type": "calendar_event" if "meeting" in full_text.lower() or "appointment" in full_text.lower() else "task"
        }

        tasks.append(task)

    # Also extract Calendar Events if present
    calendar_match = re.search(r'## Calendar Events\s*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL | re.IGNORECASE)
    if calendar_match:
        calendar_text = calendar_match.group(1)
        calendar_bullets = re.finditer(bullet_pattern, calendar_text, re.DOTALL)

        for match in calendar_bullets:
            event_title = match.group(1).strip()
            description = match.group(2).strip()
            full_text = f"{event_title}: {description}"

            # Extract "When: ..." for calendar events
            when_match = re.search(r'When:\s*(.+?)(?:\.|Location:|$)', description, re.IGNORECASE)
            due_date = None
            if when_match:
                when_text = when_match.group(1).strip().lower()
                due_date = parse_due_date(when_text)

            task = {
                "action": full_text,
                "priority": "normal",
                "due_date": due_date,
                "time_estimate": None,
                "source": thread_data[0]['from'] if thread_data else "Unknown",
                "type": "calendar_event"
            }

            tasks.append(task)

    return tasks

def parse_due_date(due_text: str) -> str:
    """
    Parse natural language due date into YYYY-MM-DD format
    Handles: today, tomorrow, Friday, Oct 18, etc.
    """
    due_text = due_text.lower().strip()
    now = datetime.now()

    # Handle "today", "tonight", "asap"
    if 'today' in due_text or 'tonight' in due_text or 'asap' in due_text:
        return now.strftime('%Y-%m-%d')

    # Handle "tomorrow"
    if 'tomorrow' in due_text:
        return (now + timedelta(days=1)).strftime('%Y-%m-%d')

    # Handle day of week (e.g., "Friday", "next Monday")
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days_of_week):
        if day in due_text:
            current_day = now.weekday()  # 0=Monday, 6=Sunday
            target_day = i

            # Calculate days until target day
            days_ahead = target_day - current_day
            if days_ahead <= 0 or 'next' in due_text:  # Target day already passed this week or explicitly "next"
                days_ahead += 7

            target_date = now + timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')

    # Handle "this week"
    if 'this week' in due_text:
        # Default to Friday of current week
        days_until_friday = (4 - now.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        return (now + timedelta(days=days_until_friday)).strftime('%Y-%m-%d')

    # Handle specific dates like "Oct 18", "October 18", "10/18"
    # Try month name + day
    month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})', due_text)
    if month_match:
        month_abbr = month_match.group(1)
        day = int(month_match.group(2))

        months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        month = months.get(month_abbr)

        if month:
            year = now.year
            # If the date has passed this year, assume next year
            target_date = datetime(year, month, day)
            if target_date < now:
                target_date = datetime(year + 1, month, day)

            return target_date.strftime('%Y-%m-%d')

    # Try MM/DD or M/D format
    date_match = re.search(r'(\d{1,2})/(\d{1,2})', due_text)
    if date_match:
        month = int(date_match.group(1))
        day = int(date_match.group(2))
        year = now.year

        try:
            target_date = datetime(year, month, day)
            if target_date < now:
                target_date = datetime(year + 1, month, day)
            return target_date.strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Default: no specific date found
    return None

def daily_digest(model: str = "gpt-4o", db = None) -> dict:
    """
    Generate a daily digest of all important items
    Like a morning briefing from your assistant
    Now uses agent memory for better context!
    """
    from .gmail import get_user_threads
    from .priority_filter import load_watch_config
    from .model_provider import ModelProvider

    # Use Eastern Time for all operations
    eastern = pytz.timezone('America/New_York')
    current_time = datetime.now(eastern)
    
    # Get today's emails from watched senders
    config = load_watch_config()
    
    # Build Gmail query for today's important emails
    query_parts = []
    
    # Add watched senders/domains
    sender_parts = []
    for sender in config.get("priority_senders", []):
        sender_parts.append(f"from:{sender}")
    for domain in config.get("priority_domains", []):
        sender_parts.append(f"from:*@{domain}")
    
    if sender_parts:
        query_parts.append(f"({' OR '.join(sender_parts)})")
    
    # Add time filter - last 24 hours
    query_parts.append("newer_than:1d")
    
    gmail_query = " ".join(query_parts)
    
    try:
        # Get threads from last 24 hours
        threads = get_user_threads(max_results=50, query=gmail_query)
        
        if not threads:
            return {
                "digest": f"Good morning John! No urgent emails in the last 24 hours. You're all caught up for {current_time.strftime('%A, %B %d, %Y')}! ✅",
                "generated_at": current_time.isoformat()
            }
        
        # Prepare email summaries for AI
        email_summaries = []
        for thread in threads[:20]:  # Limit to 20 most recent
            msgs = thread.get("messages", [])
            if msgs:
                headers = {h["name"].lower(): h["value"] for h in msgs[0].get("payload", {}).get("headers", [])}
                body = extract_message_body(msgs[0].get("payload", {}))
                
                email_summaries.append({
                    "from": headers.get("from", ""),
                    "subject": headers.get("subject", ""),
                    "date": headers.get("date", ""),
                    "snippet": body[:500]  # First 500 chars
                })
        
        # Get agent memory context if database provided
        agent_context = ""
        if db:
            try:
                from services.agent_memory import AgentMemoryService
                agent_context = AgentMemoryService.get_digest_context(db, hours=24)
            except Exception as e:
                print(f"Warning: Could not load agent memory: {e}")

        # Generate AI digest
        prompt = f"""
You are AUBS (Auburn Hills Assistant) - John's executive assistant.

TODAY'S DATE: {current_time.strftime('%A, %B %d, %Y')}
CURRENT TIME: {current_time.strftime('%I:%M %p ET')}

CONTEXT FROM YOUR RECENT WORK:
{agent_context if agent_context else "(No recent agent activity to reference)"}

The context above shows what you (and other AI agents) have already analyzed, flagged, or discussed.
Use this to avoid redundancy and build on previous findings.

Review these {len(email_summaries)} emails from the last 24 hours and create a morning operations brief.

EMAILS:
{json.dumps(email_summaries, indent=2)}

Create a brief that includes:

🔴 URGENT ITEMS (needs action TODAY - like payroll issues, coverage needed, deadlines in <24hrs)
🟡 TODAY'S DEADLINES (specific tasks due today with times)
📊 PATTERNS I'VE NOTICED (recurring issues, trends)
💡 SUGGESTIONS (proactive advice)

Be specific, conversational, and helpful. Include details like:
- Who to contact and how
- When things are due
- Why it matters
- What happens if ignored

If there are no urgent items, say so clearly. Don't make up fake issues.
"""

        messages = [
            {"role": "system", "content": "You are AUBS - Auburn Hills Assistant. You are an intelligent executive assistant who understands context and priorities."},
            {"role": "user", "content": prompt}
        ]

        digest_text = ModelProvider.chat_completion_sync(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=3000  # Increased from 1000 for more detailed output
        )

        # Record digest generation to agent memory
        if db:
            try:
                from services.agent_memory import AgentMemoryService

                # Extract key findings from digest text
                key_findings = {
                    'emails_analyzed': len(email_summaries),
                    'has_urgent': '🔴' in digest_text or 'URGENT' in digest_text.upper(),
                    'has_deadlines': '🟡' in digest_text or 'DEADLINE' in digest_text.upper()
                }

                AgentMemoryService.record_event(
                    db=db,
                    agent_type='daily_brief',
                    event_type='digest_generated',
                    summary=f"Generated daily digest analyzing {len(email_summaries)} emails",
                    context_data={
                        'digest_preview': digest_text[:500],
                        'email_count': len(email_summaries),
                        'generated_time': current_time.strftime('%I:%M %p ET')
                    },
                    key_findings=key_findings,
                    model_used=model,
                    confidence_score=90
                )
            except Exception as mem_error:
                print(f"Warning: Failed to record digest to agent memory: {mem_error}")

        return {
            "digest": digest_text,
            "generated_at": current_time.isoformat(),
            "emails_analyzed": len(email_summaries)
        }
        
    except Exception as e:
        return {
            "digest": f"⚠️ Error generating digest: {str(e)}",
            "generated_at": current_time.isoformat()
        }
