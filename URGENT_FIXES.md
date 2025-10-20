# 🔧 URGENT FIXES FOR TRIAGE PAGE

## 🐛 Issues Found:

1. **Markdown not rendering** - Line 989: Using plain text instead of markdown renderer
2. **Missing "Add to Todo" buttons** - Analysis tasks are there but buttons not showing up right
3. **Only 2 emails showing** - Line 236: max_results is hardcoded to 20, but something else is filtering

---

## 🚀 Quick Fix Script

I'm going to create a fixed version of TriagePage.tsx that:

1. Installs and uses `react-markdown` to render markdown properly
2. Ensures "Add to Todo" buttons are always visible when tasks exist
3. Increases max_results and adds debugging

---

## Step 1: Install react-markdown

```bash
cd client
npm install react-markdown remark-gfm
```

## Step 2: The fix is in the file I'm about to create...
