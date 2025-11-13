# Inbox Feature - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Application

```bash
# Windows
start_unified.bat

# This starts:
# - PostgreSQL database (port 5432)
# - Backend API (port 8002)
# - Frontend (port 3001)
```

### Step 2: Configure Domains (Optional)

**Option A: Use the UI** (Recommended)
1. Open http://localhost:3001
2. Click the **Inbox** tab (first tab)
3. Click **Domains** button
4. Add domains:
   - `brinker.com`
   - `hotschedules.com`
   - `chilis.com`

**Option B: Run Init Script**
```bash
cd server
.venv\Scripts\python init_inbox_domains.py
```

### Step 3: Sync Your Emails

1. In the Inbox tab, click **Sync Now**
2. Wait for sync to complete (fetches up to 50 emails)
3. Browse your emails!

## 📧 Using the Inbox

### View Emails
- **Email list** shows sender, subject, preview, date
- **Click any email** to view full content
- **Unread emails** have a red mail icon
- **Read emails** have a gray mail icon

### Filter & Search
- **All / Unread** buttons to filter
- **Search bar** to search by subject or sender
- **Domain badges** show which domain each email is from

### Mark as Read/Unread
1. Click an email to open it
2. Click **Mark as Read/Unread** button at bottom

### Manage Domains
1. Click **Domains** button
2. Type domain name (e.g., `example.com`)
3. Click **Add**
4. To remove: click **Remove** next to any domain

## 🔄 Background Sync (Coming Soon)

Currently, syncing is manual (click "Sync Now" button).

Future update will add automatic background sync every 5-10 minutes.

## 🎯 Features

- ✅ Lightweight email client view
- ✅ Domain-based filtering
- ✅ Read/unread status
- ✅ Search emails
- ✅ Full email content (HTML + text)
- ✅ Dark mode UI
- ✅ Fast (local cache)
- 🔄 AI analysis integration (coming soon)
- 🔄 Extract tasks from emails (coming soon)
- 🔄 Background sync (coming soon)

## 📊 How It Works

1. **You configure domains** you care about (brinker.com, etc.)
2. **Click Sync Now** → fetches emails from Gmail
3. **Emails are cached** in PostgreSQL database
4. **View emails** without hitting Gmail API repeatedly
5. **Read status** is stored locally

## 🔧 Troubleshooting

### No emails showing?
- Make sure domains are configured
- Click "Sync Now" button
- Check backend logs for errors

### Sync button stuck?
- Refresh the page
- Check database is running
- Verify Gmail OAuth is working

### Emails look weird?
- Some emails may have complex HTML
- Use text view if HTML doesn't render well

## 🎨 UI Elements

| Icon | Meaning |
|------|---------|
| 📧 Red mail icon | Unread email |
| 📭 Gray mail icon | Read email |
| 🔄 Spinning icon | Syncing... |
| ⚙️ Settings icon | Domain settings |

## 📝 Notes

- Inbox syncs emails from **priority domains only**
- Does NOT sync all Gmail emails (by design)
- Local cache means fast loading
- Works alongside existing Email Triage feature
- Complements Todos, Delegations, and other features

## 🎉 That's It!

You now have a lightweight email inbox that shows only emails from domains you care about, perfect for operations management workflows.

For more details, see [INBOX_FEATURE.md](INBOX_FEATURE.md)
