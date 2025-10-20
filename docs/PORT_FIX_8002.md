# Port Configuration Fixed - Backend is on 8002

## The Real Issue

Your backend is running on **port 8002**, not 8000!

```
INFO:     Uvicorn running on http://127.0.0.1:8002
```

We initially changed the config to port 8000, but that was wrong.

## What Was Fixed

### 1. Next.js Config ✅
**File:** `client/next.config.js`
```javascript
{
  source: '/api/backend/:path*',
  destination: 'http://localhost:8002/:path*',  // ✅ Changed back to 8002
}
```

### 2. Chat API Routes ✅
**Updated all to use port 8002:**
- `client/app/api/operations-chat/route.ts`
- `client/app/api/operations-chat/sessions/route.ts`
- `client/app/api/operations-chat/history/[sessionId]/route.ts`

Changed:
```typescript
const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';
```

## Verification

✅ Backend health check:
```bash
curl http://localhost:8002/health
# {"ok":true,"app":"OpenInbox OpsManager AI","database":"connected"}
```

## Next Steps

**You need to restart the frontend** for the Next.js config change to take effect:

```bash
# In the frontend terminal, press Ctrl+C to stop it, then:
cd client
npm run dev
```

After restart, all endpoints should work:
- ✅ Email triage
- ✅ Tasks/todo list
- ✅ Delegations
- ✅ Daily digest
- ✅ Operations chat

## Why This Happened

1. Your backend was already running on port 8002
2. We mistakenly changed config to 8000 (thinking that was the port)
3. All API calls were going to the wrong port
4. Now fixed to match your actual backend port (8002)

## Current Configuration

- **Backend:** http://localhost:8002 ✅
- **Frontend:** http://localhost:3001 ✅
- **Database:** PostgreSQL on port 5432 ✅
- **All configs updated to use 8002** ✅

**Action Required:** RESTART FRONTEND (npm run dev)
