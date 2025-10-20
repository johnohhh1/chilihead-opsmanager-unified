"""
Email filtering and prioritization service
Dynamically loads watched senders/domains from watch_config.json
"""

import json
import pathlib
from typing import List, Dict, Any
from datetime import datetime, timedelta

CONFIG_PATH = pathlib.Path(__file__).parent.parent / "watch_config.json"

def load_watch_config():
    """Load the watch configuration, with fallback defaults"""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config if file doesn't exist
        return {
            "priority_senders": [],
            "priority_domains": [],
            "keywords": [],
            "excluded_subjects": [],
            "auto_flag_as_important": True,
            "include_unread_only": False
        }

def save_watch_config(config: Dict):
    """Save updated configuration"""
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def is_watched_sender(email_from: str) -> bool:
    """Check if an email is from a watched sender or domain"""
    config = load_watch_config()
    email_from_lower = email_from.lower()
    
    # Check exact sender matches
    for sender in config.get("priority_senders", []):
        if sender.lower() in email_from_lower:
            return True
    
    # Check domain matches
    for domain in config.get("priority_domains", []):
        # Handle both @domain.com and domain.com formats
        domain_check = domain.lower()
        if not domain_check.startswith("@"):
            domain_check = "@" + domain_check
        if domain_check in email_from_lower:
            return True
    
    return False

def has_priority_keywords(subject: str, snippet: str) -> bool:
    """Check if email contains priority keywords"""
    config = load_watch_config()
    keywords = config.get("keywords", [])
    
    combined_text = f"{subject} {snippet}".lower()
    
    for keyword in keywords:
        if keyword.lower() in combined_text:
            return True
    
    return False

def is_excluded_subject(subject: str) -> bool:
    """Check if email subject matches any exclusion patterns"""
    if not subject:
        return False
        
    config = load_watch_config()
    exclusions = config.get("excluded_subjects", [])
    subject_lower = subject.lower()
    
    for pattern in exclusions:
        if pattern.lower() in subject_lower:
            return True
    
    return False

def calculate_priority_score(thread: Dict) -> int:
    """
    Calculate priority score for a thread
    Higher score = higher priority
    
    Scoring:
    - From watched sender: +50
    - Has priority keywords: +30
    - Unread: +20
    - Recent (last 24h): +15
    - Has deadline mentioned: +25
    """
    score = 0
    
    # Get thread metadata
    messages = thread.get("messages", [])
    if not messages:
        return score
    
    latest_msg = messages[-1]  # Most recent message
    headers = latest_msg.get("payload", {}).get("headers", [])
    
    # Extract sender
    from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
    if is_watched_sender(from_header):
        score += 50
    
    # Extract subject
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    snippet = thread.get("snippet", "")
    
    if has_priority_keywords(subject, snippet):
        score += 30
    
    # Check if unread
    label_ids = latest_msg.get("labelIds", [])
    if "UNREAD" in label_ids:
        score += 20
    
    # Check recency (if message has internalDate)
    internal_date = latest_msg.get("internalDate")
    if internal_date:
        msg_time = datetime.fromtimestamp(int(internal_date) / 1000)
        if datetime.now() - msg_time < timedelta(hours=24):
            score += 15
    
    # Check for deadline keywords
    deadline_keywords = ["deadline", "due", "by EOD", "by end of", "before", "must", "required by"]
    combined_lower = f"{subject} {snippet}".lower()
    if any(kw in combined_lower for kw in deadline_keywords):
        score += 25
    
    return score

def filter_threads(threads: List[Dict], filter_watched_only: bool = False) -> List[Dict]:
    """
    Filter and prioritize threads based on configuration
    
    Args:
        threads: List of Gmail thread objects
        filter_watched_only: If True, only return threads from watched senders
    
    Returns:
        List of threads, sorted by priority score
    """
    config = load_watch_config()
    
    # Filter by watched senders if requested
    if filter_watched_only or config.get("auto_flag_as_important", False):
        filtered = []
        for thread in threads:
            messages = thread.get("messages", [])
            if messages:
                latest_msg = messages[-1]
                headers = latest_msg.get("payload", {}).get("headers", [])
                from_header = next((h["value"] for h in headers if h["name"].lower() == "from"), "")
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
                
                # Skip excluded subjects
                if is_excluded_subject(subject):
                    continue
                
                if is_watched_sender(from_header):
                    # Add priority score to thread object
                    thread["priority_score"] = calculate_priority_score(thread)
                    filtered.append(thread)
                elif not filter_watched_only:
                    # Include but with lower priority
                    thread["priority_score"] = calculate_priority_score(thread)
                    filtered.append(thread)
        threads = filtered
    else:
        # Calculate priority scores for all threads and filter exclusions
        filtered = []
        for thread in threads:
            messages = thread.get("messages", [])
            if messages:
                latest_msg = messages[-1]
                headers = latest_msg.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
                
                # Skip excluded subjects
                if is_excluded_subject(subject):
                    continue
                    
                thread["priority_score"] = calculate_priority_score(thread)
                filtered.append(thread)
        threads = filtered
    
    # Sort by priority score (highest first)
    threads.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    
    return threads

def add_watched_sender(email: str):
    """Add a new sender to watch list"""
    config = load_watch_config()
    if email not in config["priority_senders"]:
        config["priority_senders"].append(email)
        save_watch_config(config)
        return True
    return False

def add_watched_domain(domain: str):
    """Add a new domain to watch list"""
    config = load_watch_config()
    if domain not in config["priority_domains"]:
        config["priority_domains"].append(domain)
        save_watch_config(config)
        return True
    return False

def remove_watched_sender(email: str):
    """Remove a sender from watch list"""
    config = load_watch_config()
    if email in config["priority_senders"]:
        config["priority_senders"].remove(email)
        save_watch_config(config)
        return True
    return False

def remove_watched_domain(domain: str):
    """Remove a domain from watch list"""
    config = load_watch_config()
    if domain in config["priority_domains"]:
        config["priority_domains"].remove(domain)
        save_watch_config(config)
        return True
    return False

def add_excluded_subject(pattern: str):
    """Add a new subject exclusion pattern"""
    config = load_watch_config()
    if "excluded_subjects" not in config:
        config["excluded_subjects"] = []
    if pattern not in config["excluded_subjects"]:
        config["excluded_subjects"].append(pattern)
        save_watch_config(config)
        return True
    return False

def remove_excluded_subject(pattern: str):
    """Remove a subject exclusion pattern"""
    config = load_watch_config()
    if "excluded_subjects" in config and pattern in config["excluded_subjects"]:
        config["excluded_subjects"].remove(pattern)
        save_watch_config(config)
        return True
    return False
