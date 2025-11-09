# 🔐 ChiliHead OpsManager - OAuth Scopes Documentation

## Current OAuth Scopes (Google)

Your app currently requests **7 Google OAuth scopes** for Gmail, Calendar, Tasks, and user profile access.

---

## 📋 COMPLETE SCOPE LIST

### 1. **Gmail - Read Access**
```
https://www.googleapis.com/auth/gmail.readonly
```
**What it does:**
- Read emails from Gmail
- Access message content, headers, attachments
- Read thread information
- Query/search emails

**Used for:**
- ✅ Email triage and analysis
- ✅ Reading RAP Mobile reports
- ✅ Smart assistant email processing
- ✅ Daily digest generation
- ✅ Priority email detection

**Does NOT allow:**
- ❌ Sending emails
- ❌ Deleting emails
- ❌ Modifying labels permanently

---

### 2. **Gmail - Modify Access**
```
https://www.googleapis.com/auth/gmail.modify
```
**What it does:**
- Add/remove labels
- Mark as read/unread
- Archive emails
- Star/unstar messages
- Modify thread state

**Used for:**
- ✅ Marking emails as acknowledged
- ✅ Auto-labeling emails (urgent, processed, etc.)
- ✅ Organizing inbox automatically
- ✅ Email state tracking

**Does NOT allow:**
- ❌ Sending emails (requires separate scope)
- ❌ Permanently deleting emails

---

### 3. **Google Calendar - Events**
```
https://www.googleapis.com/auth/calendar.events
```
**What it does:**
- Create calendar events
- Read calendar events
- Update calendar events
- Delete calendar events

**Used for:**
- ✅ Creating events from email deadlines
- ✅ "P5 Manager Schedule due Friday 5pm" → Calendar event
- ✅ Meeting reminders
- ✅ Deadline tracking in calendar
- ✅ Viewing upcoming events in dashboard

**Permissions:**
- ✅ Full read/write access to calendar events
- ✅ Can see all your calendar events
- ✅ Can create/modify/delete events

---

### 4. **Google Tasks**
```
https://www.googleapis.com/auth/tasks
```
**What it does:**
- Create tasks in Google Tasks
- Read task lists
- Update task status
- Delete tasks

**Used for:**
- ✅ Creating tasks from email action items
- ✅ Syncing ChiliHead tasks to Google Tasks
- ✅ "Call payroll about Hannah" → Google Task
- ✅ Task completion tracking
- ✅ Mobile task access (via Google Tasks app)

**Permissions:**
- ✅ Full read/write access to all task lists
- ✅ Can create/modify/delete tasks

---

### 5. **User Email Address**
```
https://www.googleapis.com/auth/userinfo.email
```
**What it does:**
- Read your email address
- Identify which Google account is authenticated

**Used for:**
- ✅ Displaying your email in the app
- ✅ Identifying the authenticated user
- ✅ Logging/audit trail

---

### 6. **User Profile**
```
https://www.googleapis.com/auth/userinfo.profile
```
**What it does:**
- Read your basic profile info (name, picture)
- Public Google account information

**Used for:**
- ✅ Displaying your name in the UI
- ✅ Profile picture in header
- ✅ Personalized greetings

---

### 7. **OpenID**
```
openid
```
**What it does:**
- Standard OAuth authentication
- Allows the app to verify your identity

**Used for:**
- ✅ Secure authentication
- ✅ Session management
- ✅ OAuth flow completion

---

## 🎯 SCOPE USAGE BY FEATURE

### Email Intelligence Features:
| Feature | Scopes Needed |
|---------|---------------|
| **Email Reading** | `gmail.readonly` |
| **Email Triage** | `gmail.readonly`, `gmail.modify` |
| **RAP Mobile Image Analysis** | `gmail.readonly` |
| **Smart Assistant** | `gmail.readonly` |
| **Daily Digest** | `gmail.readonly` |
| **Mark as Acknowledged** | `gmail.modify` |

