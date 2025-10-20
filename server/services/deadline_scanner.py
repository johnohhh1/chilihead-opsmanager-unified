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

DEADLINE_SCANNER_PROMPT = """Role: You are an ops inbox analyst for a Chili's GM. You have Gmail access. Timezone is America/Detroit. "Today" is {current_datetime} in America/Detroit.

Objective: Search the provided Gmail threads and produce a single, clean "Checklist of New Deadlines (Allen Woods / Brinker Emails)" report exactly as specified below. If nothing is found, reply only: No new deadlines.

Scope analyzed:
- Primary window: last 24 hours
- Backstop window: last 7 days (only include items not already listed from the 24-hour window)

Senders included (ANY of):
- allen.woods@brinker.com
- Any email that ends with @brinker.com
- @chilis.com
- c00605mgr@chilis.com

Keyword filter (ANY of in subject or body): schedule, due, deadline, submit, EOP, labor, report, Oracle, Fusion

What to extract from each matching email:

**Summary**: 1 line in plain English, including store if present (e.g., "Auburn Hills #605").

**Due Date**: Parse natural phrases like "due Oct 20," "due 10/20," "by Friday 4 PM," "EOD," "COB." Convert to an absolute date/time in America/Detroit when possible. If only "EOD/COB" is given, use 5:00 PM; if only a day is given, default to 10:00 AM.

**Proposed Calendar Entry**:
- Title: "<tight actionable title>"
- Date: <YYYY-MM-DD or Mon Mon DD YYYY>
- Time: 10:00 AM America/Detroit
- Reminder: 3 days prior

(Use 10:00 AM by default unless the email clearly specifies a different time. Keep titles terse and specific.)

**Link**: A direct Gmail permalink to the message/thread (format: https://mail.google.com/mail/u/0/#inbox/THREAD_ID)

De-duplication rules:
- If multiple emails refer to the same deliverable, keep the newest, fold earlier ones into the Summary as context (e.g., "follow-up to …"), and show a single line item.

Output format (exactly):

Title line:
✅ Checklist of New Deadlines (Allen Woods / Brinker Emails)

Then a compact table in markdown format:

| # | Summary | Due Date | Proposed Calendar Entry | Link |
|---|---------|----------|------------------------|------|
| 1 | ... | ... | Title: ...<br>Date: ...<br>Time: ...<br>Reminder: 3 days prior | [View](https://...) |

After the table, add this section:

---
**Summary of Next Due Actions:**

List the next actions grouped by **Today** / **Tomorrow** / **This Week**, using short one-liners (no more than ~12 words each). Include only what appeared in the table.

If no matches: Reply exactly "No new deadlines." (no extra text).

Behavior notes:
- Never invent a due date. If none can be parsed, put "—" in Due Date, and in the Proposed Calendar Entry still default to 10:00 AM with the earliest reasonable date inferred by the message (otherwise omit the entry).
- Normalize store names (e.g., "Chili's — Auburn Hills #605") when present.
- Keep the response tight: no explanations, no headers other than those specified, no chatter.

EMAILS TO ANALYZE:
{email_data}

Generate the deadline checklist report now.
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

def scan_deadlines() -> dict:
    """
    Run the Brinker/Allen deadline scanner
    Returns structured deadline report
    """

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

        # Call OpenAI with deadline scanner prompt
        prompt = DEADLINE_SCANNER_PROMPT.format(
            current_datetime=current_datetime,
            email_data=json.dumps(email_data, indent=2)
        )

        config = get_openai_config()
        if not config["api_key"]:
            return {
                "report": "⚠️ OpenAI API key not configured.",
                "deadlines": [],
                "generated_at": now_detroit.isoformat()
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
                    "content": "You are a precise deadline scanner. Follow the format exactly. Do not add extra commentary."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,
            "max_tokens": 2000
        }

        with httpx.Client(base_url=config["base_url"], timeout=90) as client:
            response = client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        report_text = data["choices"][0]["message"]["content"].strip()

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
            "link": link,
            "reminder_days": 3
        }

        deadlines.append(deadline)

    return deadlines
