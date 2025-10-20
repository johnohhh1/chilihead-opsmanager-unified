#!/usr/bin/env python3
"""Test OpenAI API key directly"""

import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")

print(f"API Key found: {'Yes' if OPENAI_API_KEY else 'No'}")
print(f"API Key prefix: {OPENAI_API_KEY[:20] if OPENAI_API_KEY else 'N/A'}...")
print(f"Model: {OPENAI_MODEL}")
print(f"Project ID: {OPENAI_PROJECT_ID}")
print(f"Base URL: {OPENAI_BASE_URL}")

if not OPENAI_API_KEY:
    print("\n❌ No API key found in environment!")
    exit(1)

# Test the API
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

if OPENAI_PROJECT_ID:
    headers["OpenAI-Project"] = OPENAI_PROJECT_ID

payload = {
    "model": OPENAI_MODEL,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'API test successful' in 5 words or less."}
    ],
    "temperature": 0.2,
    "max_tokens": 50
}

print("\n🔄 Testing OpenAI API...")

try:
    with httpx.Client(base_url=OPENAI_BASE_URL, timeout=30) as client:
        response = client.post("/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
    result = data["choices"][0]["message"]["content"].strip()
    print(f"✅ Success! Response: {result}")
    
except httpx.HTTPStatusError as e:
    print(f"❌ HTTP Error {e.response.status_code}")
    print(f"Response: {e.response.text}")
    if e.response.status_code == 401:
        print("\n⚠️  This usually means your API key is invalid or expired.")
        print("   Please check your OpenAI dashboard and generate a new key if needed.")
    elif e.response.status_code == 429:
        print("\n⚠️  Rate limit or quota exceeded. Check your OpenAI account.")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
