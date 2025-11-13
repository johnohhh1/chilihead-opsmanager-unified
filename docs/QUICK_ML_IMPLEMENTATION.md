# Quick Implementation: Intelligent Memory Updates

**Time Required:** 2-3 hours
**Cost:** ~$0.60/month in LLM calls
**Complexity:** Low

---

## TL;DR

Replace hardcoded topic matching with LLM-based extraction. No vector embeddings needed.

**Before:**
```python
if 'pedro' in user_msg_lower:
    topics.append('Pedro')
```

**After:**
```python
topics = extract_topics_llm(user_message)  # LLM figures it out
```

---

## Step 1: Create Memory Intelligence Service (30 min)

Create `C:\Users\John\Desktop\chilihead-opsmanager-unified\server\services\memory_intelligence.py`:

```python
"""
Intelligent memory update using LLM
Replaces hardcoded keyword matching
"""

import json
from typing import List, Tuple
from sqlalchemy.orm import Session
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_topics_llm(user_message: str) -> List[str]:
    """
    Extract topics using GPT-4o-mini (fast, cheap)

    Examples:
        "pedro was handled" -> ["Pedro"]
        "the payroll thing is done" -> ["payroll"]
        "that corrigo invoice" -> ["Corrigo", "invoice"]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Extract key topics from user messages about restaurant operations.

Return JSON: {"topics": ["topic1", "topic2"]}

Examples:
- "pedro was handled" -> {"topics": ["Pedro"]}
- "payroll is done" -> {"topics": ["payroll"]}
- "the corrigo invoice got paid" -> {"topics": ["Corrigo", "invoice"]}
- "schedule issue resolved" -> {"topics": ["schedule"]}

Only extract clear topics (people, systems, issues). Ignore filler words."""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.3,
            max_tokens=100,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        topics = result.get("topics", [])

        print(f"[Topic Extraction] '{user_message}' -> {topics}")
        return topics

    except Exception as e:
        print(f"[Topic Extraction Error] {e}")
        # Fallback: extract capitalized words
        import re
        words = re.findall(r'\b[A-Z][a-z]+\b', user_message)
        return words if words else []


def confirm_resolution_llm(
    user_message: str,
    candidate_summaries: List[str]
) -> List[int]:
    """
    Ask LLM which memories should be marked as resolved

    Returns:
        List of indices (0-based) to mark as resolved
    """

    if not candidate_summaries:
        return []

    summaries_text = "\n".join([
        f"{i+1}. {summary}"
        for i, summary in enumerate(candidate_summaries)
    ])

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Determine which memories should be marked as resolved based on user's message.

Return JSON: {"resolved": [1, 3], "reasoning": "why"}

Be CONSERVATIVE:
- Only mark items if clearly related
- Consider context (question vs statement)
- "is X resolved?" -> DON'T mark resolved (it's a question)
- "X was handled" -> DO mark resolved (it's a statement)

Examples:
User: "pedro was handled"
Memories: 1. Pedro call-off issue, 2. Payroll problem
Response: {"resolved": [1], "reasoning": "User confirms Pedro issue handled"}

User: "is pedro resolved?"
Response: {"resolved": [], "reasoning": "User is asking, not confirming"}"""
                },
                {
                    "role": "user",
                    "content": f"""User said: "{user_message}"

Which memories should be marked as resolved?

{summaries_text}

Return decision as JSON."""
                }
            ],
            temperature=0.3,
            max_tokens=150,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        indices = [idx - 1 for idx in result.get("resolved", [])]  # Convert to 0-based

        print(f"[Resolution Check] Confirmed {len(indices)} memories")
        print(f"  Reasoning: {result.get('reasoning', 'N/A')}")

        return indices

    except Exception as e:
        print(f"[Resolution Check Error] {e}")
        return []


def intelligent_memory_update(
    db: Session,
    user_message: str
) -> dict:
    """
    Main function: Extract topics, find memories, confirm, update

    Returns:
        {
            "topics": ["Pedro"],
            "candidates_found": 3,
            "memories_updated": 2,
            "success": True
        }
    """

    from services.agent_memory import AgentMemoryService

    # Step 1: Extract topics
    topics = extract_topics_llm(user_message)

    if not topics:
        return {
            "success": False,
            "error": "No clear topics found",
            "topics": []
        }

    # Step 2: Search for candidate memories
    candidates = []
    for topic in topics:
        matches = AgentMemoryService.search_memory(db, topic, limit=10)
        candidates.extend(matches)

    # Remove duplicates
    unique_candidates = list({m.id: m for m in candidates}.values())

    if not unique_candidates:
        return {
            "success": False,
            "error": f"No memories found for: {topics}",
            "topics": topics
        }

    # Step 3: LLM confirms which to resolve
    summaries = [m.summary for m in unique_candidates]
    confirmed_indices = confirm_resolution_llm(user_message, summaries)

    if not confirmed_indices:
        return {
            "success": False,
            "error": "LLM did not confirm any matches",
            "topics": topics,
            "candidates_found": len(unique_candidates)
        }

    # Step 4: Mark confirmed memories as resolved
    updated_count = 0
    for idx in confirmed_indices:
        if 0 <= idx < len(unique_candidates):
            mem = unique_candidates[idx]
            AgentMemoryService.mark_resolved(
                db=db,
                summary_text=mem.summary[:50],  # Use summary snippet as search
                annotation=f"User confirmation: {user_message}"
            )
            updated_count += 1

    return {
        "success": True,
        "topics": topics,
        "candidates_found": len(unique_candidates),
        "memories_updated": updated_count
    }
```

