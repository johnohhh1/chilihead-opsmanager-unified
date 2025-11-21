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
    Includes vision support for RAP Mobile dashboards and other images
    """
    from .model_provider import ModelProvider
    from .ai_triage import extract_attachments_with_images
    from .gmail import get_service

    try:
        msgs = get_thread_messages(thread_id)
        if not msgs:
            return {"analysis": "No messages found", "tasks": [], "thread_id": thread_id}

        # Get full thread content with image support
        thread_data = []
        all_images = []

        for msg in msgs[-3:]:  # Last 3 messages for context
            headers = msg.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers}

            # Extract both text and images
            body, images = extract_attachments_with_images(msg.get("payload", {}))

            # Download any attachment images
            for img in images:
                if img.get('attachment_id') and not img.get('data'):
                    try:
                        service = get_service()
                        attachment = service.users().messages().attachments().get(
                            userId='me',
                            messageId=msg.get('id'),
                            id=img['attachment_id']
                        ).execute()
                        img['data'] = attachment.get('data')
                    except Exception as img_error:
                        print(f"Warning: Failed to download attachment: {img_error}")

            all_images.extend(images)

            thread_data.append({
                "from": header_dict.get("from", ""),
                "to": header_dict.get("to", ""),
                "subject": header_dict.get("subject", ""),
                "date": header_dict.get("date", ""),
                "body": body[:2000],  # Limit body length
                "has_images": len(images) > 0
            })

        current_time = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p ET')

        prompt = SMART_ASSISTANT_PROMPT_TEMPLATE.format(
            aubs_persona=AUBS_PERSONA,
            current_time=current_time
        )
        prompt += "\n\nEMAIL THREAD TO ANALYZE:\n"
        prompt += json.dumps(thread_data, indent=2)

        if all_images:
            prompt += f"\n\n📸 This email contains {len(all_images)} image(s). Analyze any dashboards or screenshots for key metrics."

        prompt += "\n\nProvide your analysis and extracted action items in a conversational but structured way."

        # Build message content - add images if available and model supports vision
        messages = [
            {
                "role": "system",
                "content": "You are an intelligent executive assistant with vision capabilities. Analyze text AND images to provide comprehensive analysis."
            }
        ]

        # Add user message with images if using vision model
        user_content = []
        user_content.append({"type": "text", "text": prompt})

        # Add images for vision models (gpt-4o, claude-3-opus, etc.)
        if all_images and model in ['gpt-4o', 'gpt-4-vision-preview', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229']:
            for img in all_images[:3]:  # Limit to 3 images to avoid token limits
                if img.get('data'):
                    # Gmail uses URL-safe base64
                    image_data = img['data'].replace('-', '+').replace('_', '/')
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img.get('mime_type', 'image/png')};base64,{image_data}",
                            "detail": "high"  # High detail for dashboards
                        }
                    })

        messages.append({
            "role": "user",
            "content": user_content if len(user_content) > 1 else prompt
        })

        analysis = ModelProvider.chat_completion_sync(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=2000  # Increased for vision analysis
        )

        # Extract specific tasks if mentioned
        tasks = extract_smart_tasks(analysis, thread_data)

        result = {
            "analysis": analysis,
            "tasks": tasks,
            "thread_id": thread_id,
            "has_images": len(all_images) > 0,
            "image_count": len(all_images)
        }

        # Cache email and analysis if database provided
        if db:
            try:
                from services.email_sync import EmailSyncService

                # Get the latest message for caching
                gmail_message = msgs[-1] if msgs else {}

                # Cache the raw email
                EmailSyncService.cache_email(
                    db=db,
                    thread_id=thread_id,
                    gmail_message_id=gmail_message.get('id', thread_id),
                    subject=thread_data[0].get('subject', ''),
                    sender=thread_data[0].get('from', ''),
                    recipients={'to': [thread_data[0].get('to', '')]},
                    body_text=thread_data[0].get('body', ''),
                    body_html='',
                    attachments=all_images,
                    labels=gmail_message.get('labelIds', []),
                    received_at=datetime.now(),
                    has_images=len(all_images) > 0
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
                    tokens_used=2000  # Estimate
                )
            except Exception as cache_error:
                print(f"Warning: Failed to cache analysis: {cache_error}")
                # Don't fail the whole request if caching fails
                import traceback
                traceback.print_exc()

        return result

    except Exception as e:
        print(f"Error in smart_triage: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "analysis": f"Error analyzing email: {str(e)}",
            "tasks": [],
            "thread_id": thread_id,
            "error": True
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

def get_dismissed_identifiers(db) -> set:
    """
    Get all currently dismissed item identifiers (email thread IDs, subjects, etc.)
    Returns a set for fast lookups
    """
    if not db:
        return set()

    try:
        from models import DismissedItem

        # Get non-expired dismissed items
        dismissed = db.query(DismissedItem).filter(
            (DismissedItem.is_permanent == True) |
            (DismissedItem.expires_at > datetime.now()) |
            (DismissedItem.expires_at == None)
        ).all()

        # Return set of identifiers for fast lookups
        return {d.identifier for d in dismissed}
    except Exception as e:
        print(f"Warning: Could not load dismissed items: {e}")
        return set()

def daily_digest(model: str = "gpt-4o", db = None) -> dict:
    """
    Generate a comprehensive daily digest combining:
    - Emails from last 24 hours
    - Tasks (overdue + due today)
    - Delegations (follow-ups needed)
    - Calendar events for today
    - Agent memory for enhanced context

    Phase 1 Enhancement: Multi-source intelligence with modern context engineering
    """
    from .gmail import get_user_threads
    from .priority_filter import load_watch_config
    from .model_provider import ModelProvider
    from models import Task, Delegation

    # Use Eastern Time for all operations
    eastern = pytz.timezone('America/New_York')
    current_time = datetime.now(eastern)
    today = current_time.date()

    # Get dismissed items to filter out
    dismissed_ids = get_dismissed_identifiers(db)

    # ========== DATA SOURCE 1: TASKS ==========
    tasks_context = {"overdue": [], "due_today": [], "high_priority": []}
    if db:
        try:
            # Get overdue tasks
            overdue_tasks = db.query(Task).filter(
                Task.status.in_(['todo', 'in_progress']),
                Task.due_date < today
            ).order_by(Task.priority.desc(), Task.due_date.asc()).all()

            # Get tasks due today
            today_tasks = db.query(Task).filter(
                Task.status.in_(['todo', 'in_progress']),
                Task.due_date == today
            ).order_by(Task.priority.desc()).all()

            # Get high priority tasks (next 3 days)
            next_3_days = today + timedelta(days=3)
            high_priority_tasks = db.query(Task).filter(
                Task.status.in_(['todo', 'in_progress']),
                Task.priority.in_(['urgent', 'high']),
                Task.due_date.between(today, next_3_days)
            ).order_by(Task.due_date.asc()).limit(5).all()

            tasks_context = {
                "overdue": [{
                    "title": t.title,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "priority": t.priority,
                    "description": t.description,
                    "eisenhower_quadrant": t.eisenhower_quadrant
                } for t in overdue_tasks],
                "due_today": [{
                    "title": t.title,
                    "priority": t.priority,
                    "description": t.description,
                    "eisenhower_quadrant": t.eisenhower_quadrant
                } for t in today_tasks],
                "high_priority": [{
                    "title": t.title,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "priority": t.priority,
                    "eisenhower_quadrant": t.eisenhower_quadrant
                } for t in high_priority_tasks]
            }
        except Exception as e:
            print(f"Warning: Could not load tasks: {e}")

    # ========== DATA SOURCE 2: DELEGATIONS ==========
    delegations_context = {"follow_ups_needed": [], "active_delegations": []}
    if db:
        try:
            # Get delegations needing follow-up today
            follow_up_delegations = db.query(Delegation).filter(
                Delegation.status.in_(['active', 'planning']),
                Delegation.follow_up_date == today
            ).all()

            # Get all active delegations
            active_delegations = db.query(Delegation).filter(
                Delegation.status == 'active'
            ).order_by(Delegation.due_date.asc()).limit(10).all()

            delegations_context = {
                "follow_ups_needed": [{
                    "task": d.task_description,
                    "assigned_to": d.assigned_to,
                    "due_date": d.due_date.isoformat() if d.due_date else None,
                    "priority": d.priority,
                    "progress": d.chilihead_progress
                } for d in follow_up_delegations],
                "active_delegations": [{
                    "task": d.task_description,
                    "assigned_to": d.assigned_to,
                    "due_date": d.due_date.isoformat() if d.due_date else None,
                    "status": d.status
                } for d in active_delegations]
            }
        except Exception as e:
            print(f"Warning: Could not load delegations: {e}")

    # ========== DATA SOURCE 3: CALENDAR (placeholder for future integration) ==========
    calendar_context = {"today_events": []}
    # TODO: Integrate with Google Calendar API when ready
    # For now, we'll extract calendar events from tasks with time-specific data

    # ========== DATA SOURCE 4: EMAILS ==========
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

        # Prepare email summaries for AI, filtering out dismissed items
        # Also check for BI portal results email and parse it
        email_summaries = []
        filtered_count = 0
        portal_metrics = None

        for thread in threads[:20]:  # Limit to 20 most recent
            thread_id = thread.get("id", "")
            msgs = thread.get("messages", [])
            if msgs:
                headers = {h["name"].lower(): h["value"] for h in msgs[0].get("payload", {}).get("headers", [])}
                subject = headers.get("subject", "")
                sender = headers.get("from", "")

                # Check if this is the BI portal results email
                from .portal_parser import PortalResultsParser
                if PortalResultsParser.is_bi_email(sender, subject):
                    try:
                        portal_metrics = PortalResultsParser.process_bi_email(msgs, db)
                        if portal_metrics:
                            print(f"✅ Parsed portal metrics from BI email")
                    except Exception as e:
                        print(f"Warning: Failed to parse portal metrics: {e}")

                # Skip if this thread or subject is dismissed
                if thread_id in dismissed_ids or subject in dismissed_ids:
                    filtered_count += 1
                    continue

                body = extract_message_body(msgs[0].get("payload", {}))

                email_summaries.append({
                    "thread_id": thread_id,
                    "from": sender,
                    "subject": subject,
                    "date": headers.get("date", ""),
                    "snippet": body[:500]  # First 500 chars
                })
        
        # ========== DATA SOURCE 5: ENHANCED AGENT MEMORY ==========
        # Modern context engineering: Provide structured, hierarchical context
        agent_context = ""
        if db:
            try:
                from services.agent_memory import AgentMemoryService
                agent_context = AgentMemoryService.get_digest_context(db, hours=24)
            except Exception as e:
                print(f"Warning: Could not load agent memory: {e}")

        # Add filtered count info
        filter_note = f"\n\nNOTE: {filtered_count} emails were filtered out because John already dismissed them." if filtered_count > 0 else ""

        # Format portal metrics if available
        portal_section = ""
        if portal_metrics:
            from .portal_parser import PortalResultsParser
            portal_section = f"\n\nPORTAL RESULTS (from yesterday's BI email):\n{PortalResultsParser.format_metrics_for_digest(portal_metrics)}\n"

        # ========== MODERN CONTEXT ENGINEERING ==========
        # Structure context hierarchically: Time-sensitive first, then operational, then informational

        # Build priority context summary
        priority_summary = []
        overdue_count = len(tasks_context.get("overdue", []))
        today_tasks_count = len(tasks_context.get("due_today", []))
        follow_ups_count = len(delegations_context.get("follow_ups_needed", []))

        if overdue_count > 0:
            priority_summary.append(f"⚠️ {overdue_count} overdue tasks")
        if today_tasks_count > 0:
            priority_summary.append(f"📅 {today_tasks_count} tasks due today")
        if follow_ups_count > 0:
            priority_summary.append(f"👥 {follow_ups_count} delegations need follow-up")

        priority_headline = " | ".join(priority_summary) if priority_summary else "All caught up!"

        # Generate AI digest with enhanced multi-source prompt
        prompt = f"""
