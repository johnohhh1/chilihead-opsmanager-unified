# Quick Fixes Reference Card

## ✅ FIXED: Memory Updates Not Working

**Problem:** AUBS keeps showing resolved items as urgent

**Solution:** Just tell AUBS naturally!

```
You: "the pedro issue was handled yesterday"
```

AUBS automatically marks related memories as resolved and filters them out.

### Keywords That Work
- "was handled"
- "already done"
- "resolved"
- "completed"
- "update the memory"

### Manual Override
```bash
curl -X POST http://localhost:8002/api/operations-chat/mark-resolved \
  -H "Content-Type: application/json" \
  -d '{"topic": "pedro"}'
```

---

## ✅ FIXED: RAP Mobile Images Not Showing

**Problem:** Dashboard screenshots show broken image icon

**Solution:** Sync emails - attachments now automatically fetched and stored!

### How to Test
1. **Sync**: Click "Sync Emails" in Smart Inbox
2. **View**: Open RAP Mobile email
3. **Verify**: Image displays (not broken icon)
4. **AI**: Click "Analyze with AI" - AUBS mentions dashboard metrics

### Check Storage
```bash
cd server
.venv/Scripts/python test_attachments.py
```

### Troubleshoot
- Images serve from: `/api/attachments/by-cid/{thread_id}/{content_id}`
- Check browser DevTools Network tab for 404s
- Backend logs show attachment requests

---

## What Was Fixed

### 1. Agent Memory System
- ✅ Detects when you correct it
- ✅ Marks items as resolved
- ✅ Filters resolved from future chats
- ✅ Tracks your notes

**Files:** `services/agent_memory.py`, `routes/operations_chat.py`

### 2. Email Attachment System
- ✅ Fetches Gmail attachments
- ✅ Stores in database
- ✅ Serves via backend
- ✅ Replaces cid: references
- ✅ AI can analyze images

**Files:** `models.py`, `services/gmail.py`, `services/email_sync.py`, `app.py`, `services/ai_triage.py`

---

## Testing Right Now

### Test Memory Updates
```
1. Open Operations Chat
2. Say: "pedro was handled"
3. Say: "what's urgent?"
4. Pedro should NOT appear
```

### Test RAP Mobile
```
1. Forward RAP Mobile email to watched address
2. Sync emails
3. Open email
4. Image displays correctly
5. AI analysis mentions dashboard metrics
```

---

## Common Issues

### "AUBS still mentions resolved items"
→ Check backend logs for `[Memory Update]` message
→ Try manual API: `POST /api/operations-chat/mark-resolved`

### "Images still broken"
→ Run migration: `.venv/Scripts/python migrations/add_email_attachments_table.py`
→ Sync emails again
→ Check `test_attachments.py`

### "AI doesn't see images"
→ Verify model is `gpt-4o` (not `gpt-4`)
→ Check OpenAI API key has vision access
→ Ensure database session passed to AI triage

---

## Quick Commands

```bash
# Check memory status
curl http://localhost:8002/api/operations-chat/memory-status

# Mark something resolved
curl -X POST http://localhost:8002/api/operations-chat/mark-resolved \
  -H "Content-Type: application/json" \
  -d '{"topic": "pedro"}'

# Test attachments
cd server && .venv/Scripts/python test_attachments.py

# Run migration (one-time)
cd server && .venv/Scripts/python migrations/add_email_attachments_table.py
```

---

## Documentation

- **MEMORY_UPDATE_FEATURE.md** - Complete memory guide
- **ATTACHMENT_SYSTEM.md** - Full attachment docs
- **FIXES_SUMMARY.md** - Detailed summary
- **QUICK_START_ATTACHMENTS.md** - Step-by-step testing

---

## Status

🟢 **Memory Updates** - Working
🟢 **RAP Mobile Images** - Working
🟢 **AI Vision Analysis** - Working
🟢 **Attachment Storage** - Working

Everything is production-ready! Just sync emails and start chatting. 🌶️
