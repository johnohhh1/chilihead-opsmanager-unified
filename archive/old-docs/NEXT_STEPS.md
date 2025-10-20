# 🌶️ CHILIHEAD OPSMANAGER - NEXT STEPS

**Date:** October 14, 2025
**Status:** Working but needs improvements

---

## ✅ WHAT'S WORKING NOW

1. **Gmail OAuth** - Port 8002, authenticated
2. **Email Triage** - Shows emails from watched senders
3. **AI Analysis** - GPT-4 analyzes individual emails
4. **Daily Brief** - Now ACTUALLY reads Gmail (was hardcoded, fixed!)
5. **Date Filter Dropdown** - Today, Yesterday, Week, Month, All
6. **Delegations Tab** - ChiliHead 5-pillar system functional

---

## 🚨 CURRENT ISSUES

### **1. Only Showing 5 Emails** 
- Backend configured to fetch 200, but only 5 showing
- Possible causes:
  - OpenAI 10s timeout hitting during fetch
  - Frontend limiting display
  - Priority filter too aggressive
- **NEEDS INVESTIGATION**

### **2. No Specific Date Picker**
- Only has presets (today, week, etc.)
- **NEED:** Actual date input fields for custom ranges
- Gmail API supports: `after:2025/10/01 before:2025/10/15`
- Can also use Unix timestamps for precision

### **3. No Settings/Preferences Panel**
- Can't manage watched senders/domains from UI
- No way to adjust fetch limits
- No API key management interface
- **THIS IS CRITICAL** for making it production-ready

---

## 📋 PRIORITY TODO LIST

### **🔥 HIGH PRIORITY (Do These First)**

1. **Fix the 5-Email Limit**
   - Debug why only 5 showing despite fetching 200
   - Add loading progress indicators
   - Check for timeout issues

2. **Add Specific Date Range Picker**
   ```typescript
   - Add date input fields (from/to)
   - Support YYYY/MM/DD format for Gmail API
   - Allow switching between presets and custom dates
   - Update backend to handle date_from/date_to params
   ```

3. **Build Settings/Preferences Panel**
   ```
   - Tab or modal for settings
   - Manage watched senders/domains (add/remove from UI)
   - Configure fetch limits (50, 100, 200, 500)
   - Set default time range
   - Toggle features on/off
   - API key management
   ```

### **🟡 MEDIUM PRIORITY**

4. **Performance Optimization**
   - Add pagination for large result sets
   - Show "Loading X of Y emails..." progress
   - Cache email data locally
   - Lazy load email bodies

5. **Better Error Handling**
   - Show user-friendly error messages
   - Retry failed requests
   - Handle rate limits gracefully

6. **UI Polish**
   - Loading skeletons
   - Better empty states
   - Improved mobile responsiveness

### **🟢 LOW PRIORITY (Future)**

7. **Unbranding & Generalization**
   - Remove Chili's-specific branding
   - Make it industry-agnostic
   - Add customizable themes
   - Multi-user support

8. **Advanced Features**
   - Email scheduling/reminders
   - Smart categorization with ML
   - Integration with more tools (Slack, Teams, etc.)
   - Analytics dashboard

---

## 🗂️ KEY FILES TO KNOW

```
Backend:
  server/app.py - Main FastAPI app
  server/routes/mail.py - Email endpoints (/threads, /tasks, etc.)
  server/services/smart_assistant.py - AI analysis & daily digest
  server/services/gmail.py - Gmail API wrapper
  server/watch_config.json - Watched senders/domains config
  server/.env - API keys and OAuth credentials

Frontend:
  client/app/page.tsx - Main dashboard with 3 tabs
  client/app/components/TriagePage.tsx - Email triage UI
  client/app/components/TodoPage.tsx - Todo list
  client/app/delegations/ - ChiliHead delegation system
```

---

## 🔧 QUICK FIXES REFERENCE

### To Add Watched Sender:
```json
// Edit server/watch_config.json
{
  "priority_senders": ["allen.woods@brinker.com"],
  "priority_domains": ["brinker.com", "chilis.com"],
  "priority_keywords": ["urgent", "deadline"]
}
```

### To Change Fetch Limit:
```python
# server/routes/mail.py, line ~155
"maxResults": 200  # Change this number
```

### To Add New Time Range:
```python
# Backend: server/routes/mail.py
elif time_range == "custom":
    if date_from:
        query_parts.append(f"after:{date_from}")
    if date_to:
        query_parts.append(f"before:{date_to}")
```

---

## 🎯 VISION (After It Works Perfectly)

**Goal:** Best-in-class Operations Management platform

**Target Users:**
- Restaurant managers (like current use)
- Retail store managers
- Service business operators
- Team leaders with high email volume

**Key Differentiators:**
- AI understands CONTEXT, not just keywords
- Extracts actionable items automatically
- Integrates delegation system
- Clean, focused UX

**Revenue Model (Future):**
- Freemium (basic features free)
- Pro tier ($10/mo): unlimited emails, advanced AI
- Business tier ($50/mo): team features, analytics
- White label licensing

---

## 📝 NOTES FOR NEXT SESSION

- User (John) is frustrated when things don't work
- Expects current, accurate data (not hardcoded!)
- Wants to experiment and iterate
- Has a working version elsewhere but this is dev branch
- Focus on making it work perfectly for his use case FIRST
- Then generalize and unbrand

**Remember:** This is a merge of two projects still being refined. Some features may be broken/incomplete. That's expected during development!

---

## 🚀 START NEXT CHAT WITH:

"Hey! Ready to continue ChiliHead OpsManager. Let's fix the 5-email limit issue and add the date range picker. Then we'll build the settings panel."

---

**Last Updated:** October 14, 2025 @ 8:30 PM ET
**Context Saved:** Yes (memory tool used)
