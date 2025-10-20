from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
import os, json, pathlib, time
from urllib.parse import urlencode
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

router = APIRouter()

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tokens"
TOKENS_DIR.mkdir(exist_ok=True)

def _client_config():
    cid = os.getenv("GOOGLE_CLIENT_ID")
    csecret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect = os.getenv("GOOGLE_REDIRECT_URI")
    if not cid or not csecret or not redirect:
        raise HTTPException(500, "Google OAuth env vars missing")
    return {
        "web": {
            "client_id": cid,
            "project_id": "openinbox-dev",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": csecret,
            "redirect_uris": [redirect],
        }
    }

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

@router.get("/auth/url")
def auth_url():
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    auth_uri, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return {"auth_url": auth_uri}

@router.get("/auth/callback")
def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("<h3>No code provided</h3>", status_code=400)
    
    try:
        flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
        flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        # Fetch token with authorization response URL to handle scope changes
        flow.fetch_token(code=code)
        creds = flow.credentials
    except Exception as e:
        print(f"OAuth error: {e}")
        # If there's a scope mismatch warning, we can still proceed
        if "Scope has changed" in str(e):
            # Re-initialize flow and try again without strict scope checking
            flow = Flow.from_client_config(_client_config(), scopes=None)
            flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
            flow.fetch_token(code=code)
            creds = flow.credentials
        else:
            raise HTTPException(500, f"OAuth error: {str(e)}")

    # In a real app, associate with the signed-in user.
    token_path = TOKENS_DIR / "user_dev.json"
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    return HTMLResponse("<h3>Auth complete. You can close this tab.</h3>")