### Task Management Features:
| Feature | Scopes Needed |
|---------|---------------|
| **Create Task from Email** | `tasks` |
| **Sync to Google Tasks** | `tasks` |
| **View Tasks** | `tasks` |
| **Complete Tasks** | `tasks` |

### Calendar Features:
| Feature | Scopes Needed |
|---------|---------------|
| **Create Event from Deadline** | `calendar.events` |
| **View Upcoming Events** | `calendar.events` |
| **Deadline Reminders** | `calendar.events` |

### User Identity:
| Feature | Scopes Needed |
|---------|---------------|
| **Login/Authentication** | `openid`, `userinfo.email` |
| **Profile Display** | `userinfo.profile` |

---

## 🔒 SECURITY & PRIVACY

### What Your App CAN Do:
- ✅ Read your Gmail emails
- ✅ Label/organize emails
- ✅ Create calendar events
- ✅ Create Google Tasks
- ✅ See your name and email

### What Your App CANNOT Do:
- ❌ Send emails on your behalf
- ❌ Permanently delete emails
- ❌ Access other people's Gmail
- ❌ Share your data with third parties
- ❌ Access Google Drive, Contacts, Photos, etc.

### Data Storage:
- **Email content**: Only metadata stored (subject, sender, dates)
- **Full content**: Never stored, only analyzed via API
- **Tokens**: Stored locally in `/server/tokens/user_dev.json`
- **Database**: Only task data and email state (read/unread)

---

## 🛠️ SCOPE MANAGEMENT

### Check Current Scopes:
```bash
# API endpoint
GET http://localhost:8000/auth/scopes

# Response shows:
{
  "authenticated": true,
  "granted_scopes": [...],
  "missing_scopes": [...],
  "needs_reauth": false
}
```

### Re-authenticate (Add More Scopes):
```bash
# If you add new scopes to the code, users need to re-auth
GET http://localhost:8000/auth/url

# Visit the URL, grant permissions
# Callback will save new token with updated scopes
```

### Revoke Access:
```
1. Go to: https://myaccount.google.com/permissions
2. Find "ChiliHead OpsManager" 
3. Click "Remove Access"
4. Delete /server/tokens/user_dev.json
```

---

## 📊 SCOPE COMPARISON

### What We Use vs Other Apps:

| App Type | Typical Scopes |
|----------|----------------|
| **Email Client** | `gmail.readonly`, `gmail.send`, `gmail.modify` |
| **ChiliHead OpsManager** | `gmail.readonly`, `gmail.modify` |
| **Calendar App** | `calendar` (full access) |
| **ChiliHead OpsManager** | `calendar.events` (events only) |
| **Task Manager** | `tasks` |
| **ChiliHead OpsManager** | `tasks` |

**We request MINIMAL scopes needed** - not full access to everything.

---

## 🚀 POTENTIAL FUTURE SCOPES

### Not Currently Requested (But Could Add):

#### Gmail Send:
```
https://www.googleapis.com/auth/gmail.send
```
**Use case:** Auto-respond to emails, send delegation reminders

#### Google Drive:
```
https://www.googleapis.com/auth/drive.file
```
**Use case:** Store reports, export data to Drive

#### Google Contacts:
```
https://www.googleapis.com/auth/contacts.readonly
```
**Use case:** Auto-complete manager names, team directory

