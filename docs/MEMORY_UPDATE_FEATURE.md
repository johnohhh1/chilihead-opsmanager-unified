# Agent Memory Update System

## Problem Fixed
AUBS wasn't updating its memory when you told it items were resolved. It would just record the conversation but keep showing "Pedro issue" as urgent in future chats.

## Solution
Added intelligent memory update system that:
1. **Detects corrections** - Recognizes when you're telling it something is done
2. **Updates memory** - Marks related items as `[RESOLVED]`
3. **Filters context** - Resolved items don't show up in future responses
4. **Tracks annotations** - Saves your notes about why it's resolved

## How It Works

### Automatic Detection
When you say things like:
- "the pedro issue was handled"
- "payroll is already done"
- "that's resolved"
- "update the memory that X was completed"

AUBS automatically:
1. Searches memory for related items (Pedro, payroll, etc.)
2. Marks them as `[RESOLVED]`
3. Adds your note as an annotation
4. Filters them out of future context

### Keywords That Trigger Updates
- "was handled"
- "already done"
- "not urgent"
- "resolved"
- "completed"
- "fixed"
- "update the memory"
- "mark as done"

### Topics It Recognizes
- Pedro
- Payroll
- Schedule
- Invoice
- (More can be added easily)

## API Endpoints

### Manual Update
```http
POST /api/operations-chat/mark-resolved
Content-Type: application/json

{
    "topic": "Pedro",
    "annotation": "Handled on Tuesday morning - called off issue resolved"
}
```

**Response:**
```json
{
    "success": true,
    "resolved_count": 3,
    "topic": "Pedro",
    "message": "Marked 3 memories related to 'Pedro' as resolved"
}
```

### Memory Status
```http
GET /api/operations-chat/memory-status
```

**Response:**
```json
{
    "total_active": 12,
    "total_resolved": 5,
    "by_agent": {
        "triage": [
            {
                "id": "abc-123",
                "summary": "Analyzed urgent email about Corrigo invoice",
                "created_at": "2025-01-12T09:00:00",
                "event_type": "email_analyzed"
            }
        ],
        "daily_brief": [...]
    },
    "resolved_items": [
        {
            "summary": "[RESOLVED] Analyzed email about Pedro call-off",
            "resolved_at": "2025-01-12T10:30:00"
        }
    ]
}
```

## Usage Examples

### In Chat (Automatic)

**You:**
> "the pedro issue was handled the very next day it wasn't even in today's emails"

**AUBS:**
> "Got it, marking the Pedro issue as resolved in my memory. I'll stop flagging it in future digests."

**Behind the scenes:**
- Searches memory for "Pedro"
- Finds 3 related items from email triage and daily digest
- Marks all as `[RESOLVED]`
- Adds annotation: "User update: the pedro issue was handled the very next day..."

### Manual API Call

```bash
curl -X POST http://localhost:8002/api/operations-chat/mark-resolved \
  -H "Content-Type: application/json" \
  -d '{"topic": "payroll", "annotation": "Hannah was paid on Tuesday"}'
```

### Check Status

```bash
curl http://localhost:8002/api/operations-chat/memory-status
```

## How Memory Updates Work

### Before Update
```
AGENT MEMORY (Last 48h):

TRIAGE Agent:
  - [Jan 12, 09:00 AM] Analyzed email about Pedro call-off
    🚨 Urgent: Coverage needed for dinner shift
  - [Jan 11, 04:00 PM] Analyzed email about payroll issue
    🚨 Urgent: Hannah hasn't been paid

DAILY_BRIEF Agent:
  - [Jan 12, 07:00 AM] Generated morning digest
    🚨 Urgent: Pedro, payroll issues flagged
```

### After Telling AUBS "Pedro was handled"
```
AGENT MEMORY (Last 48h - Active items only):

TRIAGE Agent:
  - [Jan 11, 04:00 PM] Analyzed email about payroll issue
    🚨 Urgent: Hannah hasn't been paid

DAILY_BRIEF Agent:
  - (No active items)
```

Pedro items are now filtered out because they're marked `[RESOLVED]`.

### In Database
The resolved items aren't deleted - they're marked:

```sql
summary: "[RESOLVED] Analyzed email about Pedro call-off"
context_data: {
    "annotations": [
        {
            "timestamp": "2025-01-12T10:30:00",
            "note": "User update: the pedro issue was handled the very next day",
            "status": "resolved"
        }
    ]
}
```

## New Service Methods

### `AgentMemoryService.mark_resolved()`
```python
from services.agent_memory import AgentMemoryService

# Mark by topic
resolved_count = AgentMemoryService.mark_resolved(
    db=db,
    summary_text="Pedro",
    annotation="Handled on Tuesday"
)

# Mark by email ID
resolved_count = AgentMemoryService.mark_resolved(
    db=db,
    email_id="thread_abc123",
    annotation="Issue resolved"
)
```

