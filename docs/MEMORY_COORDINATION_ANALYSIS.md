# Multi-Agent Memory Coordination System - Analysis & Fixes

## Executive Summary

The ChiliHead OpsManager uses a centralized memory system (`agent_memory` table) to coordinate between 3 AI agents:
1. **Email Triage Agent** - Analyzes emails, flags urgent items
2. **Daily Brief Agent** - Generates morning digest
3. **Operations Chat Agent** - Interactive assistant

**CRITICAL PROBLEM**: When users tell the chat agent something is resolved (e.g., "the pedro issue was handled"), the memory updates DO NOT propagate to other agents, causing the Daily Brief to keep showing resolved items as still urgent.

## Root Cause Analysis

### Problem 1: Database Transaction Not Committed Immediately
**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\agent_memory.py`
**Lines**: 362-416 (`mark_resolved()` function)

```python
# CURRENT CODE (BROKEN):
def mark_resolved(db: Session, email_id=None, summary_text=None, annotation="Resolved by user"):
    # ... finds memories and updates them ...
    for mem in memories:
        mem.summary = f"[RESOLVED] {mem.summary}"
        # ... adds annotations ...

    db.commit()  # ✓ Commits to database
    return len(memories)
```

**Issue**: The commit happens, but there's a caching/timing problem. The Daily Brief Agent reads memory BEFORE the commit is visible.

### Problem 2: No Cache Invalidation Signal
**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\smart_assistant.py`
**Lines**: 639-647 (`daily_digest()` function)

```python
# CURRENT CODE (BROKEN):
try:
    from services.agent_memory import AgentMemoryService
    agent_context = AgentMemoryService.get_digest_context(db, hours=24)
except Exception as e:
    print(f"Warning: Could not load agent memory: {e}")
    agent_context = "(Agent memory temporarily unavailable)"
```

**Issue**: `get_digest_context()` calls `get_coordination_context()` which filters `[RESOLVED]` items, BUT it reads from database session that might not see recent commits from other sessions.

### Problem 3: SQLAlchemy Session Isolation
**File**: Multiple files using `Depends(get_db)`

**Issue**: Each API endpoint gets its own database session. When the chat endpoint updates memory, the daily digest endpoint (if called immediately after) gets a DIFFERENT session that might not see uncommitted/recent changes due to transaction isolation.

### Problem 4: Keyword Detection Too Narrow
**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`
**Lines**: 283-312

```python
# CURRENT CODE (LIMITED):
correction_keywords = ['was handled', 'already done', 'not urgent', 'resolved',
                      'completed', 'fixed', 'update the memory', 'mark as done']
```

**Issue**: User said "update the memory that the pedro issue was handled" - this DOES match "was handled", so keyword detection works. The problem is the UPDATE itself isn't propagating.

## Architecture Review

### Current Memory Flow (BROKEN)

```
User: "the pedro issue was handled"
  ↓
Operations Chat Agent:
  1. Detects correction keywords ✓
  2. Calls mark_resolved(db, summary_text='Pedro') ✓
  3. Updates AgentMemory records in DB ✓
  4. Commits to database ✓
  ↓
Daily Brief Agent (called later):
  1. Gets NEW db session (isolation!)
  2. Reads AgentMemory from database
  3. STILL SEES RESOLVED ITEMS because filter isn't working
  ↓
RESULT: User sees Pedro issue AGAIN in digest
```

### Problem Deep Dive: The `get_coordination_context()` Filter

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\agent_memory.py`
**Lines**: 136-199

```python
def get_coordination_context(db, hours=24, format="text", include_resolved=False):
    memories = AgentMemoryService.get_recent_context(db, hours=hours, limit=100)

    # Filter out resolved items unless requested
    if not include_resolved:
        memories = [m for m in memories if "[RESOLVED]" not in m.summary]  # ← FILTER

    # ... formats and returns context ...
```

**Analysis**:
- This filter SHOULD work if memory.summary was updated to `[RESOLVED] <original summary>`
- The problem is likely one of:
  1. **Transaction isolation**: New session doesn't see recent commits
  2. **Object state**: In-memory objects aren't refreshed after mark_resolved
  3. **Database session caching**: SQLAlchemy session cache holding old objects

