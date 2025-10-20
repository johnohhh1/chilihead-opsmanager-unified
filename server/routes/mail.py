from fastapi import APIRouter, HTTPException, Query
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pathlib, json
from typing import Optional

try:
    # Try relative import first (when run as module)
    from ..services.priority_filter import (
        filter_threads, 
        load_watch_config, 
        save_watch_config,
        add_watched_sender,
        add_watched_domain,
        remove_watched_sender,
        remove_watched_domain,
        add_excluded_subject,
        remove_excluded_subject
    )
    from ..services.task_extractor import (
        process_threads_to_tasks,
        mark_task_complete,
        mark_task_dismissed,
        mark_task_active,
        get_task_status,
        extract_action_items
    )
    from ..services.state_manager import state_manager
except ImportError:
    # Fall back to adding to sys.path (when run directly)
    import sys
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from services.priority_filter import (
        filter_threads, 
        load_watch_config, 
        save_watch_config,
        add_watched_sender,
        add_watched_domain,
        remove_watched_sender,
        remove_watched_domain,
        add_excluded_subject,
        remove_excluded_subject
    )
    from services.task_extractor import (
        process_threads_to_tasks,
        mark_task_complete,
        mark_task_dismissed,
        mark_task_active,
        get_task_status,
        extract_action_items
    )
    from services.state_manager import state_manager

router = APIRouter()

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tokens"

def _creds():
    token_path = TOKENS_DIR / "user_dev.json"
    if not token_path.exists():
        raise HTTPException(401, "Not authenticated. Hit /auth/url first.")
    with open(token_path, "r") as f:
        data = json.load(f)
    return Credentials.from_authorized_user_info(data)

@router.get("/profile")
def profile():
    creds = _creds()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    me = service.users().getProfile(userId="me").execute()
    return me

@router.get("/watch-config")
def get_watch_config():
    """Get current watch configuration"""
    return load_watch_config()

@router.post("/watch-config/add-sender")
def add_sender(email: str):
    """Add a sender to watch list"""
    success = add_watched_sender(email)
    return {
        "success": success,
        "message": f"Added {email} to watch list" if success else f"{email} already in watch list",
        "config": load_watch_config()
    }

@router.post("/watch-config/add-domain")
def add_domain(domain: str):
    """Add a domain to watch list"""
    success = add_watched_domain(domain)
    return {
        "success": success,
        "message": f"Added {domain} to watch list" if success else f"{domain} already in watch list",
        "config": load_watch_config()
    }

@router.delete("/watch-config/remove-sender")
def remove_sender(email: str):
    """Remove a sender from watch list"""
    success = remove_watched_sender(email)
    return {
        "success": success,
        "message": f"Removed {email} from watch list" if success else f"{email} not in watch list",
        "config": load_watch_config()
    }

@router.delete("/watch-config/remove-domain")
def remove_domain(domain: str):
    """Remove a domain from watch list"""
    success = remove_watched_domain(domain)
    return {
        "success": success,
        "message": f"Removed {domain} from watch list" if success else f"{domain} not in watch list",
        "config": load_watch_config()
    }

@router.post("/watch-config/add-exclusion")
def add_exclusion(pattern: str):
    """Add a subject exclusion pattern"""
    success = add_excluded_subject(pattern)
    return {
        "success": success,
        "message": f"Added exclusion '{pattern}'" if success else f"'{pattern}' already excluded",
        "config": load_watch_config()
    }

@router.delete("/watch-config/remove-exclusion")
def remove_exclusion(pattern: str):
    """Remove a subject exclusion pattern"""
    success = remove_excluded_subject(pattern)
    return {
        "success": success,
        "message": f"Removed exclusion '{pattern}'" if success else f"'{pattern}' not in exclusions",
        "config": load_watch_config()
    }

