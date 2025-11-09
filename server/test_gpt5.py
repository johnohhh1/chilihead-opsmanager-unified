"""
Test script for GPT-5 integration
Run this to verify GPT-5 models work correctly with chat/completions endpoint
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.model_provider import ModelProvider

async def test_gpt5():
    """Test GPT-5 with the chat/completions API"""
    
    print("=" * 70)
    print("Testing GPT-5 Integration (Chat Completions API)")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment!")
        print("   Make sure your .env file has OPENAI_API_KEY set.")
        return
    
    print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2? Answer in one short sentence."}
    ]
    
    # Test GPT-5 models
    gpt5_models = [
        ("gpt-5", "GPT-5 (Full)"),
        ("gpt-5-mini", "GPT-5 Mini"),
        ("gpt-5-nano", "GPT-5 Nano"),
    ]
    
    success_count = 0
    fail_count = 0
    
    for model_id, model_name in gpt5_models:
        print(f"📡 Testing {model_name} ({model_id})...")
        try:
            response = await ModelProvider.chat_completion(
                messages=messages,
                model=model_id,
                temperature=0.7,
                max_tokens=100
            )
            print(f"   ✅ SUCCESS!")
            print(f"   Response: {response}")
            print()
            success_count += 1
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            print()
            fail_count += 1
    
    # Test GPT-4 for comparison (should still work)
    print(f"📡 Testing GPT-4o (for comparison - uses max_tokens)...")
    try:
        response = await ModelProvider.chat_completion(
            messages=messages,
            model="gpt-4o",
            temperature=0.7,
            max_tokens=100
        )
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {response}")
        print()
        success_count += 1
    except Exception as e:
        print(f"   ❌ FAILED: {str(e)}")
        print()
        fail_count += 1
    
    print("=" * 70)
    print(f"Test Results: {success_count} passed, {fail_count} failed")
    print("=" * 70)
    
    if fail_count == 0:
        print()
        print("🎉 All tests passed! GPT-5 is working correctly.")
        print()
        print("Next steps:")
        print("  1. Restart your server: python run_server.py")
        print("  2. Select GPT-5 in the UI dropdown")
        print("  3. Try it out!")
    else:
        print()
        print("⚠️ Some tests failed. Common issues:")
        print()
        print("1. GPT-5 Access:")
        print("   - Make sure your OpenAI account has GPT-5 access")
        print("   - Check OpenAI dashboard for model availability")
        print()
        print("2. API Key:")
        print("   - Verify OPENAI_API_KEY in .env is correct")
        print("   - Check that the key has proper permissions")
        print()
        print("3. Rate Limits:")
        print("   - You may have hit OpenAI rate limits")
        print("   - Wait a moment and try again")

if __name__ == "__main__":
    asyncio.run(test_gpt5())
