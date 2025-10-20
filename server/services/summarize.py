import os
import httpx
from dotenv import load_dotenv
from .gmail import get_thread_messages

# Load environment variables first
load_dotenv()

def get_openai_config():
    """Get OpenAI configuration, loading from environment each time"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "project_id": os.getenv("OPENAI_PROJECT_ID"),
        "org_id": os.getenv("OPENAI_ORG_ID")
    }


# === MAIN SUMMARIZER FUNCTION ===
def summarize_thread(thread_id: str) -> str:
    """
    Pulls the last few Gmail messages in a thread, concatenates the snippets,
    and summarizes them into a 5-bullet digest + one-line Next: action.
    """

    # -- Gather latest messages from Gmail --
    msgs = get_thread_messages(thread_id)
    excerpts = []

    for m in msgs[-5:]:  # take last few messages
        snippet = m.get("snippet", "")
        if snippet:
            excerpts.append(snippet)

    content = "\n\n".join(excerpts)[:6000] or "No content found."
    prompt = f"""You are an email triage assistant. Summarize the thread below in 5 bullet points.
Include the sender(s), the main ask, and any deadlines.
End with a one-line next action prefixed 'Next:'.
---
{content}
"""

    # Get fresh config
    config = get_openai_config()
    
    # -- No key loaded --
    if not config["api_key"]:
        return "[No OPENAI_API_KEY configured] " + prompt[:280]
    
    # Debug: Log that we have a key (without exposing it)
    print(f"OpenAI API Key loaded: {config['api_key'][:20]}...")

    # === BUILD HEADERS ===
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    # Support project-scoped & org-scoped keys
    if config["project_id"]:
        headers["OpenAI-Project"] = config["project_id"]
    if config["org_id"]:
        headers["OpenAI-Organization"] = config["org_id"]

    # === PAYLOAD ===
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "system",
                "content": "You are a precise, concise email triage assistant that never hallucinates."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
    }

    # === MAKE REQUEST ===
    try:
        with httpx.Client(base_url=config["base_url"], timeout=60) as client:
            response = client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        return f"[HTTP Error] {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"[Request Error] {str(e)}"

    # === PARSE RESULT ===
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return f"[Parse Error] Raw data: {data}"
