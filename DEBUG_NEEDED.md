# 🚨 3 CRITICAL FIXES NEEDED

## Problem 1: Markdown Not Rendering ✅ FIXABLE
**Location:** `TriagePage.tsx` line 989  
**Issue:** Displaying `analysis.analysis` as plain text  
**Fix:** Install `react-markdown` and render properly

## Problem 2: Tasks Not Showing  ✅ FIXABLE
**Location:** Smart assistant returns tasks, but format might be off  
**Issue:** Frontend expects `analysis.tasks` array, backend provides it  
**Debug needed:** Check what `analysis.tasks` actually contains

## Problem 3: Only 2 Emails  ❓ NEEDS INVESTIGATION
**Location:** Backend filtering  
**Issue:** Frontend requests 20 emails (line 236), but only 2 show  
**Possible causes:**
  - Watch config too restrictive
  - Priority filter being too aggressive
  - Time range filtering

---

## 🔧 FIXES TO APPLY:

### Fix 1: Install Markdown Renderer
```bash
cd client
npm install react-markdown remark-gfm
```

### Fix 2 & 3: I need to see what's actually happening

**Can you:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "AI Analysis" on an email
4. Look for the `/smart-triage` request
5. Click on it and show me the "Response" tab

This will tell me exactly what format the AI is returning tasks in.

Also check the `/threads` request to see how many emails the backend is actually returning.

---

## Quick Temporary Workaround:

If you want to see the markdown rendered NOW before we fix the root cause:

1. Copy the AI analysis text
2. Paste it into: https://markdownlivepreview.com/
3. See it rendered properly

But let's fix it properly. Can you check those network requests?
