from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pathlib, json

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tokens"

def get_service():
    token_path = TOKENS_DIR / "user_dev.json"
    with open(token_path, "r") as f:
        data = json.load(f)
    creds = Credentials.from_authorized_user_info(data)
    return build("gmail", "v1", credentials=creds, cache_discovery=False)

def get_thread_messages(thread_id: str):
    svc = get_service()
    tdata = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
    return tdata.get("messages", [])

def get_user_threads(max_results: int = 50, query: str = None):
    """Get threads from Gmail with optional query"""
    svc = get_service()
    
    params = {
        "userId": "me",
        "maxResults": max_results
    }
    
    if query:
        params["q"] = query
    
    result = svc.users().threads().list(**params).execute()
    thread_ids = result.get("threads", [])
    
    # Fetch full thread data
    threads = []
    for thread_info in thread_ids:
        thread_id = thread_info["id"]
        thread_data = svc.users().threads().get(userId="me", id=thread_id, format="full").execute()
        threads.append(thread_data)
    
    return threads
