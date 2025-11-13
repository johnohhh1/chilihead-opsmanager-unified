# Email Attachment System

Complete implementation of email attachment handling including inline images (RAP Mobile screenshots).

## Overview

The system fetches, stores, and serves email attachments including:
- ✅ Inline images with `cid:` references (RAP Mobile reports)
- ✅ Regular attachments with `attachmentId`
- ✅ Image analysis for AI triage
- ✅ HTML processing to display inline images

## Architecture

### 1. Database Storage
**Table:** `email_attachments`

```python
EmailAttachment:
    - id: UUID primary key
    - thread_id: Gmail thread ID (indexed)
    - gmail_message_id: Gmail message ID (indexed)
    - gmail_attachment_id: Gmail's attachmentId for fetching
    - filename: Original filename
    - mime_type: Content type (e.g., 'image/png')
    - size_bytes: File size
    - content_id: For cid: references (indexed)
    - data: Base64-encoded file data
    - is_inline: Boolean flag
    - created_at: Timestamp
    - last_accessed_at: Last served timestamp
```

### 2. Gmail API Integration
**File:** `server/services/gmail.py`

```python
get_attachment(message_id, attachment_id) -> dict
```

Fetches attachment data from Gmail API using the attachmentId.

### 3. Email Sync Service
**File:** `server/services/email_sync.py`

#### Key Methods:

**extract_and_store_attachments(db, message, thread_id)**
- Recursively processes email payload parts
- Extracts Content-ID from headers for inline images
- Fetches attachment data via Gmail API
- Stores in database
- Returns attachment metadata

**process_html_with_attachments(db, thread_id, body_html)**
- Replaces `cid:xxxxx` references with backend URLs
- Pattern: `src="cid:123"` → `src="http://localhost:8002/api/attachments/by-cid/{thread_id}/123"`

**get_email_by_thread(db, thread_id)**
- Automatically processes HTML to replace cid: references
- Returns email with working inline image URLs

### 4. Backend API Endpoints
**File:** `server/app.py`

#### GET `/api/attachments/{attachment_id}`
Serves attachment by database ID.

**Response:** Binary file with appropriate Content-Type

#### GET `/api/attachments/by-cid/{thread_id}/{content_id}`
Serves attachment by Content-ID (for cid: references).

**Response:** Binary file with appropriate Content-Type

Both endpoints:
- Decode base64url data from Gmail
- Set correct MIME type
- Update last_accessed_at timestamp
- Return 404 if not found

### 5. AI Triage Integration
**File:** `server/services/ai_triage.py`

**summarize_thread_advanced(thread_id, use_vision=True, db=None)**

Now fetches attachments from database:
1. Extracts inline images from payload (as before)
2. Queries `EmailAttachment` table for stored images
3. Deduplicates images
4. Passes all images to GPT-4o for analysis

```python
# Fetch stored attachments from database
stored_attachments = db.query(EmailAttachment).filter(
    EmailAttachment.thread_id == thread_id,
    EmailAttachment.mime_type.like('image/%')
).all()

# Add to all_images list for AI analysis
all_images.append({
    'mime_type': att.mime_type,
    'data': att.data,  # Base64-encoded
    'filename': att.filename,
    'from_db': True
})
```

## Usage Flow

### Email Sync Process
1. User syncs emails via `/inbox/sync`
2. `EmailSyncService.sync_emails()` called
3. For each email:
   - `extract_email_metadata()` - Extract headers, subject, sender
   - `parse_email_body()` - Extract text/HTML content
   - **`extract_and_store_attachments()`** - NEW: Store attachments
4. Attachments saved to `email_attachments` table
5. Metadata cached in `email_cache.attachments_json`

### AI Analysis Process
1. User clicks "Analyze with AI" on email
2. `POST /ai-triage` called with thread_id
3. `summarize_thread_advanced()` fetches:
   - Email messages from Gmail API
   - Stored attachments from database
4. All images passed to GPT-4o with vision
5. AUBS analyzes text + images for insights

### Display Process
1. Frontend requests email via `/inbox/email/{thread_id}`
2. `get_email_by_thread()` returns email data
3. **`process_html_with_attachments()`** replaces cid: references
4. Frontend renders HTML with working image URLs
5. Browser fetches images from `/api/attachments/by-cid/...`

## RAP Mobile Integration

RAP Mobile emails contain dashboard screenshots as inline images:

**Before:**
```html
<img src="cid:abc123def@mobile.rap.com" />
```

**After Processing:**
```html
<img src="http://localhost:8002/api/attachments/by-cid/thread_xyz/abc123def@mobile.rap.com" />
```

## Installation & Setup

### 1. Run Migration
```bash
cd server
.venv/Scripts/python migrations/add_email_attachments_table.py
```

### 2. Sync Emails
Visit Smart Inbox and click "Sync Emails" - attachments will be automatically fetched and stored.

### 3. Verify
Check database:
```sql
SELECT
    filename,
    mime_type,
    size_bytes,
    is_inline,
    thread_id
FROM email_attachments
WHERE mime_type LIKE 'image/%';
```