---

## Step 2: Update Operations Chat (10 min)

Edit `C:\Users\John\Desktop\chilihead-opsmanager-unified\server\routes\operations_chat.py`:

Find lines 278-313 (the correction detection block) and replace with:

```python
        # Record chat interaction to agent memory
        try:
            from services.agent_memory import AgentMemoryService
            from services.memory_intelligence import intelligent_memory_update

            # Check if user is correcting/updating memory
            correction_keywords = [
                'was handled', 'already done', 'not urgent', 'resolved',
                'completed', 'fixed', 'update the memory', 'mark as done',
                'taken care of', 'no longer an issue'
            ]

            user_msg_lower = request.message.lower()
            is_correction = any(keyword in user_msg_lower for keyword in correction_keywords)

            if is_correction:
                # Use intelligent LLM-based memory update
                result = intelligent_memory_update(db, request.message)

                if result["success"]:
                    print(f"[Smart Memory Update] Success!")
                    print(f"  Topics: {result['topics']}")
                    print(f"  Candidates: {result['candidates_found']}")
                    print(f"  Updated: {result['memories_updated']} memories")
                else:
                    print(f"[Smart Memory Update] {result.get('error', 'Failed')}")

            # Record the chat interaction itself
            AgentMemoryService.record_event(
                db=db,
                agent_type='operations_chat',
                event_type='question_answered',
                summary=f"Answered: {request.message[:80]}...",
                context_data={
                    'user_question': request.message,
                    'assistant_response': assistant_response[:500],
                    'model_used': request.model,
                    'was_correction': is_correction,
                    'memory_update_result': result if is_correction else None
                },
                key_findings={},
                model_used=request.model,
                confidence_score=80
            )
        except Exception as mem_error:
            print(f"Warning: Failed to record chat to agent memory: {mem_error}")
```

---

## Step 3: Test It (10 min)

Create `C:\Users\John\Desktop\chilihead-opsmanager-unified\server\test_smart_memory.py`:

```python
"""
Test intelligent memory updates
"""

from database import SessionLocal
from services.agent_memory import AgentMemoryService
from services.memory_intelligence import intelligent_memory_update
from datetime import datetime
import json

db = SessionLocal()

# Create test memory
print("Creating test memory...")
mem = AgentMemoryService.record_event(
    db=db,
    agent_type='triage',
    event_type='email_analyzed',
    summary='Analyzed email about Pedro call-off for dinner shift',
    key_findings={'priority': 'urgent'},
    model_used='gpt-4o',
    confidence_score=90
)
print(f"Created memory: {mem.summary}\n")

# Test 1: Simple correction
print("=" * 80)
print("TEST 1: Simple correction")
print("=" * 80)
result = intelligent_memory_update(
    db,
    "pedro was handled yesterday"
)
print(json.dumps(result, indent=2))

# Verify memory was updated
updated = db.query(AgentMemory).filter(AgentMemory.id == mem.id).first()
print(f"\nMemory after update: {updated.summary}")
print(f"Resolved: {'[RESOLVED]' in updated.summary}")

# Test 2: Question (should NOT resolve)
print("\n" + "=" * 80)
print("TEST 2: Question (should NOT resolve)")
print("=" * 80)

# Create another test memory
mem2 = AgentMemoryService.record_event(
    db=db,
    agent_type='triage',
    event_type='email_analyzed',
    summary='Analyzed email about payroll issue with Hannah',
    key_findings={'priority': 'urgent'},
    model_used='gpt-4o',
    confidence_score=85
)

result2 = intelligent_memory_update(
    db,
    "is the payroll thing resolved?"
)
print(json.dumps(result2, indent=2))

# Test 3: Ambiguous
print("\n" + "=" * 80)
print("TEST 3: Ambiguous reference")
print("=" * 80)

result3 = intelligent_memory_update(
    db,
    "that's done now"
)
print(json.dumps(result3, indent=2))

db.close()
print("\n✅ Tests complete!")
```

Run it:
```bash
cd C:\Users\John\Desktop\chilihead-opsmanager-unified\server
.venv\Scripts\python test_smart_memory.py
```

Expected output:
```
Creating test memory...
Created memory: Analyzed email about Pedro call-off for dinner shift

================================================================================
TEST 1: Simple correction
================================================================================
[Topic Extraction] 'pedro was handled yesterday' -> ['Pedro']
[Resolution Check] Confirmed 1 memories
  Reasoning: User confirms Pedro issue handled
[Memory System] Marked 1 memories as resolved for 'Analyzed email about Pedro'
{
  "success": true,
  "topics": ["Pedro"],
  "candidates_found": 1,
  "memories_updated": 1
}

Memory after update: [RESOLVED] Analyzed email about Pedro call-off for dinner shift
Resolved: True

================================================================================
TEST 2: Question (should NOT resolve)
================================================================================
[Topic Extraction] 'is the payroll thing resolved?' -> ['payroll']
[Resolution Check] Confirmed 0 memories
  Reasoning: User is asking, not confirming
{
  "success": false,
  "error": "LLM did not confirm any matches",
  "topics": ["payroll"],
  "candidates_found": 1
}

================================================================================
TEST 3: Ambiguous reference
================================================================================
[Topic Extraction] 'that's done now' -> []
{
  "success": false,
  "error": "No clear topics found",
  "topics": []
}

✅ Tests complete!
```

---

## Step 4: Test in Real Chat (5 min)

1. Start backend:
```bash
cd C:\Users\John\Desktop\chilihead-opsmanager-unified
start_unified.bat
```