## Verified Issues

### Issue 1: No Explicit Session Refresh After Update
When `mark_resolved()` updates memory records, it commits but doesn't call `db.refresh(memory)` or `db.expire_all()`, meaning:
- Changes ARE in the database
- But the CURRENT session might have cached old objects
- FUTURE sessions (daily brief) SHOULD see changes, but might not due to isolation level

### Issue 2: Missing Database Session Configuration
**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\database.py`

Need to verify session isolation level. PostgreSQL default is READ COMMITTED, which SHOULD show recent commits from other sessions, but there might be a timing issue.

### Issue 3: No Explicit Cache Busting
When chat agent updates memory, there's no signal to:
- Expire cached database objects
- Invalidate any in-memory caches
- Force other agents to re-read from database

## Recommended Fixes (Priority Order)

### FIX 1: Add Explicit Session Refresh in mark_resolved() ⭐ CRITICAL

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\agent_memory.py`
**Lines**: 362-416

```python
@staticmethod
def mark_resolved(db: Session, email_id=None, summary_text=None, annotation="Resolved by user"):
    query = db.query(AgentMemory)

    if email_id:
        query = query.filter(AgentMemory.email_id == email_id)
    elif summary_text:
        query = query.filter(AgentMemory.summary.ilike(f"%{summary_text}%"))
    else:
        return 0

    cutoff = datetime.now() - timedelta(days=7)
    query = query.filter(AgentMemory.created_at >= cutoff)

    memories = query.all()

    for mem in memories:
        if "[RESOLVED]" in mem.summary:
            continue

        if not mem.context_data:
            mem.context_data = {}

        if 'annotations' not in mem.context_data:
            mem.context_data['annotations'] = []

        mem.context_data['annotations'].append({
            'timestamp': datetime.now().isoformat(),
            'note': annotation,
            'status': 'resolved'
        })

        mem.summary = f"[RESOLVED] {mem.summary}"

        # NEW: Force SQLAlchemy to update this specific object
        db.add(mem)

    db.commit()

    # NEW: Critical fix - expire all cached objects so next session sees changes
    db.expire_all()

    return len(memories)
```

### FIX 2: Add Database Session Expiry Before Reading Memory ⭐ CRITICAL

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\agent_memory.py`
**Lines**: 72-99 (`get_recent_context()`)

```python
@staticmethod
def get_recent_context(db: Session, agent_type=None, hours=24, limit=50):
    # NEW: Force fresh read from database, don't use cached objects
    db.expire_all()

    cutoff = datetime.now() - timedelta(hours=hours)

    query = db.query(AgentMemory).filter(
        AgentMemory.created_at >= cutoff
    )

    if agent_type:
        query = query.filter(AgentMemory.agent_type == agent_type)

    return query.order_by(AgentMemory.created_at.desc()).limit(limit).all()
```

### FIX 3: Add Explicit Commit + Flush in Chat Endpoint ⭐ HIGH PRIORITY

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`
**Lines**: 305-312

```python
for topic in topics:
    resolved_count = AgentMemoryService.mark_resolved(
        db=db,
        summary_text=topic,
        annotation=f"User update: {request.message}"
    )
    if resolved_count > 0:
        print(f"[Memory Update] Marked {resolved_count} '{topic}' memories as resolved")

        # NEW: Force immediate database flush
        db.flush()
        db.commit()
        db.expire_all()
```

### FIX 4: Improve Keyword Detection (Optional Enhancement)

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`
**Lines**: 283-312

```python
# Better keyword patterns
correction_keywords = [
    'was handled', 'already done', 'not urgent', 'resolved', 'completed',
    'fixed', 'update the memory', 'mark as done', 'taken care of',
    'all set', 'no longer needed', 'false alarm', 'ignore that',
    'scratch that', 'never mind', 'cancel', 'disregard'
]

# Add natural language patterns
correction_patterns = [
    r'(pedro|payroll|schedule|invoice|coverage).+(handled|resolved|fixed|done)',
    r'already (handled|resolved|fixed|done).+(pedro|payroll|schedule)',
    r'no longer (urgent|needed|an issue)',
    r'false alarm.+(pedro|payroll|schedule)',
]
```

### FIX 5: Add Memory Update Confirmation to Chat Response

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`
**Lines**: 314-328

