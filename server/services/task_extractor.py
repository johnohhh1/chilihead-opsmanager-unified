"""
Enhanced email filtering with action item extraction and task management
"""

import json
import pathlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "watch_config.json"
TASK_STATE_PATH = pathlib.Path(__file__).parent.parent / "task_state.json"

def load_watch_config():
    """Load the watch configuration, with fallback defaults"""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Enhanced default config for action item extraction
        return {
            "priority_senders": [
                "c00605mgr@chilis.com",
                "allen.woods@brinker.com"
            ],
            "priority_domains": [
                "@hotschedules.com",
                "@fourth.com",
                "@brinker.com",
                "@chilis.com"
            ],
            "action_keywords": [
                # Emergency/911
                "called off", "no-show", "coverage needed", "left early", 
                "sick", "urgent", "ASAP", "911", "emergency",
                
                # Deadlines
                "due", "deadline", "submit", "by EOD", "by end of", 
                "must", "required by", "need by", "complete by",
                
                # Actions required
                "please", "can you", "could you", "will you",
                "need you to", "action required", "response required",
                "confirm", "approve", "review", "sign", "upload",
                
                # Schedule/shifts
                "schedule", "shift", "coverage", "swap", "trade",
                "open", "close", "inventory", "labor",
                
                # Reports/submissions
                "report", "Oracle", "Fusion", "Fourth", "HotSchedules",
                "P&L", "variance", "audit", "compliance"
            ],
            "emergency_keywords": [
                "911", "urgent", "emergency", "ASAP", "immediately",
                "called off", "no-show", "coverage needed"
            ],
            "auto_flag_as_important": True,
            "include_unread_only": False
        }

def save_watch_config(config: Dict):
    """Save updated configuration"""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def load_task_state():
    """Load task completion state"""
    try:
        with open(TASK_STATE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "completed": [],  # List of completed thread IDs
            "dismissed": [],  # List of dismissed/not important thread IDs
            "tasks": {}  # Thread ID -> extracted tasks mapping
        }