2. Open Operations Chat (http://localhost:3001/chat)

3. Test phrases:
- "pedro was handled" → Should update memory
- "is pedro resolved?" → Should NOT update (it's a question)
- "the payroll thing is done" → Should update
- "mark the invoice as resolved" → Should update

4. Check backend logs for:
```
[Smart Memory Update] Success!
  Topics: ['Pedro']
  Candidates: 1
  Updated: 1 memories
```

---

## Step 5: Verify Next Day (1 min)

Next morning when Daily Brief generates:
- Resolved items should NOT appear
- Only active items show up

---

## Cost Analysis

**LLM Calls per Correction:**
- Topic extraction: 1 call to gpt-4o-mini (~100 tokens) = $0.0001
- Confirmation: 1 call to gpt-4o-mini (~200 tokens) = $0.0002
- **Total per correction: ~$0.0003**

**Monthly estimate:**
- 2-3 corrections per day = 60-90/month
- Cost: 60 × $0.0003 = **$0.018/month** (~2 cents)

**Comparison:**
- Current system: $0 but doesn't work
- This solution: $0.02/month and works reliably
- Vector embeddings: $5-10/month setup + complexity

---

## Error Handling

The code includes fallbacks:

1. **LLM fails to extract topics** → Falls back to capitalized words
2. **No candidates found** → Returns helpful error message
3. **LLM doesn't confirm any** → Doesn't update (conservative)
4. **OpenAI API down** → Logs error, continues without update

---

## Future Enhancements (Optional)

### 1. Add Fuzzy Matching (30 min)
```python
from difflib import SequenceMatcher

def fuzzy_search(db, topic, threshold=0.7):
    """Search with typo tolerance"""
    recent = AgentMemoryService.get_recent_context(db, hours=168)

    matches = []
    for mem in recent:
        similarity = SequenceMatcher(None, topic.lower(), mem.summary.lower()).ratio()
        if similarity >= threshold:
            matches.append((mem, similarity))

    return sorted(matches, key=lambda x: x[1], reverse=True)
```

### 2. Add Confidence Display (15 min)
```python
# In chat response, tell user:
f"Updated {count} memories about {topics} with {confidence*100:.0f}% confidence"
```

### 3. Add Undo Capability (30 min)
```python
@router.post("/api/operations-chat/undo-resolution")
async def undo_resolution(memory_id: str, db: Session = Depends(get_db)):
    """Undo a resolution if user made a mistake"""
    memory = db.query(AgentMemory).filter(AgentMemory.id == memory_id).first()
    if memory and "[RESOLVED]" in memory.summary:
        memory.summary = memory.summary.replace("[RESOLVED] ", "")
        db.commit()
        return {"success": True}
```

---

## Troubleshooting

### Issue: LLM not extracting topics
**Check:** Backend logs for "[Topic Extraction]"
**Fix:** Verify OpenAI API key is set

### Issue: No memories found
**Check:** Are there recent memories?
```bash
cd server
.venv\Scripts\python -c "
from database import SessionLocal
from models import AgentMemory
db = SessionLocal()
print(f'Total memories: {db.query(AgentMemory).count()}')
"
```

### Issue: LLM not confirming matches
**Check:** Backend logs for "[Resolution Check] Reasoning: ..."
**Debug:** Add `print(summaries_text)` before LLM call to see what it's evaluating

### Issue: Updates not persisting
**Check:** Database commit is happening
**Fix:** Verify `db.commit()` and `db.expire_all()` in mark_resolved()

---

## Monitoring

Add to Daily Brief or admin dashboard:

```python
# Show memory update stats
@router.get("/api/agent-memory/stats")
async def memory_stats(db: Session = Depends(get_db)):
    """Show memory system statistics"""
    from datetime import datetime, timedelta

    cutoff_24h = datetime.now() - timedelta(hours=24)
    cutoff_7d = datetime.now() - timedelta(days=7)

    memories_24h = db.query(AgentMemory).filter(
        AgentMemory.created_at >= cutoff_24h
    ).count()

    resolved_24h = db.query(AgentMemory).filter(
        AgentMemory.created_at >= cutoff_24h,
        AgentMemory.summary.like('%RESOLVED%')
    ).count()

    return {
        "last_24h": {
            "total": memories_24h,
            "resolved": resolved_24h,
            "active": memories_24h - resolved_24h
        }
    }
```

---

## Summary

**What you're getting:**
- Intelligent topic extraction (handles "pedro" and "the P situation")
- LLM confirmation (won't mark questions as resolved)
- Conservative by default (when in doubt, doesn't update)
- Low cost (~2 cents/month)
- Easy to debug (see exact reasoning in logs)

**What you're NOT getting:**
- Vector embeddings (don't need them yet)
- Semantic similarity search (ILIKE is fine for 50 memories)
- Complex infrastructure (just add one file + small edit)

**Time investment:** 2-3 hours
**Monthly cost:** $0.02
**Maintenance:** None (uses existing OpenAI API)

---

**Ready to implement?** Follow Steps 1-4 above. Should take 1-2 hours total.