#### Gmail Compose:
```
https://www.googleapis.com/auth/gmail.compose
```
**Use case:** Draft emails (doesn't send, just creates drafts)

#### Calendar Settings:
```
https://www.googleapis.com/auth/calendar.settings.readonly
```
**Use case:** Detect work hours, timezone preferences

---

## 🎯 MINIMAL SCOPE PRINCIPLE

### Why We Don't Request Everything:

1. **Security**: Fewer permissions = less risk if token leaked
2. **User Trust**: Users more likely to grant limited access
3. **Compliance**: Easier to audit and comply with privacy laws
4. **Maintenance**: Fewer APIs to maintain and test

### Scope Expansion Decision Tree:
```
New Feature Idea
    ↓
Does it REQUIRE new scope?
    ↓
    YES → Is it ESSENTIAL to core functionality?
        ↓
        YES → Document why, add scope, update docs
        ↓
        NO → Find alternative without new scope
    ↓
    NO → Implement with existing scopes
```

---

## 📝 DEVELOPER NOTES

### Adding a New Scope:

1. **Update `/server/routes/oauth.py`:**
```python
SCOPES = [
    # ... existing scopes ...
    "https://www.googleapis.com/auth/NEW_SCOPE",  # Add here
]
```

2. **Update this documentation** with:
   - What the scope does
   - Why it's needed
   - What features use it

3. **Test re-authentication:**
```bash
# Delete old token
rm server/tokens/user_dev.json

# Get new auth URL
curl http://localhost:8000/auth/url

# Complete OAuth flow
```

4. **Update Google Cloud Console:**
   - Go to: https://console.cloud.google.com
   - APIs & Services > OAuth consent screen
   - Add the new scope to the list

---

## 🔍 SCOPE VERIFICATION

### Verify What Scopes Are Active:

```python
# In Python
from services.gmail import get_service

# This will fail if scopes insufficient
service = get_service()
profile = service.users().getProfile(userId='me').execute()
print(f"Email: {profile['emailAddress']}")
print(f"Total messages: {profile['messagesTotal']}")
```

### Check Token File:
```bash
cat server/tokens/user_dev.json | jq .scopes
```

### Programmatic Check:
```python
import json

with open('server/tokens/user_dev.json') as f:
    token = json.load(f)
    
granted = token.get('scopes', [])
needed = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    # ... etc
]

missing = [s for s in needed if s not in granted]
if missing:
    print(f"❌ Missing scopes: {missing}")
else:
    print("✅ All scopes granted!")
```

---

## 📱 MOBILE / DESKTOP APPS

If you ever make a mobile or desktop app:

### OAuth 2.0 for Mobile/Desktop:
- Use **PKCE flow** (more secure)
- Store tokens in secure keychain/credential manager
- Never hardcode client secret in app

### Platform-Specific Auth:
- **iOS**: Use ASWebAuthenticationSession
- **Android**: Use Custom Tabs
- **Desktop**: Use system browser with localhost redirect

---

## 🎓 BEST PRACTICES

### DO:
- ✅ Request minimum scopes needed
- ✅ Document why each scope is needed
- ✅ Provide clear explanation to users
- ✅ Handle token expiration gracefully
- ✅ Store tokens securely
- ✅ Use incremental authorization (add scopes as needed)

### DON'T:
- ❌ Request scopes "just in case"
- ❌ Request full `gmail` scope (too broad)
- ❌ Store tokens in version control
- ❌ Share tokens between users
- ❌ Forget to refresh expired tokens

---

## 📊 SCOPE AUDIT LOG

| Date | Change | Reason |
|------|--------|--------|
| 2024-XX-XX | Initial scopes | Gmail, Calendar, Tasks |
| 2025-01-XX | Added image analysis | RAP Mobile dashboard support |
| Future | TBD | New features as needed |

---

## 🆘 TROUBLESHOOTING

### "Insufficient Permission" Error:
**Fix:** Re-authenticate to grant new scopes
```bash
curl http://localhost:8000/auth/url
```

### Token Expired:
**Fix:** App should auto-refresh, but if not:
```bash
rm server/tokens/user_dev.json
# Re-authenticate
```

### Scope Mismatch Warning:
**Fix:** This is usually safe to ignore. The app will work with the scopes you granted.

### Can't Access Calendar/Tasks:
**Fix:** Check if scopes were actually granted:
```bash
curl http://localhost:8000/auth/scopes
```

---

## 📚 REFERENCES

- [Google OAuth 2.0 Scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
- [Gmail API Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Calendar API Scopes](https://developers.google.com/calendar/api/auth)
- [Tasks API Scopes](https://developers.google.com/tasks/reference/rest)

---

**Last Updated:** November 2024  
**Current Version:** ChiliHead OpsManager v1.0  
**Scope Count:** 7 Google OAuth scopes