def save_task_state(state: Dict):
    """Save task state"""
    with open(TASK_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def extract_action_items(thread: Dict) -> List[Dict]:
    """
    Extract actionable items from an email thread
    Following the Ops Email Triage prompt patterns
    """
    config = load_watch_config()
    hotschedules_keywords = config.get("hotschedules_keywords", [])
    deadline_keywords = config.get("deadline_keywords", [])
    action_keywords = config.get("action_keywords", [])
    emergency_keywords = config.get("emergency_keywords", [])
    
    tasks = []
    
    # Get the latest message
    messages = thread.get("messages", [])
    if not messages:
        return tasks
    
    latest_msg = messages[-1]
    headers = latest_msg.get("payload", {}).get("headers", [])
    
    # Extract key info
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
    date_header = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
    
    # Get body text - need to extract from MIME structure
    body = extract_body_text(latest_msg.get("payload", {}))
    full_text = f"{subject} {body}".lower()
    snippet = thread.get("snippet", "")
    
    # Parse sender
    sender_name = from_header.split("<")[0].strip() if "<" in from_header else from_header
    sender_email = from_header.split("<")[1].replace(">", "").strip() if "<" in from_header else from_header
    
    # Check for 911/Emergency (HotSchedules pattern)
    is_911 = False
    if any(kw.lower() in sender_email.lower() for kw in ["hotschedules", "fourth"]):
        # Check for emergency keywords in HotSchedules emails
        if any(kw.lower() in full_text for kw in hotschedules_keywords):
            is_911 = True
    elif any(kw.lower() in full_text for kw in emergency_keywords):
        is_911 = True
    
    # Check for deadlines (Brinker/Allen Woods pattern)
    has_deadline = False
    if any(kw.lower() in sender_email.lower() for kw in ["brinker", "chilis"]):
        if any(kw.lower() in full_text for kw in deadline_keywords):
            has_deadline = True
    
    # Check for general action items
    has_action = any(kw.lower() in full_text for kw in action_keywords)
    
    # Extract dates
    dates_found = extract_dates_from_text(full_text)
    due_date = dates_found[0] if dates_found else None
    
    # Only create task if it matches our patterns
    if is_911 or has_deadline or has_action or due_date:
        
        # Determine task type and priority
        if is_911:
            task_type = "emergency"
            priority = "urgent"
            category = "coverage"
        elif has_deadline:
            task_type = "deadline"
            priority = "high" if due_date else "urgent"
            category = "deadline"
        else:
            task_type = "action"
            priority = "normal"
            category = "task"
        
        # Extract specific action
        action_desc = extract_enhanced_action(full_text, subject, is_911, has_deadline)
        
        task = {
            "thread_id": thread.get("id"),
            "type": task_type,
            "priority": priority,
            "category": category,
            "from": sender_name,
            "from_email": sender_email,
            "subject": subject,
            "action": action_desc,
            "due_date": due_date,
            "created_at": date_header,
            "snippet": snippet[:200],
            "is_911": is_911
        }
        
        tasks.append(task)
    
    return tasks

def extract_body_text(payload: Dict) -> str:
    """
    Extract text from email MIME payload
    """
    body = ""
    
    # Check if this is a multipart message
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    import base64
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif "parts" in part:
                # Recursively check nested parts
                body += extract_body_text(part)
    else:
        # Single part message
        if payload.get("mimeType", "").startswith("text"):
            data = payload.get("body", {}).get("data", "")
            if data:
                import base64
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    return body

def extract_enhanced_action(text: str, subject: str, is_911: bool, has_deadline: bool) -> str:
    """
    Extract action description with enhanced patterns
    """
    text_lower = text.lower()
    
    # 911/Emergency patterns
    if is_911:
        if "called off" in text_lower or "called out" in text_lower:
            # Try to extract who called off
            import re
            match = re.search(r"(\w+)\s+(called off|called out)", text_lower)
            if match:
                return f"🚨 Coverage needed: {match.group(1).title()} called off"
            return "🚨 Coverage needed: Call-off reported"
        elif "no-show" in text_lower or "no show" in text_lower:
            return "🚨 Coverage needed: No-show reported"
        elif "coverage needed" in text_lower:
            return "🚨 Coverage needed for shift"
        elif "left early" in text_lower:
            return "🚨 Partial coverage loss: Employee left early"
        else:
            return f"🚨 Emergency: {subject[:50]}"
    
    # Deadline patterns
    if has_deadline:
        if "schedule" in text_lower:
            if "manager" in text_lower or "mgr" in text_lower:
                # Extract period if mentioned
                import re
                period_match = re.search(r"p(\d+)|period\s*(\d+)", text_lower)
                if period_match:
                    period = period_match.group(1) or period_match.group(2)
                    return f"📅 Submit Manager Schedule (P{period})"
                return "📅 Submit Manager Schedule"
            return "📅 Schedule submission required"
        elif "report" in text_lower:
            if "labor" in text_lower:
                return "📅 Submit Labor Report"
            elif "variance" in text_lower:
                return "📅 Submit Variance Report"
            return "📅 Report submission required"
        elif "oracle" in text_lower or "fusion" in text_lower:
            return "📅 Oracle/Fusion task required"
        else:
            return f"📅 Deadline: {subject[:50]}"
    
    # General action patterns
    patterns = [
        (r"please\s+(.+?)[\.\?!]", "Action: {}"),
        (r"can you\s+(.+?)[\.\?!]", "Request: {}"),
        (r"need you to\s+(.+?)[\.\?!]", "Required: {}"),
        (r"follow up on\s+(.+?)[\.\?!]", "Follow up: {}"),
        (r"complete\s+(.+?)[\.\?!]", "Complete: {}"),
        (r"submit\s+(.+?)[\.\?!]", "Submit: {}"),
        (r"review\s+(.+?)[\.\?!]", "Review: {}"),
        (r"approve\s+(.+?)[\.\?!]", "Approve: {}"),
    ]
    
    for pattern, template in patterns:
        import re
        match = re.search(pattern, text_lower)
        if match:
            action = match.group(1).strip()
            # Clean up
            action = action.replace("\n", " ").replace("\r", "")
            if len(action) > 60:
                action = action[:57] + "..."
            return template.format(action)
    
    # Fallback
    return f"Action Required: {subject[:50]}"

def extract_action_description(text: str, subject: str) -> str:
    """
    Extract a clear action description from email text
    """
    text_lower = text.lower()
    
    # Pattern matching for common action requests
    patterns = [
        (r"please\s+(.+?)[\.\?!]", "Action: {}"),
        (r"can you\s+(.+?)[\.\?!]", "Request: {}"),
        (r"need you to\s+(.+?)[\.\?!]", "Required: {}"),
        (r"must\s+(.+?)[\.\?!]", "Must: {}"),
        (r"complete\s+(.+?)[\.\?!]", "Complete: {}"),
        (r"submit\s+(.+?)[\.\?!]", "Submit: {}"),
        (r"coverage needed for\s+(.+?)[\.\?!]", "Coverage needed: {}"),
        (r"called off\s+(.+?)[\.\?!]", "Call-off: {}"),
    ]
    
    for pattern, template in patterns:
        match = re.search(pattern, text_lower)
        if match:
            action = match.group(1).strip()
            # Clean up and truncate
            action = action.replace("\n", " ").replace("\r", "")
            if len(action) > 100:
                action = action[:97] + "..."
            return template.format(action)
    
    # Fallback to subject-based action
    if "schedule" in text_lower:
        return f"Review/Update: {subject[:50]}"
    elif "report" in text_lower:
        return f"Submit: {subject[:50]}"
    elif "coverage" in text_lower or "shift" in text_lower:
        return f"Handle: {subject[:50]}"
    else:
        return f"Action Required: {subject[:50]}"

def extract_dates_from_text(text: str) -> List[str]:
    """
    Extract dates from text, converting relative dates to absolute
    Returns list of ISO date strings
    """
    dates = []
    today = datetime.now()
    
    # Common patterns
    if "today" in text:
        dates.append(today.strftime("%Y-%m-%d"))
    if "tomorrow" in text:
        dates.append((today + timedelta(days=1)).strftime("%Y-%m-%d"))
    if "end of day" in text or "eod" in text or "by close" in text:
        dates.append(today.strftime("%Y-%m-%d"))
    
    # Day names
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if day in text:
            # Find next occurrence of this day
            days_ahead = (i - today.weekday()) % 7
            if days_ahead == 0:  # Today, assume next week
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            dates.append(target.strftime("%Y-%m-%d"))
    
    # Specific date patterns (MM/DD, MM-DD)
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})',  # MM/DD or MM-DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YY or MM/DD/YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                if len(match.groups()) == 2:
                    month, day = match.groups()
                    year = today.year
                    date = datetime(year, int(month), int(day))
                    if date < today:  # If date is past, assume next year
                        date = datetime(year + 1, int(month), int(day))
                    dates.append(date.strftime("%Y-%m-%d"))
            except:
                pass  # Invalid date
    
    return dates