You are AUBS (Auburn Hills Assistant) - John's executive COO assistant for Chili's #605.

TODAY'S DATE: {current_time.strftime('%A, %B %d, %Y')}
CURRENT TIME: {current_time.strftime('%I:%M %p ET')}

OPERATIONS SNAPSHOT: {priority_headline}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 YOUR TODO LIST (Tasks)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OVERDUE TASKS ({overdue_count}):
{json.dumps(tasks_context.get("overdue", []), indent=2) if overdue_count > 0 else "None - you're caught up!"}

DUE TODAY ({today_tasks_count}):
{json.dumps(tasks_context.get("due_today", []), indent=2) if today_tasks_count > 0 else "No tasks due today"}

HIGH PRIORITY (Next 3 Days):
{json.dumps(tasks_context.get("high_priority", []), indent=2)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 TEAM DELEGATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FOLLOW-UPS NEEDED TODAY ({follow_ups_count}):
{json.dumps(delegations_context.get("follow_ups_needed", []), indent=2) if follow_ups_count > 0 else "No follow-ups needed today"}

ACTIVE DELEGATIONS:
{json.dumps(delegations_context.get("active_delegations", []), indent=2)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 RECENT EMAILS ({len(email_summaries)} from last 24h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{json.dumps(email_summaries, indent=2)}{filter_note}

{portal_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 AGENT MEMORY (What I've noticed recently)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{agent_context if agent_context else "(No recent agent activity to reference)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR TASK:
Create a comprehensive morning operations brief that INTEGRATES all sources above.

Structure your brief like this:

## 🌶️ Good Morning John - {current_time.strftime('%A, %B %d')}

### 📊 PORTAL RESULTS
[If portal metrics provided, highlight key metrics and trends]

### 🔴 URGENT ACTION NEEDED TODAY
[Combine: Overdue tasks + Today's deadlines + Critical emails + Follow-ups needed]
- Be specific: WHO needs to be contacted, WHAT needs to happen, WHEN it's due
- Include phone numbers, portal links, specific deadlines
- Cross-reference tasks with emails (e.g., "You have a task to call payroll, and there's also an email about Hannah's pay card")

### 🟡 TODAY'S DEADLINES & TIME-BLOCKS
[List everything due today with specific times]
- Suggest when to tackle each item based on typical restaurant schedule
- Example: "Best time for paperwork: 2-4pm (between lunch/dinner rush)"

### 👥 TEAM CHECK-INS NEEDED
[Delegations follow-ups + any email mentions of team members]
- Who to follow up with and about what
- Progress on delegations

### 📈 PATTERNS & INSIGHTS
[What trends do you notice across tasks, emails, delegations?]
- Recurring issues (e.g., "3rd time this week someone called off for dinner shift")
- Bottlenecks in delegation progress
- Unusual metrics in portal

### 💡 PROACTIVE SUGGESTIONS
[What should John do to get ahead?]
- Suggest 2-3 proactive actions based on patterns
- Time-saving tips

### ✅ WINS & PROGRESS
[Acknowledge completed tasks, positive trends, good news from emails]

IMPORTANT:
- Don't just list items separately - INTEGRATE them (connect emails to tasks to delegations)
- Be conversational but direct (AUBS voice: "Here's the deal...")
- If something is truly urgent, say so clearly
- If there are no urgent items, celebrate that!
- Include specific action steps with WHO/WHAT/WHEN details
"""

        messages = [
            {"role": "system", "content": "You are AUBS - Auburn Hills Assistant. You synthesize multi-source operational data into actionable intelligence. You understand restaurant operations, prioritize based on urgency and impact, and provide context-aware recommendations."},
            {"role": "user", "content": prompt}
        ]

        # Fix timeout issue: Increase from default (likely 30s) to 120s for GPT-5
        digest_text = ModelProvider.chat_completion_sync(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=4000,  # Increased for comprehensive multi-source digest
            timeout=120  # 120 seconds to handle GPT-5 slowness
        )

        # Record digest generation to agent memory with comprehensive context
        if db:
            try:
                from services.agent_memory import AgentMemoryService

                # Extract key findings from digest text and data sources
                key_findings = {
                    'emails_analyzed': len(email_summaries),
                    'overdue_tasks_count': overdue_count,
                    'today_tasks_count': today_tasks_count,
                    'delegations_follow_ups': follow_ups_count,
                    'has_urgent': '🔴' in digest_text or 'URGENT' in digest_text.upper(),
                    'has_deadlines': '🟡' in digest_text or 'DEADLINE' in digest_text.upper(),
                    'has_portal_metrics': portal_metrics is not None,
                    'priority_headline': priority_headline
                }

                # Build comprehensive context data for future agents
                context_data = {
                    'digest_preview': digest_text[:800],  # More preview text
                    'email_count': len(email_summaries),
                    'tasks_summary': {
                        'overdue': overdue_count,
                        'due_today': today_tasks_count,
                        'high_priority': len(tasks_context.get("high_priority", []))
                    },
                    'delegations_summary': {
                        'follow_ups_needed': follow_ups_count,
                        'active_count': len(delegations_context.get("active_delegations", []))
                    },
                    'generated_time': current_time.strftime('%I:%M %p ET'),
                    'generated_date': current_time.strftime('%Y-%m-%d'),
                    'model_used': model
                }

                # Extract people and deadlines for entity tracking
                related_entities = {
                    'people': [d['assigned_to'] for d in delegations_context.get("follow_ups_needed", []) if d.get('assigned_to')],
                    'emails': [e['thread_id'] for e in email_summaries[:10]],  # Track top 10 emails
                    'tasks': [],  # Will be populated from task IDs if needed
                    'deadlines': [t['due_date'] for t in tasks_context.get("due_today", []) if t.get('due_date')]
                }

                AgentMemoryService.record_event(
                    db=db,
                    agent_type='daily_brief',
                    event_type='digest_generated',
                    summary=f"Generated comprehensive daily digest: {priority_headline}",
                    context_data=context_data,
                    key_findings=key_findings,
                    related_entities=related_entities,
                    model_used=model,
                    confidence_score=95  # Higher confidence with multi-source data
                )
            except Exception as mem_error:
                print(f"Warning: Failed to record digest to agent memory: {mem_error}")

        return {
            "digest": digest_text,
            "generated_at": current_time.isoformat(),
            "emails_analyzed": len(email_summaries),
            "data_sources": {
                "overdue_tasks": overdue_count,
                "today_tasks": today_tasks_count,
                "high_priority_tasks": len(tasks_context.get("high_priority", [])),
                "delegations_follow_ups": follow_ups_count,
                "active_delegations": len(delegations_context.get("active_delegations", [])),
                "emails": len(email_summaries),
                "portal_metrics": portal_metrics is not None
            },
            "priority_headline": priority_headline
        }
        
    except Exception as e:
        return {
            "digest": f"⚠️ Error generating digest: {str(e)}",
            "generated_at": current_time.isoformat()
        }
