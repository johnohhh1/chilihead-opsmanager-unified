#!/usr/bin/env python3
"""Start the FastAPI server with proper environment loading"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables FIRST, before any imports
load_dotenv()

# Now verify they're loaded
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ OpenAI API Key loaded: {api_key[:20]}...")
else:
    print("⚠️  Warning: No OpenAI API Key found!")

# Now import and run the app
import uvicorn
from app import app

if __name__ == "__main__":
    print("Starting OpenInbox server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
