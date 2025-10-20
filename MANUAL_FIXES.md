# 🔧 TRIAGE PAGE FIXES - Apply These Changes

## Issue: Markdown not rendering, tasks not showing, only 2 emails

---

## FIX 1: Add markdown import at the TOP of TriagePage.tsx

**Find this line (around line 1-10):**
```typescript
'use client';

import { useState, useEffect } from 'react';
import { 
  RefreshCw, Calendar, AlertTriangle, Clock, 
  ChevronDown, ChevronUp, Plus, Brain, Zap,
  Mail, User, Tag, ArrowRight, Sparkles, MessageSquare,
  Phone, Link, CheckCircle, Check, X, Filter, Eye, EyeOff,
  Settings, Trash2
} from 'lucide-react';
```

**Add these TWO lines right after the lucide-react import:**
```typescript
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
```

---

## FIX 2: Change max_results from 20 to 100

**Find this line (around line 236):**
```typescript
max_results: '20',
```

**Change it to:**
```typescript
max_results: '100',
```

---

## FIX 3: Replace the markdown rendering section

**Find this section (around line 989):**
```typescript
<div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
  {linkifyText(analysis.analysis)}
</div>
```

**Replace it with:**
```typescript
<div className="text-gray-800 leading-relaxed prose prose-sm max-w-none">
  <ReactMarkdown remarkPlugins={[remarkGfm]}>
    {analysis.analysis || 'No analysis available'}
  </ReactMarkdown>
</div>
```

---

## FIX 4: Add debug logging for tasks

**Find this section (around line 997):**
```typescript
{/* Extracted Actions */}
{analysis.tasks && analysis.tasks.length > 0 && (
```

**Add console.log RIGHT BEFORE that line:**
```typescript
{/* Debug: Log tasks to console */}
{console.log('Analysis tasks:', analysis.tasks)}

{/* Extracted Actions */}
{analysis.tasks && analysis.tasks.length > 0 && (
```

---

## After Making Changes:

1. **Save the file**
2. **Restart the frontend:**
   ```bash
   # Stop the frontend (Ctrl+C)
   # Then restart:
   cd client
   npm run dev
   ```

3. **Test it:**
   - Refresh the page (F12 → Console tab open)
   - Click "AI Analysis" on an email
   - Check console for: `Analysis tasks: [...]`
   - See if markdown renders (bold, bullets work)
   - Check if tasks show up

4. **Tell me:**
   - What does the console say for "Analysis tasks"?
   - Is markdown rendering now?
   - Do you see more than 2 emails?

---

## If you want me to do it:

Just say "do it for me" and I'll create the complete fixed file and replace it.