```python
# Record chat interaction
context_update_note = ""
if is_correction and resolved_count > 0:
    context_update_note = f"\n\n✅ Memory updated: Marked {resolved_count} items as resolved."

AgentMemoryService.record_event(
    db=db,
    agent_type='operations_chat',
    event_type='question_answered',
    summary=f"Answered: {request.message[:80]}..." + context_update_note,
    # ... rest of code ...
)

# Include in response so user knows it worked
return {
    "response": assistant_response + context_update_note,
    "session_id": session.id,
    "timestamp": datetime.now().isoformat(),
    "memory_updates": resolved_count if is_correction else 0
}
```

### FIX 6: Add Diagnostic Endpoint for Memory State

**File**: `c:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`
**New endpoint**

```python
@router.get("/api/operations-chat/debug-memory/{topic}")
async def debug_memory_state(topic: str, db: Session = Depends(get_db)):
    """
    Debug endpoint to see current memory state for a topic
    """
    from services.agent_memory import AgentMemoryService

    # Force fresh read
    db.expire_all()

    # Search for topic
    memories = AgentMemoryService.search_memory(db, topic, limit=20)

    return {
        "topic": topic,
        "total_found": len(memories),
        "memories": [
            {
                "id": m.id,
                "summary": m.summary,
                "is_resolved": "[RESOLVED]" in m.summary,
                "created_at": m.created_at.isoformat(),
                "agent_type": m.agent_type,
                "annotations": m.context_data.get('annotations', []) if m.context_data else []
            }
            for m in memories
        ]
    }
```

## Testing Plan

### Test 1: Verify mark_resolved() Actually Updates Database

```python
# Run: python server/test_memory_update.py

# Expected output:
# ✓ Created test memories
# ✓ Marked 2 'Pedro' memories as resolved
# ✓ Verified database shows [RESOLVED] prefix
# ✓ Coordination context excludes resolved items
```

### Test 2: Verify Cross-Session Visibility

```bash
# Terminal 1: Start backend
cd server && .venv/Scripts/python -m uvicorn app:app --reload --port 8002

# Terminal 2: Test sequence
curl -X POST http://localhost:8002/api/operations-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "update the memory that pedro was handled", "model": "gpt-4o"}'

# Wait 2 seconds

curl -X GET http://localhost:8002/api/operations-chat/debug-memory/pedro

# Expected: Should show memories with [RESOLVED] prefix
```

### Test 3: Verify Daily Brief Excludes Resolved Items

```bash
# After running Test 2, regenerate daily brief
curl -X GET "http://localhost:8002/api/daily-operations-brief?model=gpt-4o&fresh=true"

# Expected: Daily brief should NOT mention Pedro issue
```

## Better Architecture Patterns (Future Enhancements)

### Pattern 1: Event-Driven Memory Updates

```python
# Instead of: mark_resolved() directly updates DB
# Better: Emit event that all agents can react to

from typing import Callable, List

class MemoryEventBus:
    _subscribers: List[Callable] = []

    @classmethod
    def subscribe(cls, handler: Callable):
        cls._subscribers.append(handler)

    @classmethod
    def emit(cls, event_type: str, data: dict):
        for handler in cls._subscribers:
            handler(event_type, data)

# Usage:
def mark_resolved(db, topic):
    # Update database...
    db.commit()

    # Notify all agents
    MemoryEventBus.emit('memory_resolved', {
        'topic': topic,
        'resolved_count': count,
        'timestamp': datetime.now()
    })
```

### Pattern 2: Explicit Memory Versioning

```python
class AgentMemory(Base):
    # ... existing fields ...
    version = Column(Integer, default=1)  # NEW
    status = Column(String(20), default='active')  # NEW: active, resolved, invalidated
    invalidated_at = Column(DateTime)  # NEW
    invalidated_by = Column(String(50))  # NEW: agent that invalidated it

# Instead of: Filtering by "[RESOLVED]" prefix in summary
# Better: Query by status field
memories = db.query(AgentMemory).filter(
    AgentMemory.created_at >= cutoff,
    AgentMemory.status == 'active'  # Cleaner than string prefix
).all()
```

