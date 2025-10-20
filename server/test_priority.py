#!/usr/bin/env python3
"""
Test the priority filtering system for restaurant emails
"""

import httpx
import json

BASE_URL = "http://localhost:8000"

def test_watch_config():
    """Test the watch configuration endpoints"""
    
    print("🔍 Testing Watch Configuration System")
    print("=" * 50)
    
    # Get current config
    print("\n📋 Current watch configuration:")
    response = httpx.get(f"{BASE_URL}/watch-config")
    config = response.json()
    print(json.dumps(config, indent=2))
    
    print("\n" + "=" * 50)
    
    # Test getting threads with different filters
    print("\n📧 Testing different thread filters:")
    
    # 1. All threads (no filter)
    print("\n1️⃣  All threads (priority sorted):")
    response = httpx.get(f"{BASE_URL}/threads?max_results=5&priority_sort=true&watched_only=false")
    data = response.json()
    print(f"   Found {data['total_filtered']} threads")
    for thread in data["threads"][:3]:
        print(f"   📌 Score {thread['priority_score']:3d}: {thread['from'][:40]}")
        print(f"      Subject: {thread['subject'][:60]}")
    
    # 2. Only watched senders
    print("\n2️⃣  Only watched senders (Chili's/Brinker):")
    response = httpx.get(f"{BASE_URL}/threads?max_results=10&watched_only=true")
    data = response.json()
    print(f"   Found {data['total_filtered']} threads from watched senders")
    for thread in data["threads"]:
        print(f"   🔴 Score {thread['priority_score']:3d}: {thread['from'][:50]}")
        print(f"      Subject: {thread['subject'][:60]}")
        if "UNREAD" in thread.get("labels", []):
            print(f"      ⚠️  UNREAD")
    
    print("\n" + "=" * 50)
    print("\n✅ Quick API reference:")
    print("""
    GET  /threads?watched_only=true     - Only Chili's/Brinker emails
    GET  /threads?priority_sort=true    - All emails, sorted by importance
    GET  /watch-config                   - See current watch list
    
    POST /watch-config/add-sender?email=manager@chilis.com
    POST /watch-config/add-domain?domain=@hotschedules.com
    
    DELETE /watch-config/remove-sender?email=someone@example.com
    DELETE /watch-config/remove-domain?domain=@example.com
    """)

if __name__ == "__main__":
    test_watch_config()