### `AgentMemoryService.annotate_memory()`
```python
# Annotate specific memories
updated = AgentMemoryService.annotate_memory(
    db=db,
    email_id="thread_abc123",
    annotation="User correction: This was resolved yesterday",
    status="resolved"
)
```

### `AgentMemoryService.get_coordination_context()` (Updated)
```python
# Get context without resolved items (default)
context = AgentMemoryService.get_coordination_context(
    db=db,
    hours=48,
    include_resolved=False  # Default
)

# Include resolved items if needed
context = AgentMemoryService.get_coordination_context(
    db=db,
    hours=48,
    include_resolved=True
)
```

## Configuration

### Adding More Topics

In [operations_chat.py:294-302](server/routes/operations_chat.py#L294-L302):

```python
# Look for key nouns/topics
topics = []
if 'pedro' in user_msg_lower:
    topics.append('Pedro')
if 'payroll' in user_msg_lower or 'pay' in user_msg_lower:
    topics.append('payroll')
# Add more topics here:
if 'inventory' in user_msg_lower:
    topics.append('inventory')
```

### Adding More Keywords

In [operations_chat.py:283](server/routes/operations_chat.py#L283):

```python
correction_keywords = [
    'was handled',
    'already done',
    'not urgent',
    'resolved',
    'completed',
    'fixed',
    'update the memory',
    'mark as done',
    # Add more here:
    'taken care of',
    'no longer an issue'
]
```

## Benefits

### 1. Accurate Context
AUBS won't keep telling you about resolved issues.

### 2. Clean Digests
Daily Brief only shows active items.

### 3. Audit Trail
All corrections are tracked with timestamps and notes.

### 4. Easy Corrections
Just tell AUBS naturally - it figures out what you mean.

### 5. Manual Control
API endpoint for explicit updates if needed.

## Testing

### 1. Chat Test
1. Go to Operations Chat
2. Say: "the pedro issue was handled"
3. Check backend logs: Should see "Marked N 'Pedro' memories as resolved"
4. Say: "What's urgent today?"
5. Pedro should NOT appear in response

### 2. API Test
```bash
# Mark something as resolved
curl -X POST http://localhost:8002/api/operations-chat/mark-resolved \
  -H "Content-Type: application/json" \
  -d '{"topic": "test", "annotation": "Testing memory update"}'

# Check status
curl http://localhost:8002/api/operations-chat/memory-status
```

### 3. Database Test
```sql
-- See resolved items
SELECT
    summary,
    context_data->'annotations'->-1->>'note' as last_note,
    created_at
FROM agent_memory
WHERE summary LIKE '%RESOLVED%'
ORDER BY created_at DESC;
```

## Technical Details

### Memory Record Structure
```python
AgentMemory:
    summary: "[RESOLVED] Original summary"  # Prefixed when resolved
    context_data: {
        "original_data": {...},
        "annotations": [
            {
                "timestamp": "2025-01-12T10:30:00",
                "note": "User correction",
                "status": "resolved"
            }
        ]
    }
```

### Resolution Flow
1. User says correction phrase
2. System detects keywords
3. Extracts topic (Pedro, payroll, etc.)
4. Queries `agent_memory` for matching summaries
5. Adds `[RESOLVED]` prefix to summary
6. Appends annotation to context_data
7. Commits changes
8. Future context queries filter out `[RESOLVED]` items

### Performance
- Only searches last 7 days
- ILIKE search on summary field (indexed)
- Updates are batched in single transaction
- No performance impact on chat responses

## Limitations

### Current Topic Detection
- Uses simple keyword matching
- Only recognizes predefined topics
- Case-insensitive

### Future Enhancements
1. **LLM-based extraction** - Let AI extract topics from natural language
2. **Fuzzy matching** - "payrol" matches "payroll"
3. **Entity linking** - Connect to actual email/task IDs
4. **Confidence scores** - "Did you mean Pedro call-off or Pedro schedule?"
5. **Undo** - "Actually, that's not resolved"

## Files Modified

1. ✅ [services/agent_memory.py](server/services/agent_memory.py) - Core memory update methods
2. ✅ [routes/operations_chat.py](server/routes/operations_chat.py) - Automatic detection + API endpoints

## Summary

Now when you tell AUBS something is done, it actually remembers! No more repeated warnings about resolved issues. The system is smart enough to understand natural corrections and keep its memory up-to-date.

**Test it:** Just say "update the memory that X was handled" and watch it work! 🚀