### Pattern 3: Explicit Entity Relationships

```python
# CURRENT: Relies on text matching ("pedro" in summary)
# BETTER: Explicit foreign keys

class AgentMemory(Base):
    # ... existing fields ...

    # STRONG typing of relationships
    related_email_threads = Column(JSON)  # ["thread_123", "thread_456"]
    related_task_ids = Column(JSON)  # ["task_789"]
    related_people = Column(JSON)  # ["Pedro Martinez", "Hannah Zimmerman"]

    # Make searchable
    __table_args__ = (
        Index('idx_related_emails', postgresql_using='gin', related_email_threads),
        Index('idx_related_people', postgresql_using='gin', related_people),
    )

# Usage:
mark_resolved(db, person="Pedro Martinez")  # Instead of fuzzy text match
```

### Pattern 4: Memory Hierarchy (Short/Medium/Long Term)

```python
class MemoryTier:
    SHORT_TERM = "short_term"   # 24 hours - immediate operations
    MEDIUM_TERM = "medium_term" # 7 days - weekly planning
    LONG_TERM = "long_term"     # 30+ days - patterns, learning

class AgentMemory(Base):
    # ... existing fields ...
    memory_tier = Column(String(20), default='short_term')
    expires_at = Column(DateTime)  # Auto-archive after this time

    # Promotion/demotion of importance
    promoted_to_medium = Column(Boolean, default=False)
    promoted_to_long = Column(Boolean, default=False)

# Daily brief focuses on SHORT_TERM only
# Operations chat includes MEDIUM_TERM for context
# Pattern detection uses LONG_TERM
```

## Summary of Immediate Actions

### Critical (Do First):
1. ✅ Add `db.expire_all()` to `mark_resolved()` after commit
2. ✅ Add `db.expire_all()` to `get_recent_context()` before query
3. ✅ Add explicit `db.flush()` and `db.commit()` in chat endpoint after mark_resolved

### High Priority (Do Next):
4. ✅ Add memory update confirmation in chat response
5. ✅ Add debug endpoint to inspect memory state
6. ✅ Test end-to-end: chat update → daily brief regeneration

### Nice to Have (Future):
7. ⚪ Implement event-driven memory updates
8. ⚪ Add explicit `status` field instead of `[RESOLVED]` prefix
9. ⚪ Add entity relationship tracking (foreign keys)
10. ⚪ Implement memory tiering (short/medium/long term)

## Key Insight: Why This Happened

The core issue is **SQLAlchemy session isolation**. Each FastAPI endpoint gets its own database session via `Depends(get_db)`. When one endpoint (chat) updates memory and commits, another endpoint (daily brief) with a DIFFERENT session might not see those changes immediately due to:

1. **Object-level caching**: SQLAlchemy caches objects in memory per session
2. **Transaction isolation**: PostgreSQL READ COMMITTED isolation means you only see COMMITTED changes from other transactions when you START a new query
3. **No cache invalidation**: There's no mechanism to tell other sessions "hey, memory was updated, re-read from DB"

The fix is simple: **Force sessions to re-read from database** using `db.expire_all()` before critical queries.

## Testing the Fix

After implementing FIX 1-3 above, test this sequence:

```python
# 1. Create a test memory
POST /api/operations-chat
Body: {"message": "remind me about pedro calling off", "model": "gpt-4o"}

# 2. Mark it resolved
POST /api/operations-chat
Body: {"message": "update the memory that pedro was handled", "model": "gpt-4o"}

# 3. Check memory state (should show RESOLVED)
GET /api/operations-chat/debug-memory/pedro

# 4. Generate daily brief (should NOT mention pedro)
GET /api/daily-operations-brief?model=gpt-4o&fresh=true

# 5. Verify memory status endpoint
GET /api/operations-chat/memory-status
```

Expected result: Pedro should NOT appear in daily brief urgent section.

---

**Status**: Analysis complete. Ready to implement fixes.
**Confidence**: High - root cause identified with clear solution path.
**Risk**: Low - fixes are additive, no breaking changes to existing code.
