# Quick Start - Email Attachments

## Setup (One-time)

✅ **Already Done:**
1. Database table created
2. Code implemented
3. Migration run successfully

## Testing the System

### Step 1: Sync Emails
```
1. Start backend: start_unified.bat
2. Open Smart Inbox: http://localhost:3001/inbox
3. Click "Sync Emails" button
4. Wait for sync to complete
```

Attachments are now automatically fetched and stored during sync!

### Step 2: Verify Storage
```bash
cd server
.venv/Scripts/python test_attachments.py
```

This shows:
- How many attachments are stored
- Recent attachments with details
- URLs to access them

### Step 3: View Email with Images
```
1. Open an email in Smart Inbox
2. Images should display automatically
3. Check browser DevTools Network tab
4. Look for requests to /api/attachments/by-cid/...
```

### Step 4: Test AI Analysis
```
1. Find RAP Mobile email (with dashboard screenshot)
2. Click "Analyze with AI"
3. AUBS should mention metrics from the image
4. Check that vision analysis is working
```

## How to Get RAP Mobile Email

Forward a RAP Mobile report to your watched email address:
- RAP Mobile sends daily/weekly dashboard reports
- Contains inline images with KPI charts
- Perfect for testing vision analysis

## Troubleshooting

### Images Not Showing?
```bash
# Check if attachments were stored
cd server
.venv/Scripts/python test_attachments.py

# Check database directly
psql -U postgres -d opsmanager
SELECT COUNT(*) FROM email_attachments WHERE mime_type LIKE 'image/%';
```

### Attachments Not Syncing?
- Check console logs during sync
- Verify Gmail API quota
- Check OAuth scopes include gmail.readonly
- Look for errors in backend logs

### AI Not Analyzing Images?
- Ensure OpenAI API key is set
- Verify model is gpt-4o (supports vision)
- Check that `use_vision=True` in AI triage
- Database session must be passed to summarize_thread_advanced()

## API Endpoints

### Serve Attachment by ID
```
GET /api/attachments/{attachment_id}
```

### Serve Inline Image by Content-ID
```
GET /api/attachments/by-cid/{thread_id}/{content_id}
```

### Example URLs
```
http://localhost:8002/api/attachments/abc-123-def
http://localhost:8002/api/attachments/by-cid/thread_xyz/image001@mobile.rap.com
```

## Technical Details

### Where Attachments Are Stored
- Database: `email_attachments` table
- Format: Base64-encoded text
- Includes: Images, PDFs, other files

### How cid: References Work
**Before:**
```html
<img src="cid:abc123@example.com" />
```

**After Processing:**
```html
<img src="http://localhost:8002/api/attachments/by-cid/thread_xyz/abc123@example.com" />
```

### What Gets Stored
1. **Inline images** - Images embedded in HTML (cid: references)
2. **Attachments** - Files attached to email
3. **Metadata** - Filename, size, MIME type, Content-ID

### Performance
- Attachments fetched ONCE during sync
- Stored permanently in database
- No re-fetching from Gmail
- Instant serving via backend endpoints

## Files to Know

### Code
- `server/models.py` - EmailAttachment model
- `server/services/email_sync.py` - Attachment extraction
- `server/services/gmail.py` - Gmail API integration
- `server/app.py` - Serving endpoints
- `server/services/ai_triage.py` - Vision analysis

### Documentation
- `ATTACHMENT_SYSTEM.md` - Complete technical guide
- `ATTACHMENT_IMPLEMENTATION_SUMMARY.md` - What was done
- `QUICK_START_ATTACHMENTS.md` - This file

### Testing
- `server/test_attachments.py` - Quick verification script
- `server/migrations/add_email_attachments_table.py` - Migration

## Common Use Cases

### View RAP Mobile Dashboard
1. Forward RAP Mobile email to watched address
2. Sync emails in Smart Inbox
3. Open email
4. Dashboard screenshots display automatically

### AI Analysis of Dashboard
1. Click "Analyze with AI" on RAP Mobile email
2. AUBS analyzes both text and images
3. Gets KPI insights from dashboard screenshot
4. Provides specific recommendations

### Download Attachment
1. View email in Smart Inbox
2. Click attachment link
3. Browser downloads/displays file
4. Served from local database (fast!)

## Success Criteria

✅ Images display in email HTML
✅ AI can analyze dashboard screenshots
✅ No broken image links
✅ Attachments served instantly
✅ No duplicate Gmail API calls

## What's Next?

Everything is ready! Just:
1. Sync some emails
2. Verify images work
3. Test AI analysis

The system handles everything automatically from now on.

## Need Help?

- Check backend console logs
- Run test_attachments.py for diagnostics
- Review ATTACHMENT_SYSTEM.md for details
- Check browser DevTools Network tab