def mark_task_complete(thread_id: str):
    """Mark a task/thread as complete"""
    state = load_task_state()
    if thread_id not in state["completed"]:
        state["completed"].append(thread_id)
    # Remove from dismissed if it was there
    if thread_id in state["dismissed"]:
        state["dismissed"].remove(thread_id)
    save_task_state(state)

def mark_task_dismissed(thread_id: str):
    """Mark a task/thread as not important/dismissed"""
    state = load_task_state()
    if thread_id not in state["dismissed"]:
        state["dismissed"].append(thread_id)
    # Remove from completed if it was there
    if thread_id in state["completed"]:
        state["completed"].remove(thread_id)
    save_task_state(state)

def mark_task_active(thread_id: str):
    """Reactivate a task (remove from both completed and dismissed)"""
    state = load_task_state()
    if thread_id in state["completed"]:
        state["completed"].remove(thread_id)
    if thread_id in state["dismissed"]:
        state["dismissed"].remove(thread_id)
    save_task_state(state)

def get_task_status(thread_id: str) -> str:
    """Get the status of a task"""
    state = load_task_state()
    if thread_id in state["completed"]:
        return "completed"
    elif thread_id in state["dismissed"]:
        return "dismissed"
    else:
        return "active"

def process_threads_to_tasks(threads: List[Dict]) -> List[Dict]:
    """
    Process email threads and extract actionable tasks
    """
    state = load_task_state()
    all_tasks = []
    
    for thread in threads:
        thread_id = thread.get("id")
        
        # Skip if already processed and completed/dismissed
        status = get_task_status(thread_id)
        
        # Extract action items from this thread
        tasks = extract_action_items(thread)
        
        for task in tasks:
            task["status"] = status
            task["thread_id"] = thread_id
            all_tasks.append(task)
        
        # Store extracted tasks in state
        if tasks:
            state["tasks"][thread_id] = tasks
    
    save_task_state(state)
    
    # Sort by priority and due date
    priority_order = {"urgent": 0, "high": 1, "normal": 2}
    all_tasks.sort(key=lambda x: (
        priority_order.get(x.get("priority", "normal"), 3),
        x.get("due_date") or "9999-12-31"
    ))
    
    return all_tasks

# Keep existing functions
from .priority_filter import (
    is_watched_sender,
    has_priority_keywords,
    calculate_priority_score,
    filter_threads,
    add_watched_sender,
    add_watched_domain,
    remove_watched_sender,
    remove_watched_domain
)
