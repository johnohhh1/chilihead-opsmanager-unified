#!/usr/bin/env python3
"""
Show detailed view of Chili's/Brinker emails with priority scores
"""

import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def show_restaurant_emails():
    print("\n🍔 CHILI'S/BRINKER EMAIL TRACKER")
    print("=" * 70)
    
    # Get watched emails only
    response = httpx.get(f"{BASE_URL}/threads?watched_only=true&max_results=20")
    data = response.json()
    
    print(f"\n📧 Found {data['total_filtered']} emails from watched senders:")
    print("-" * 70)
    
    if not data["threads"]:
        print("No emails from watched senders found.")
        return
    
    for i, thread in enumerate(data["threads"], 1):
        # Parse sender
        from_email = thread["from"]
        if "<" in from_email and ">" in from_email:
            sender_name = from_email.split("<")[0].strip()
            sender_email = from_email.split("<")[1].replace(">", "").strip()
        else:
            sender_name = ""
            sender_email = from_email
        
        # Check for important indicators
        is_unread = "UNREAD" in thread.get("labels", [])
        priority = thread.get("priority_score", 0)
        
        # Priority indicator
        if priority >= 75:
            priority_icon = "🔴"  # High priority
        elif priority >= 50:
            priority_icon = "🟡"  # Medium priority  
        else:
            priority_icon = "⚪"  # Low priority
        
        print(f"\n{i}. {priority_icon} Priority Score: {priority}")
        print(f"   From: {sender_name if sender_name else sender_email}")
        if sender_name:
            print(f"   Email: {sender_email}")
        print(f"   Subject: {thread['subject']}")
        if thread.get("snippet"):
            print(f"   Preview: {thread['snippet'][:100]}...")
        if is_unread:
            print(f"   ⚠️  STATUS: UNREAD")
        print(f"   Thread ID: {thread['id']}")
    
    print("\n" + "=" * 70)
    print("\n📌 QUICK ACTIONS:")
    print("   - Summarize an email: POST /summarize with thread_id")
    print("   - Add sender: POST /watch-config/add-sender?email=...")
    print("   - Add domain: POST /watch-config/add-domain?domain=...")
    
    # Show all emails with priority
    print("\n\n🎯 ALL EMAILS BY PRIORITY:")
    print("-" * 70)
    
    response = httpx.get(f"{BASE_URL}/threads?priority_sort=true&max_results=10")
    data = response.json()
    
    for thread in data["threads"][:5]:
        score = thread.get("priority_score", 0)
        from_short = thread["from"].split("<")[0].strip() if "<" in thread["from"] else thread["from"][:30]
        subject_short = thread["subject"][:50] if thread["subject"] else "No subject"
        
        # Highlight if it's from watched sender
        if score >= 50:
            print(f"⭐ Score {score:3d}: {from_short[:30]:30s} | {subject_short}")
        else:
            print(f"   Score {score:3d}: {from_short[:30]:30s} | {subject_short}")

if __name__ == "__main__":
    show_restaurant_emails()
