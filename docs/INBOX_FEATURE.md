# Inbox Feature - Implementation Complete

## Overview
Added a lightweight email client "Inbox" tab that syncs and displays emails from priority domains (like brinker.com, hotschedules.com) using the existing Gmail API integration.

## What Was Added

### Backend (`server/`)

1. **Email Sync Service** (`server/services/email_sync.py`)
   - Added inbox-specific methods to existing `EmailSyncService`:
   - `sync_emails()` - Fetches emails from Gmail filtered by priority domains
   - `get_inbox_emails()` - Retrieves emails from cache with filters
   - `get_email_by_thread()` - Gets full email content including AI analysis
   - `mark_read()` - Toggles read/unread status
   - `get_watched_domains()` - Lists configured domains
   - `add_watched_domain()` - Adds domain to watch list
   - `remove_watched_domain()` - Removes domain from watch list

2. **API Routes** (`server/routes/inbox.py`)
   - `POST /sync-inbox` - Manual email sync trigger
   - `GET /api/inbox` - List emails (supports filters: unread_only, domain, pagination)
   - `GET /api/inbox/{thread_id}` - Get full email details
   - `PATCH /api/inbox/{thread_id}/mark-read` - Mark as read/unread
   - `GET /api/settings/domains` - Get watched domains
   - `POST /api/settings/domains` - Add domain
   - `DELETE /api/settings/domains` - Remove domain
   - `GET /api/inbox/stats` - Inbox statistics

3. **App Integration** (`server/app.py`)
   - Registered inbox router

### Frontend (`client/`)

1. **InboxPage Component** (`client/app/components/InboxPage.tsx`)
   - **Email List View**: Shows sender, subject, preview, date, read/unread status
   - **Email Detail View**: Full email content (HTML or text)
   - **Filters**: All emails, Unread only
   - **Search**: Search by subject or sender
   - **Domain Management**: Add/remove watched domains
   - **Sync Button**: Manual sync trigger
   - **Read/Unread Toggle**: Mark emails as read/unread
   - **Stats Display**: Shows total emails and unread count
   - **AI Analysis Display**: Shows priority score and category if analyzed

2. **Navigation Update** (`client/app/page.tsx`)
   - Added "Inbox" as first tab (Tab 0)
   - Set as default landing page
   - Imported `Mail` icon from lucide-react

## How to Use

### 1. Start the Application

```bash
# Start database (if not running)
scripts\start_database.bat

# Start backend and frontend
start_unified.bat
```

### 2. Configure Watched Domains

1. Navigate to the **Inbox** tab
2. Click **Domains** button
3. Add domains you want to monitor:
   - `brinker.com`
   - `hotschedules.com`
   - `chilis.com`
4. Domains are saved to the `watch_config` table

### 3. Sync Emails

1. Click **Sync Now** button
2. Backend fetches up to 50 emails from Gmail matching your domains
3. Emails are stored in the `email_cache` table

### 4. Browse Emails

- **Filter by status**: All or Unread
- **Search**: Type in search box to filter by subject/sender
- **Click email**: View full content in right panel
- **Mark as read/unread**: Click button in email detail view

### 5. AI Integration (Future)

- Email analysis from existing AI triage can be displayed
- "Extract Tasks" button is placeholder for future integration

## Database Tables Used

### Existing Tables
- `email_cache` - Stores email content synced from Gmail
- `watch_config` - Stores priority domains (used by both Triage and Inbox)
- `email_analysis_cache` - AI analysis (displayed if available)

### Fields Used
- `EmailCache.thread_id` (primary key)
- `EmailCache.subject`, `sender`, `body_text`, `body_html`
- `EmailCache.is_read`, `is_archived`
- `EmailCache.received_at`, `labels`
- `WatchConfig.priority_domains` (JSON array)

## API Examples

### Sync emails from Gmail
```bash
curl -X POST http://localhost:8002/sync-inbox
```

### Get inbox emails
```bash
# All emails
curl http://localhost:8002/api/inbox

# Unread only
curl http://localhost:8002/api/inbox?unread_only=true

# Filter by domain
curl http://localhost:8002/api/inbox?domain=brinker.com
```

### Get specific email
```bash
curl http://localhost:8002/api/inbox/{thread_id}
```

