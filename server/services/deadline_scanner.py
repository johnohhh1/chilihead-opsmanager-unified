"""
Brinker/Allen Deadline Scanner
Searches Gmail for deadline-driven emails and produces structured output
"""

import os
import httpx
from dotenv import load_dotenv
from .gmail import get_user_threads, get_thread_messages
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

DEADLINE_SCANNER_PROMPT = """You are John's restaurant operations assistant. Today is {current_datetime} (Eastern Time).

Scan these emails and find ANYTHING with a deadline, due date, or time-sensitive action. Look for:
- Schedule submissions (P5, manager schedules, etc.)
- Reports due (labor, sales, safety, etc.)
- Training deadlines
- Compliance items
- Payroll issues that need action by a certain time
- Meeting times
- Anything that says "by Friday," "due Oct 20," "submit by 5pm," etc.

For each deadline you find, create a table row with:

| # | What needs to be done | When it's due | Calendar Entry | Email Link |
|---|----------------------|---------------|----------------|------------|
| 1 | Submit manager schedule for Period 5 | Friday Oct 18 at 5pm | Title: Submit P5 Manager Schedule<br>Date: 2025-10-18<br>Time: 5:00 PM America/Detroit<br>Reminder: 3 days prior | [View](gmail_link) |

**Format the Calendar Entry like this:**
- Title: Short, actionable title (like "Submit P5 Schedule" or "Complete Safety Training")
- Date: YYYY-MM-DD format
- Time: Actual time if mentioned, otherwise 10:00 AM America/Detroit
- Reminder: 3 days prior

**After the table, add a quick summary:**
### What's Due:
- **Today**: [list items due today]
- **This Week**: [list items due this week]
- **Later**: [list items due later]

If there are NO deadlines found, just say "No urgent deadlines found in recent emails."

**Be practical:**
- If an email mentions multiple deadlines, create separate rows for each
- Convert vague dates like "EOD" to 5:00 PM today, "tomorrow" to the actual date, etc.
- Include the Gmail link so John can click through to read the full email

EMAILS TO SCAN:
{email_data}
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

def scan_deadlines(model: str = "gpt-4o") -> dict:
    """
    Run the Brinker/Allen deadline scanner
    Returns structured deadline report
    """
    from .model_provider import ModelProvider

    # Get current time in Detroit timezone
    detroit_tz = pytz.timezone('America/Detroit')
    now_detroit = datetime.now(detroit_tz)
    current_datetime = now_detroit.strftime('%A, %B %d, %Y at %I:%M %p ET')

    # Build Gmail query for deadline emails
    # Primary: last 24 hours
    # Backstop: last 7 days
    sender_query = "(from:allen.woods@brinker.com OR from:@brinker.com OR from:@chilis.com OR from:c00605mgr@chilis.com)"
    keyword_query = "(schedule OR due OR deadline OR submit OR EOP OR labor OR report OR Oracle OR Fusion)"

    # Get threads from last 7 days (we'll filter by date in the AI prompt)
    gmail_query = f"{sender_query} {keyword_query} newer_than:7d"

    try:
        threads = get_user_threads(max_results=100, query=gmail_query)

        if not threads:
            return {
                "report": "No new deadlines.",
                "deadlines": [],
                "generated_at": now_detroit.isoformat()
            }

        # Extract email data for AI analysis
        email_data = []
        for thread in threads:
            thread_id = thread.get("id")
            msgs = get_thread_messages(thread_id)

            if not msgs:
                continue

            # Get the most recent message in thread
            msg = msgs[-1]
            headers = msg.get("payload", {}).get("headers", [])
            header_dict = {h["name"].lower(): h["value"] for h in headers}
            body = extract_message_body(msg.get("payload", {}))

            # Calculate how old the email is
            date_str = header_dict.get("date", "")
            email_age_hours = get_email_age_hours(date_str, now_detroit)

            email_data.append({
                "thread_id": thread_id,
                "from": header_dict.get("from", ""),
                "subject": header_dict.get("subject", ""),
                "date": date_str,
                "age_hours": email_age_hours,
                "body": body[:2000],  # Limit body length
                "link": f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"
            })

        # Sort by age (newest first)
        email_data.sort(key=lambda x: x.get("age_hours", 999))

        # Call AI with deadline scanner prompt
        prompt = DEADLINE_SCANNER_PROMPT.format(
            current_datetime=current_datetime,
            email_data=json.dumps(email_data, indent=2)
        )

        messages = [
            {
                "role": "system",
                "content": "You are a precise deadline scanner. Follow the format exactly. Do not add extra commentary."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        report_text = ModelProvider.chat_completion_sync(
            messages=messages,
            model=model,
            temperature=0.2,
            max_tokens=2000
        )

        # Parse the report to extract structured deadline data
        deadlines = parse_deadline_report(report_text)

        return {
            "report": report_text,
            "deadlines": deadlines,
            "generated_at": now_detroit.isoformat(),
            "emails_analyzed": len(email_data)
        }

    except Exception as e:
        return {
            "report": f"⚠️ Error scanning deadlines: {str(e)}",
            "deadlines": [],
            "generated_at": now_detroit.isoformat()
        }

def get_email_age_hours(date_str: str, now_detroit: datetime) -> float:
    """Calculate how old an email is in hours"""
    try:
        from email.utils import parsedate_to_datetime
        email_dt = parsedate_to_datetime(date_str)
        age = now_detroit - email_dt
        return age.total_seconds() / 3600
    except:
        return 999  # Unknown age, put at end

def parse_deadline_report(report_text: str) -> list:
    """
    Parse the markdown table in the deadline report
    Extract structured deadline data for calendar integration
    """
    deadlines = []

    if "No new deadlines" in report_text:
        return deadlines

    # Find the table rows
    table_pattern = r'\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*\[View\]\((.+?)\)'
    matches = re.finditer(table_pattern, report_text, re.MULTILINE)

    for match in matches:
        number = match.group(1).strip()
        summary = match.group(2).strip()
        due_date = match.group(3).strip()
        calendar_entry = match.group(4).strip()
        link = match.group(5).strip()

        # Parse calendar entry details
        title_match = re.search(r'Title:\s*(.+?)(?:<br>|Date:)', calendar_entry, re.IGNORECASE)
        date_match = re.search(r'Date:\s*(.+?)(?:<br>|Time:)', calendar_entry, re.IGNORECASE)
        time_match = re.search(r'Time:\s*(.+?)(?:<br>|Reminder:)', calendar_entry, re.IGNORECASE)

        deadline = {
            "number": int(number) if number.isdigit() else 0,
            "summary": summary,
            "due_date": due_date,
            "calendar_title": title_match.group(1).strip() if title_match else summary,
            "calendar_date": date_match.group(1).strip() if date_match else None,
            "calendar_time": time_match.group(1).strip() if time_match else "10:00 AM America/Detroit",
            "gmail_link": link,  # Changed from "link" to "gmail_link" for frontend consistency
            "reminder_days": 3
        }

        deadlines.append(deadline)

    return deadlines