## Performance Considerations

### Storage
- Base64 encoding increases size by ~33%
- Images stored in PostgreSQL TEXT column
- Consider moving to filesystem/S3 for large volumes

### Caching
- Attachments fetched once during sync
- Stored permanently in database
- No re-fetching from Gmail API

### Optimization Ideas
1. **Lazy Loading**: Fetch attachments on-demand instead of during sync
2. **Compression**: Compress images before storing
3. **External Storage**: Use S3/filesystem for large files
4. **CDN**: Cache frequently accessed attachments
5. **Cleanup**: Delete old attachments after N days

## Error Handling

### Missing Attachments
- Returns 404 with clear error message
- Logs to console for debugging

### Decode Errors
- Returns 500 with decode error details
- Gmail uses base64url encoding (not standard base64)

### Gmail API Failures
- Catches exceptions during `get_attachment()`
- Logs error and continues with other attachments
- Marks attachment as `stored: false` in metadata

## Testing

### Test Inline Images
1. Forward RAP Mobile email to watched address
2. Sync emails
3. View email in Smart Inbox
4. Verify images display correctly

### Test Regular Attachments
1. Send email with image attachments
2. Sync emails
3. Check database for stored attachments
4. Access via `/api/attachments/{id}`

### Test AI Analysis
1. Analyze RAP Mobile email
2. Check that AUBS mentions metrics from dashboard
3. Verify token usage includes vision costs

## Security Considerations

### Access Control
- Currently no authentication on attachment endpoints
- TODO: Add user authentication
- TODO: Verify user owns the email thread

### Content-Type Validation
- Validates MIME type before serving
- Prevents XSS via crafted filenames

### Size Limits
- Gmail API has 25MB attachment limit
- Consider adding database-level size checks

## Future Enhancements

1. **PDF Support**: Extract text from PDF attachments
2. **OCR**: Extract text from images (already implemented for Portal Metrics)
3. **Thumbnails**: Generate thumbnails for large images
4. **Sharing**: Allow sharing attachments via public URLs
5. **Download All**: ZIP multiple attachments for download
6. **Virus Scanning**: Scan attachments for malware
7. **Expiration**: Auto-delete old attachments to save space

## Troubleshooting

### Images Not Showing
1. Check database: `SELECT * FROM email_attachments WHERE thread_id = 'xxx'`
2. Check content_id matches cid: reference
3. Verify backend URL in HTML processing
4. Check browser console for 404 errors

### AI Not Analyzing Images
1. Verify `use_vision=True` in AI triage call
2. Check that images exist in database
3. Verify OpenAI API key has vision access
4. Check that model is `gpt-4o` (not `gpt-4`)

### Sync Failing
1. Check Gmail API quota
2. Verify OAuth scopes include `gmail.readonly`
3. Check database connectivity
4. Review console logs for errors

## Technical Notes

### Base64URL Encoding
Gmail uses base64url (RFC 4648) which replaces:
- `+` with `-`
- `/` with `_`
- Removes padding `=`

Must convert before decoding:
```python
data_bytes = base64.urlsafe_b64decode(
    attachment.data.replace('-', '+').replace('_', '/')
)
```

### Content-ID Format
- Usually: `<abc123def@domain.com>`
- Brackets removed before storing
- Matches cid: reference without brackets

### Multipart MIME
- Emails use recursive multipart structure
- Must traverse all parts to find attachments
- Content-ID found in part headers, not body

## Files Modified

1. ✅ `server/models.py` - Added EmailAttachment model
2. ✅ `server/services/gmail.py` - Added get_attachment()
3. ✅ `server/services/email_sync.py` - Added attachment extraction
4. ✅ `server/app.py` - Added attachment endpoints
5. ✅ `server/services/ai_triage.py` - Updated to use DB attachments
6. ✅ `server/migrations/add_email_attachments_table.py` - Migration script

## API Reference

### Attachment Endpoints

#### GET /api/attachments/{attachment_id}
Serve attachment by database ID.

**Parameters:**
- `attachment_id` (path): UUID of attachment

**Response:** 200 OK
- Content-Type: From mime_type
- Content-Disposition: inline
- Body: Binary file data

**Errors:**
- 404: Attachment not found
- 500: Decode error

#### GET /api/attachments/by-cid/{thread_id}/{content_id}
Serve attachment by Content-ID for cid: references.

**Parameters:**
- `thread_id` (path): Gmail thread ID
- `content_id` (path): Content-ID without cid: prefix

**Response:** 200 OK
- Content-Type: From mime_type
- Content-Disposition: inline
- Body: Binary file data

**Errors:**
- 404: Attachment not found
- 500: Decode error

## Dependencies

- `google-api-python-client` - Gmail API
- `SQLAlchemy` - Database ORM
- `FastAPI` - Web framework
- `base64` - Encoding/decoding (stdlib)
- `re` - Regex for cid: replacement (stdlib)

No additional packages required! ✅
