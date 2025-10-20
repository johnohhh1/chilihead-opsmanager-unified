#!/usr/bin/env python3
"""
Debug script to test task extraction
"""

import httpx
import json

BASE_URL = "http://localhost:8000"

print("🔍 Debugging Task Extraction")
print("=" * 60)

# First, let's see what threads we're getting
print("\n1️⃣ Checking raw threads from watched senders:")
response = httpx.get(f"{BASE_URL}/threads?watched_only=true&max_results=10")
if response.status_code == 200:
    data = response.json()
    print(f"   Found {len(data['threads'])} threads")
    for i, thread in enumerate(data['threads'][:3], 1):
        print(f"\n   Thread {i}:")
        print(f"   From: {thread.get('from', 'Unknown')[:50]}")
        print(f"   Subject: {thread.get('subject', 'No subject')[:50]}")
        print(f"   Snippet: {thread.get('snippet', '')[:100]}")
        print(f"   Priority Score: {thread.get('priority_score', 0)}")
else:
    print(f"   Error: {response.status_code}")

print("\n" + "=" * 60)

# Now check what tasks are being extracted
print("\n2️⃣ Checking extracted tasks:")
response = httpx.get(f"{BASE_URL}/tasks")
if response.status_code == 200:
    data = response.json()
    print(f"   Total tasks found: {data['total']}")
    print(f"   Stats: {json.dumps(data['stats'], indent=2)}")
    
    if data['tasks']:
        for task in data['tasks'][:3]:
            print(f"\n   Task:")
            print(f"   Action: {task.get('action', 'No action')}")
            print(f"   From: {task.get('from', 'Unknown')}")
            print(f"   Priority: {task.get('priority', 'normal')}")
            print(f"   Status: {task.get('status', 'active')}")
    else:
        print("\n   ❌ No tasks were extracted!")
        print("\n   Possible reasons:")
        print("   - Email content doesn't match action keywords")
        print("   - Task extractor needs tuning")
        print("   - Emails are being filtered out")
else:
    print(f"   Error: {response.status_code}")
    print(f"   Response: {response.text}")

print("\n" + "=" * 60)

# Check the watch config
print("\n3️⃣ Current watch configuration:")
response = httpx.get(f"{BASE_URL}/watch-config")
if response.status_code == 200:
    config = response.json()
    print(f"   Watched senders: {config.get('priority_senders', [])}")
    print(f"   Watched domains: {config.get('priority_domains', [])}")
    print(f"   Action keywords: {len(config.get('keywords', []))} configured")
else:
    print(f"   Error: {response.status_code}")

print("\n" + "=" * 60)
print("\n💡 If no tasks are showing, we may need to:")
print("   1. Adjust the action keyword detection")
print("   2. Check if emails are in full format vs snippets")
print("   3. Add more specific patterns for your restaurant emails")
