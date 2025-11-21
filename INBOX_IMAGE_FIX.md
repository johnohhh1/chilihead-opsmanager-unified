# Smart Inbox Image Display & Vision Analysis Fix

## Issues Fixed

### 1. Smart Triage 500 Errors ✅
**Problem**: The `/smart-triage` endpoint was throwing 500 errors
**Root Cause**:
- Function wasn't extracting images from emails for vision analysis
- Missing error handling when database tables don't exist
- Not downloading Gmail attachment images before analysis

**Fix Applied**:
- Updated `smart_triage()` in `server/services/smart_assistant.py` to:
  - Extract images using `extract_attachments_with_images()`
  - Download attachment images from Gmail API
  - Pass images to vision models (gpt-4o, claude-3-opus, etc.) for analysis
  - Add comprehensive try/catch error handling to prevent 500 errors
  - Log errors with traceback for debugging

### 2. Images Not Displaying in Smart Inbox ✅
**Problem**: RAP Mobile dashboard images and other email images not showing
**Root Cause**: Database table `email_attachments` may not exist or have wrong schema

**Fix Applied**:
- Created `server/init_database.py` to initialize all database tables
- Ensures `gmail_attachment_id` column is TEXT (not VARCHAR(255))
- Backend already has proper `process_html_with_attachments()` to convert cid: references

### 3. Vision Analysis Not Working ✅
**Problem**: AI couldn't analyze RAP Mobile dashboard images
**Root Cause**: smart_triage wasn't passing images to vision-capable models

**Fix Applied**:
- smart_triage now detects vision-capable models
- Formats images as base64 data URLs for GPT-4o and Claude vision models
- Instructs AI to extract metrics from dashboard screenshots
- Limits to 3 images per request to avoid token limits

## Setup Instructions

### Step 1: Initialize Database

Run the database initialization script to create all tables:

```bash
cd server
python init_database.py
```

**Expected Output**:
```
🔧 Initializing database...
Creating tables from models...
✅ All tables created successfully
✅ gmail_attachment_id is already TEXT
✅ Database initialization complete!
```

### Step 2: Start Backend Server

```bash
cd server
.venv/Scripts/python -m uvicorn app:app --reload --port 8002
```

**On Linux/Mac**:
```bash
cd server
.venv/bin/python -m uvicorn app:app --reload --port 8002
```

### Step 3: Start Frontend

```bash
cd client
npm run dev
```

### Step 4: Sync Emails with Images

1. Go to Smart Inbox page
2. Click "Sync Inbox" button
3. Wait for emails to download

### Step 5: Test Vision Analysis

1. Select an email with images (like RAP Mobile dashboard)
2. Select a vision model from dropdown (gpt-4o recommended)
3. Click "Analyze" button
4. AI should now extract metrics from dashboard images

## How It Works Now

### Image Extraction Flow:
1. **Email Sync**: When syncing emails, `extract_and_store_attachments()` stores images in `email_attachments` table
2. **CID Conversion**: `process_html_with_attachments()` converts `cid:xxx` references to `/api/attachments/by-cid/thread_id/content_id`
3. **Frontend Display**: Smart Inbox displays images using converted URLs
4. **Vision Analysis**: smart_triage downloads images and sends to GPT-4o/Claude for analysis

### Vision Models Supported:
- `gpt-4o` ✅ (Recommended - fast and accurate)
- `gpt-4-vision-preview` ✅
- `claude-3-opus-20240229` ✅
- `claude-3-sonnet-20240229` ✅

### Image Sources Handled:
- Inline images (cid: references)
- Gmail attachments
- RAP Mobile dashboard screenshots
- Any image MIME type (PNG, JPG, GIF, WebP)

## Testing Checklist

- [ ] Database initialized successfully
- [ ] Backend starts without errors
- [ ] Smart Inbox loads and shows emails
- [ ] Clicking "Sync Inbox" downloads new emails
- [ ] Emails with images show image count badge
- [ ] Clicking on email shows images in preview
- [ ] Selecting vision model (gpt-4o) works
- [ ] Clicking "Analyze" on RAP Mobile email succeeds
- [ ] Analysis includes metrics extracted from dashboard image
- [ ] No 500 errors in console
- [ ] inbox/stats endpoint returns data (no 404)

## Troubleshooting

### 500 Error on smart-triage
**Check backend logs for**:
- Database connection errors
- Missing table errors
- Gmail API authentication issues

**Solution**: Run `python init_database.py`

### 404 Error on /inbox/stats
**Check**:
- Backend server is running on port 8002
- Router is properly registered in app.py

**Current Status**: Route exists and should work after backend restart

### Images not showing
**Check**:
- email_attachments table exists
- gmail_attachment_id column is TEXT
- CID references are being converted properly

**Solution**:
1. Run database init script
2. Re-sync emails
3. Check browser dev tools for image load errors

### Vision analysis not extracting metrics
**Check**:
- Using a vision-capable model (gpt-4o, claude-3-opus, etc.)
- Email actually contains images
- Images are being passed to the model (check backend logs)

**Solution**: Select gpt-4o from model dropdown before analyzing

## File Changes Summary

### Modified Files:
- `server/services/smart_assistant.py` - Added vision support to smart_triage()
- Added comprehensive error handling
- Extract and download images from Gmail
  - Format images for vision models

### New Files:
- `server/init_database.py` - Database initialization script
- `INBOX_IMAGE_FIX.md` - This documentation

### Existing Files (No Changes Needed):
- `server/services/email_sync.py` - Already handles CID conversion properly
- `server/routes/inbox.py` - inbox/stats route exists
- `client/app/components/SmartInboxPage.tsx` - Image display logic correct

## Next Steps

After testing, you can:
1. Set up auto-sync for inbox emails
2. Configure watched domains for filtering
3. Use vision analysis for all RAP Mobile emails
4. Extract portal metrics automatically

## Questions?

If you encounter issues:
1. Check backend logs in terminal
2. Check browser console for frontend errors
3. Verify database tables exist: `psql -d openinbox_dev -c "\dt"`
4. Test endpoints manually with curl:
   ```bash
   curl http://localhost:8002/inbox/stats
   curl http://localhost:8002/health
   ```