@router.get("/threads")
def threads(
    max_results: int = Query(10, ge=1, le=100),
    watched_only: bool = Query(False, description="Only show emails from watched senders"),
    priority_sort: bool = Query(True, description="Sort by priority score"),
    time_range: str = Query("today", description="Time filter: today, yesterday, week, month, all")
):
    creds = _creds()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    # Build Gmail query with date filter
    query_parts = []
    
    # Add watched sender filters if requested
    if watched_only:
        config = load_watch_config()
        sender_parts = []
        for sender in config.get("priority_senders", []):
            sender_parts.append(f"from:{sender}")
        for domain in config.get("priority_domains", []):
            sender_parts.append(f"from:*@{domain}")
        
        if sender_parts:
            query_parts.append(f"({' OR '.join(sender_parts)})")
    
    # Add time filter
    if time_range == "today":
        query_parts.append("newer_than:1d")
    elif time_range == "yesterday":
        query_parts.append("newer_than:2d older_than:1d")
    elif time_range == "week":
        query_parts.append("newer_than:7d")
    elif time_range == "month":
        query_parts.append("newer_than:30d")
    # 'all' means no time filter
    
    gmail_query = " ".join(query_parts) if query_parts else None
    
    # Fetch more emails to account for filtering - increase from 60 to 200
    fetch_params = {
        "userId": "me",
        "maxResults": min(200, max_results * 10)  # Fetch 10x more for filtering
    }
    if gmail_query:
        fetch_params["q"] = gmail_query
    
    res = service.users().threads().list(**fetch_params).execute()
    
    threads = []
    for t in res.get("threads", []):
        tdata = service.users().threads().get(userId="me", id=t["id"], format="full").execute()
        threads.append(tdata)
    
    # Apply filtering and prioritization
    if priority_sort or watched_only:
        threads = filter_threads(threads, filter_watched_only=watched_only)
    
    # Convert to lightweight format for response and include state
    formatted_threads = []
    for tdata in threads[:max_results]:  # Limit to requested count
        if tdata.get("messages"):
            headers = {h["name"].lower(): h["value"] 
                      for h in tdata["messages"][0].get("payload", {}).get("headers", [])}
            thread_id = tdata["id"]
            
            # Get state for this email
            email_state = state_manager.get_email_state(thread_id)
            
            formatted_threads.append({
                "id": thread_id,
                "snippet": tdata.get("snippet"),
                "subject": headers.get("subject"),
                "from": headers.get("from"),
                "to": headers.get("to"),
                "date": headers.get("date"),
                "priority_score": tdata.get("priority_score", 0),
                "historyId": tdata.get("historyId"),
                "messageCount": len(tdata.get("messages", [])),
                "labels": tdata.get("messages", [{}])[0].get("labelIds", []),
                "state": email_state  # Include state
            })
    
    return {
        "threads": formatted_threads,
        "total_filtered": len(threads),
        "total_fetched": len(res.get("threads", [])),
        "query_used": gmail_query,
        "watch_config": load_watch_config()
    }

@router.get("/tasks")
def get_tasks(
    include_completed: bool = Query(False, description="Include completed tasks"),
    include_dismissed: bool = Query(False, description="Include dismissed tasks"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    time_window: Optional[str] = Query(None, description="Preset: today, yesterday, week, month")
):
    """Get actionable tasks extracted from emails"""
    creds = _creds()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    # Build Gmail query based on date filters
    gmail_query_parts = []
    
    # Add sender filters
    config = load_watch_config()
    sender_parts = []
    for sender in config.get("priority_senders", []):
        sender_parts.append(f"from:{sender}")
    for domain in config.get("priority_domains", []):
        sender_parts.append(f"from:{domain}")
    
    if sender_parts:
        gmail_query_parts.append(f"({' OR '.join(sender_parts)})")
    
    # Add date filters
    if time_window:
        if time_window == "today":
            gmail_query_parts.append("newer_than:1d")
        elif time_window == "yesterday":
            gmail_query_parts.append("newer_than:2d older_than:1d")
        elif time_window == "week":
            gmail_query_parts.append("newer_than:7d")
        elif time_window == "month":
            gmail_query_parts.append("newer_than:30d")
    elif date_from or date_to:
        if date_from:
            gmail_query_parts.append(f"after:{date_from}")
        if date_to:
            gmail_query_parts.append(f"before:{date_to}")
    else:
        # Default: last 7 days for better coverage
        gmail_query_parts.append("newer_than:7d")
    
    gmail_query = " ".join(gmail_query_parts) if gmail_query_parts else None
    
    # Get threads with query
    res = service.users().threads().list(
        userId="me", 
        maxResults=100,
        q=gmail_query
    ).execute()
    
    threads = []
    for t in res.get("threads", []):
        tdata = service.users().threads().get(userId="me", id=t["id"], format="full").execute()
        threads.append(tdata)
    
    # Process threads to extract tasks
    tasks = process_threads_to_tasks(threads)
    
    # Filter based on status
    if not include_completed:
        tasks = [t for t in tasks if t.get("status") != "completed"]
    if not include_dismissed:
        tasks = [t for t in tasks if t.get("status") != "dismissed"]
    
    return {
        "tasks": tasks,
        "total": len(tasks),
        "query_used": gmail_query,
        "threads_found": len(threads),
        "stats": {
            "urgent": len([t for t in tasks if t.get("priority") == "urgent"]),
            "high": len([t for t in tasks if t.get("priority") == "high"]),
            "normal": len([t for t in tasks if t.get("priority") == "normal"]),
            "completed": len([t for t in tasks if t.get("status") == "completed"]),
            "dismissed": len([t for t in tasks if t.get("status") == "dismissed"])
        }
    }

@router.post("/tasks/{thread_id}/complete")
def complete_task(thread_id: str):
    """Mark a task as complete"""
    mark_task_complete(thread_id)
    return {"success": True, "message": "Task marked as complete"}

@router.post("/tasks/{thread_id}/dismiss")
def dismiss_task(thread_id: str):
    """Mark a task as not important/dismissed"""
    mark_task_dismissed(thread_id)
    return {"success": True, "message": "Task dismissed"}

@router.post("/tasks/{thread_id}/reactivate")
def reactivate_task(thread_id: str):
    """Reactivate a completed or dismissed task"""
    mark_task_active(thread_id)
    return {"success": True, "message": "Task reactivated"}