### Mark as read
```bash
curl -X PATCH http://localhost:8002/api/inbox/{thread_id}/mark-read \
  -H "Content-Type: application/json" \
  -d '{"is_read": true}'
```

### Manage domains
```bash
# Get domains
curl http://localhost:8002/api/settings/domains

# Add domain
curl -X POST http://localhost:8002/api/settings/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "brinker.com"}'

# Remove domain
curl -X DELETE http://localhost:8002/api/settings/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "brinker.com"}'
```

## Features

### ✅ Implemented
- Email sync from Gmail with domain filtering
- Local email cache (no repeated API calls)
- Read/unread status tracking
- Email list with preview
- Full email view (HTML and text)
- Search and filters
- Domain management UI
- Manual sync trigger
- Inbox statistics
- Dark mode UI matching app style

### 🔄 Future Enhancements
- **Background sync**: Auto-sync every 5-10 minutes (needs background task)
- **Task extraction**: Integrate with existing AI triage to extract tasks
- **Email archiving**: Archive emails to clean up inbox
- **Reply/Forward**: Send emails (would need Gmail send API)
- **Attachments**: Download and view attachments
- **Labels/Tags**: Apply custom labels
- **Notifications**: Show badge count on Inbox tab

## Architecture Notes

### Email Sync Flow
1. User clicks "Sync Now" OR background task runs
2. Backend calls `EmailSyncService.sync_emails()`
3. Service builds Gmail query from `WatchConfig.priority_domains`
4. Fetches threads using `get_user_threads()` with query
5. Parses email metadata and body
6. Stores/updates in `email_cache` table
7. Returns sync stats (synced count, updated count)

### Gmail Query Format
```python
# Example for ["brinker.com", "hotschedules.com"]
query = "from:*@brinker.com OR from:*@hotschedules.com"
```

### Email Body Parsing
- Handles both `text/plain` and `text/html` MIME types
- Recursively extracts parts from multipart messages
- Decodes Gmail's base64url encoding
- Stores both `body_text` and `body_html`

## Design Decisions

1. **Reused Existing Infrastructure**
   - Uses existing `EmailCache` model
   - Uses existing `WatchConfig` for domain filtering
   - Uses existing `gmail.py` service
   - Consistent with app's dark mode design

2. **Local Cache First**
   - Reduces Gmail API calls
   - Faster load times
   - Works offline (after initial sync)

3. **Manual Sync**
   - User controls when to fetch new emails
   - Future: Add background sync with configurable interval

4. **Simple UI**
   - Two-column layout (list + detail)
   - Matches existing app patterns
   - Minimal but functional

## Testing Checklist

- [ ] Start app with `start_unified.bat`
- [ ] Navigate to Inbox tab
- [ ] Add domains (brinker.com, hotschedules.com)
- [ ] Click "Sync Now" - should fetch emails
- [ ] Verify emails appear in list
- [ ] Click an email - should show full content
- [ ] Mark as read/unread - should update status
- [ ] Test filters (All/Unread)
- [ ] Test search functionality
- [ ] Verify stats display correctly
- [ ] Check existing features still work (Triage, Todos, etc.)

## Files Modified/Created

### Backend
- ✏️ `server/services/email_sync.py` (added inbox methods)
- ➕ `server/routes/inbox.py` (new)
- ✏️ `server/app.py` (registered inbox router)

### Frontend
- ➕ `client/app/components/InboxPage.tsx` (new)
- ✏️ `client/app/page.tsx` (added Inbox tab)

### Documentation
- ➕ `INBOX_FEATURE.md` (this file)

## Troubleshooting

### No emails showing after sync
1. Check domains are configured correctly
2. Verify Gmail API is authenticated (`server/tokens/user_dev.json` exists)
3. Check backend logs for sync errors
4. Try manual sync with curl to see error messages

### Emails not displaying correctly
1. Check if `body_html` or `body_text` is populated
2. Some emails may have nested multipart structure
3. Check browser console for React errors

### Sync fails
1. Ensure database is running (port 5432)
2. Check Gmail API quota (shouldn't be an issue for <50 emails)
3. Verify OAuth token is valid

## Next Steps

1. **Test the feature** with real emails
2. **Add background sync** using APScheduler or similar
3. **Integrate with AI triage** - show analysis in inbox
4. **Task extraction** - one-click to add tasks from email
5. **Email threading** - show conversation threads properly
6. **Pagination** - add "Load More" for large inboxes
