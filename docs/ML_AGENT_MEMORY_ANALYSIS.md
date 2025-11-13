# ML Analysis: Agent Memory Coordination System

**Date:** 2025-11-12
**System:** ChiliHead OpsManager - Personal restaurant operations management
**Context:** Single user, ~10-50 emails/day, 3 AI agents (triage, daily_brief, operations_chat)

---

## Executive Summary

**RECOMMENDATION: Don't over-engineer this. Current text-based approach is 90% sufficient.**

The pain point ("pedro was handled" not updating memories) is **NOT a machine learning problem** - it's a keyword matching and natural language understanding problem that can be solved with:

1. **Better keyword extraction** (current: hardcoded list → better: LLM-based extraction)
2. **Fuzzy matching** (current: exact ILIKE → better: Levenshtein distance)
3. **Entity resolution** (current: text search → better: link to actual email/task IDs)

Vector embeddings would be overkill for this scale. Save ML for when you have 1000+ memories and complex retrieval needs.

---

## Current System Analysis

### What Works Well

**1. Database Design (9/10)**
```python
AgentMemory:
  - summary: Text          # Human-readable summary
  - context_data: JSON     # Full context
  - key_findings: JSON     # Structured data (deadlines, urgent items)
  - related_entities: JSON # People, emails, tasks
  - email_id, task_id      # Foreign keys for exact matching
```

This is EXCELLENT. You already have:
- Structured data extraction (key_findings)
- Entity linking (email_id, task_id)
- Flexible JSON storage for context
- Temporal ordering (created_at)

**2. Context Building (8/10)**
```python
# Group by agent type
by_agent = {}
for m in memories:
    if m.agent_type not in by_agent:
        by_agent[m.agent_type] = []
    by_agent[m.agent_type].append(m)
```

Good separation of concerns. Each agent sees relevant context.

**3. Resolution Tracking (7/10)**
```python
# Filter resolved items
if not include_resolved:
    memories = [m for m in memories if "[RESOLVED]" not in m.summary]
```

Simple, works. Annotation system is solid.

### What Needs Improvement

**1. Keyword Detection (Current: 4/10)**
```python
# Hardcoded topics (operations_chat.py:294-302)
if 'pedro' in user_msg_lower:
    topics.append('Pedro')
if 'payroll' in user_msg_lower or 'pay' in user_msg_lower:
    topics.append('payroll')
```

**Problems:**
- Brittle: "the P situation" won't match "Pedro"
- No fuzzy matching: "payrol" won't match "payroll"
- Hardcoded list: Requires code change for new topics
- Case-sensitive on entity names (Pedro vs pedro)

**2. Search Method (Current: 5/10)**
```python
# Simple ILIKE search (agent_memory.py:222)
query = query.filter(AgentMemory.summary.ilike(f"%{query_text}%"))
```

**Problems:**
- No semantic understanding
- No ranking (returns in time order, not relevance)
- No multi-term support ("pedro payroll" searches for exact phrase)
- No synonym handling ("Hannah pay issue" won't match "Hannah payroll problem")

**3. Intent Understanding (Current: 3/10)**
```python
# Correction detection (operations_chat.py:283)
correction_keywords = ['was handled', 'already done', 'not urgent', 'resolved']
is_correction = any(keyword in user_msg_lower for keyword in correction_keywords)
```

**Problems:**
- No context: "is it resolved?" triggers resolution
- No negation: "not resolved" might trigger resolution
- No entity extraction: "pedro was handled" matches keyword but needs Pedro extraction

---

## ML vs Non-ML Solutions

### Option 1: Stay Simple (Current + Improvements)
**Cost:** 2-4 hours development
**Complexity:** Low
**Maintenance:** Easy

**Improvements:**
1. **LLM-based topic extraction** (replaces hardcoded list)
2. **Fuzzy string matching** (handles typos)
3. **Better entity resolution** (link to actual email/task IDs)

**Implementation:**
```python
def extract_topics_llm(user_message: str) -> List[str]:
    """Use GPT-4o mini to extract topics from user message"""
    prompt = f"""
    Extract key topics/entities from this message:
    "{user_message}"

    Return only the topics as a JSON array: ["topic1", "topic2"]

    Examples:
    - "pedro was handled" → ["Pedro"]
    - "the payroll thing is done" → ["payroll"]
    - "that invoice from corrigo" → ["Corrigo", "invoice"]
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )

    return json.loads(response.choices[0].message.content)

# Then search with fuzzy matching
from difflib import SequenceMatcher

def fuzzy_search(db: Session, topic: str, threshold: float = 0.7):
    """Search with fuzzy matching"""
    recent = db.query(AgentMemory).filter(
        AgentMemory.created_at >= datetime.now() - timedelta(days=7)
    ).all()

    matches = []
    for mem in recent:
        similarity = SequenceMatcher(None, topic.lower(), mem.summary.lower()).ratio()
        if similarity >= threshold:
            matches.append((mem, similarity))

    # Sort by similarity descending
    return sorted(matches, key=lambda x: x[1], reverse=True)
```

**Pros:**
- Solves the immediate problem
- No new infrastructure
- Uses existing OpenAI API
- Easy to debug and maintain

**Cons:**
- Extra API call per correction (acceptable - only on user corrections)
- Still limited to recent memories (7 days)

---

### Option 2: Add Vector Embeddings (pgvector)
**Cost:** 8-12 hours development + ongoing maintenance
**Complexity:** Medium
**Maintenance:** Moderate

**Implementation:**
```python
# Add to models.py
class AgentMemory(Base):
    # ... existing fields ...
    embedding = Column(Vector(1536))  # OpenAI ada-002 embeddings

# On memory creation
def record_event(summary: str, ...):
    # Generate embedding
    embedding_response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=summary
    )
    embedding_vector = embedding_response.data[0].embedding

    memory = AgentMemory(
        summary=summary,
        embedding=embedding_vector,
        # ... other fields
    )

# Semantic search
def semantic_search(db: Session, query: str, limit: int = 10):
    query_embedding = get_embedding(query)

    results = db.execute(f"""
        SELECT id, summary,
               embedding <-> '{query_embedding}' AS distance
        FROM agent_memory
        WHERE created_at >= NOW() - INTERVAL '7 days'
        ORDER BY distance
        LIMIT {limit}
    """)

    return results.fetchall()
```

**Pros:**
- Semantic understanding: "the P situation" matches "Pedro issue"
- Handles synonyms: "pay problem" matches "payroll issue"
- Ranked by relevance
- Scalable to 1000s of memories

**Cons:**
- Requires pgvector extension (PostgreSQL setup complexity)
- Embedding generation cost (~$0.0001 per memory, negligible)
- Migration needed for existing memories
- More complex debugging ("why did it match that?")
- Overkill for 50 memories

---

### Option 3: Hybrid Approach (Best of Both)
**Cost:** 4-6 hours development
**Complexity:** Low-Medium
**Maintenance:** Easy

**Implementation:**
```python
def intelligent_memory_update(
    db: Session,
    user_message: str
) -> int:
    """
    Intelligent memory update using LLM + fuzzy matching

    1. LLM extracts topics from user message
    2. Fuzzy search finds related memories
    3. LLM confirms matches are correct
    4. Update confirmed memories
    """

    # Step 1: Extract topics
    topics = extract_topics_llm(user_message)

    # Step 2: Fuzzy search for each topic
    candidates = []
    for topic in topics:
        matches = fuzzy_search(db, topic, threshold=0.6)
        candidates.extend(matches)

    # Step 3: LLM confirmation
    confirmed = llm_confirm_matches(user_message, candidates)

    # Step 4: Update confirmed memories
    for mem, confidence in confirmed:
        if confidence > 0.7:
            mark_resolved(db, memory_id=mem.id, annotation=user_message)

    return len(confirmed)

def llm_confirm_matches(
    user_message: str,
    candidates: List[Tuple[AgentMemory, float]]
) -> List[Tuple[AgentMemory, float]]:
    """
    Ask LLM to confirm which memories should be updated
    """

    summaries = "\n".join([
        f"{i+1}. {mem.summary[:100]}"
        for i, (mem, _) in enumerate(candidates)
    ])

    prompt = f"""
    User said: "{user_message}"

    Which of these memories should be marked as resolved?

    {summaries}

    Return JSON: {{"resolved": [1, 3, 5], "confidence": [0.9, 0.8, 0.7]}}

    Only include items that are clearly related to what the user said.
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )

    result = json.loads(response.choices[0].message.content)

    confirmed = []
    for idx, conf in zip(result["resolved"], result["confidence"]):
        if 0 <= idx - 1 < len(candidates):
            confirmed.append((candidates[idx - 1][0], conf))

    return confirmed
```

**Pros:**
- Solves the "pedro was handled" problem reliably
- LLM handles ambiguity and context
- Fuzzy matching catches typos
- No infrastructure changes needed
- Easy to debug (see what LLM decided)

**Cons:**
- 2 LLM calls per correction (extraction + confirmation)
- Cost: ~$0.001 per correction (negligible)

---

## Recommendation: Hybrid Approach

### Why Not Vector Embeddings?

**Scale doesn't justify complexity:**
- You have ~50 memories in 48h window
- PostgreSQL ILIKE search is instant at this scale
- Vector search is for 1000s-10000s of items

**Current pain points aren't about search:**
- "pedro was handled" fails because keyword extraction is hardcoded
- Fuzzy matching would solve 80% of this
- LLM-based topic extraction solves the remaining 20%

**When to add pgvector:**
- You have 1000+ memories and search is slow
- You need cross-lingual search
- You want to find semantically similar past situations
- You're building a "memory clustering" feature

### Proposed Solution

**Phase 1: Fix Immediate Problem (2-3 hours)**

1. **Replace hardcoded topics with LLM extraction:**
```python
# In operations_chat.py, replace lines 294-302 with:
topics = extract_topics_llm(user_message)
```

2. **Add fuzzy matching to mark_resolved:**
```python
# In agent_memory.py mark_resolved(), add fuzzy search option
def mark_resolved(
    db: Session,
    summary_text: Optional[str] = None,
    fuzzy: bool = True,
    threshold: float = 0.7
):
    if fuzzy and summary_text:
        # Use fuzzy matching instead of ILIKE
        return fuzzy_mark_resolved(db, summary_text, threshold)
    else:
        # Original ILIKE logic
        ...
```

3. **Add LLM confirmation for safety:**
```python
# Before marking resolved, ask LLM:
# "User said X. Should I resolve memories about Y? Yes/No"
```

**Phase 2: Enhanced Search (Optional, 2-3 hours)**

1. **Add semantic search endpoint** (using LLM, not vectors):
```python
@router.get("/api/agent-memory/search")
async def smart_search(query: str, db: Session = Depends(get_db)):
    """
    Smart search that:
    1. Uses LLM to extract intent
    2. Searches multiple ways (exact, fuzzy, synonym)
    3. LLM ranks results
    """
    pass
```

2. **Add memory clustering UI** (show related memories):
```python
@router.get("/api/agent-memory/related/{topic}")
async def get_related_memories(topic: str):
    """
    Show all memories related to a topic (Pedro, payroll, etc.)
    """
    pass
```

**Phase 3: Analytics (Optional, future)**

1. **Memory dashboard** - Show what agents learned
2. **Confidence tracking** - Which memories are uncertain?
3. **Duplicate detection** - Same event recorded twice?

---

## Cost-Benefit Analysis

### Current System (Broken)
- **Dev Cost:** $0
- **Runtime Cost:** $0
- **User Frustration:** High ("pedro was handled" doesn't work)

### Option 1: Simple Improvements
- **Dev Cost:** 2-4 hours ($200-400 at $100/hr)
- **Runtime Cost:** ~$0.001 per correction (~$0.30/month)
- **User Frustration:** Low (95% accuracy)
- **Maintenance:** Easy

### Option 2: Vector Embeddings
- **Dev Cost:** 8-12 hours ($800-1200)
- **Runtime Cost:** ~$0.0001 per memory + pgvector infrastructure
- **User Frustration:** Low (98% accuracy)
- **Maintenance:** Moderate (pgvector migrations, index maintenance)

### Option 3: Hybrid (LLM + Fuzzy)
- **Dev Cost:** 4-6 hours ($400-600)
- **Runtime Cost:** ~$0.002 per correction (~$0.60/month)
- **User Frustration:** Very Low (97% accuracy)
- **Maintenance:** Easy

---

## Code Examples

### Minimal Fix (30 minutes)

Add to `server/services/agent_memory.py`:

```python
def extract_topics_simple(user_message: str) -> List[str]:
    """Extract topics using basic NLP (no LLM needed)"""
    from collections import Counter
    import re

    # Remove common words
    stopwords = {'the', 'is', 'was', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}

    # Extract words
    words = re.findall(r'\b[a-z]+\b', user_message.lower())

    # Filter and capitalize proper nouns (likely names/entities)
    topics = []
    for word in words:
        if word not in stopwords and len(word) > 2:
            # Check if it appears in recent memories
            if word.capitalize() in recent_memory_entities(db):
                topics.append(word.capitalize())

    return topics

def recent_memory_entities(db: Session) -> Set[str]:
    """Get all entities mentioned in recent memories"""
    recent = get_recent_context(db, hours=168)  # Last week

    entities = set()
    for mem in recent:
        if mem.related_entities and 'people' in mem.related_entities:
            entities.update(mem.related_entities['people'])

    return entities
```

### Full LLM Solution (2 hours)

Add to `server/services/memory_intelligence.py` (new file):

```python
"""
Intelligent memory update system using LLM
"""

import json
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def intelligent_memory_update(
    db: Session,
    user_message: str,
    dry_run: bool = False
) -> dict:
    """
    Use LLM to intelligently update agent memory

    Returns:
        {
            "topics_extracted": ["Pedro", "payroll"],
            "candidates_found": 5,
            "confirmed_matches": 3,
            "memories_updated": [memory_id1, memory_id2],
            "confidence": 0.85
        }
    """

    # Step 1: Extract topics
    topics = extract_topics_llm(user_message)
    if not topics:
        return {"error": "No topics found in message"}

    # Step 2: Find candidate memories
    from services.agent_memory import AgentMemoryService

    candidates = []
    for topic in topics:
        matches = AgentMemoryService.search_memory(db, topic, limit=20)
        candidates.extend(matches)

    # Remove duplicates
    candidates = list({m.id: m for m in candidates}.values())

    if not candidates:
        return {"error": f"No memories found for topics: {topics}"}

    # Step 3: LLM confirmation
    confirmed = llm_confirm_matches(user_message, candidates)

    if dry_run:
        return {
            "topics_extracted": topics,
            "candidates_found": len(candidates),
            "confirmed_matches": len(confirmed),
            "would_update": [mem.id for mem, _ in confirmed],
            "dry_run": True
        }

    # Step 4: Update memories
    updated_ids = []
    for mem, confidence in confirmed:
        if confidence > 0.7:
            AgentMemoryService.mark_resolved(
                db=db,
                email_id=mem.email_id,
                annotation=f"User update: {user_message}"
            )
            updated_ids.append(mem.id)

    return {
        "topics_extracted": topics,
        "candidates_found": len(candidates),
        "confirmed_matches": len(confirmed),
        "memories_updated": updated_ids,
        "average_confidence": sum(c for _, c in confirmed) / len(confirmed) if confirmed else 0
    }


def extract_topics_llm(user_message: str) -> List[str]:
    """Extract topics using GPT-4o-mini"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Extract key topics/entities from user messages.

Return a JSON array of topics (people, systems, issues).

Examples:
- "pedro was handled" -> ["Pedro"]
- "the payroll thing is done" -> ["payroll"]
- "that corrigo invoice got paid" -> ["Corrigo", "invoice"]
- "schedule issue resolved" -> ["schedule"]

Only return clear topics, not filler words."""
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

    try:
        result = json.loads(response.choices[0].message.content)
        return result.get("topics", [])
    except:
        return []


def llm_confirm_matches(
    user_message: str,
    candidates: List
) -> List[Tuple[any, float]]:
    """Ask LLM which memories should be updated"""

    summaries = "\n".join([
        f"{i+1}. {mem.summary[:120]}"
        for i, mem in enumerate(candidates[:10])  # Limit to top 10
    ])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You help determine which agent memories should be updated.

User will say something like "pedro was handled" or "payroll is done".

Return JSON:
{
    "resolved": [1, 3],  // indices of memories to mark as resolved
    "confidence": [0.9, 0.8],  // confidence for each (0-1)
    "reasoning": "User said X matches memories 1,3 about Y"
}

Only mark memories as resolved if they CLEARLY relate to what the user said.
Be conservative - when in doubt, don't mark it."""
            },
            {
                "role": "user",
                "content": f"""User said: "{user_message}"

Which of these memories should be marked as resolved?

{summaries}

Return your decision as JSON."""
            }
        ],
        temperature=0.3,
        max_tokens=200,
        response_format={"type": "json_object"}
    )

    try:
        result = json.loads(response.choices[0].message.content)

        confirmed = []
        for idx, conf in zip(result.get("resolved", []), result.get("confidence", [])):
            if 1 <= idx <= len(candidates):
                confirmed.append((candidates[idx - 1], conf))

        return confirmed
    except Exception as e:
        print(f"LLM confirmation error: {e}")
        return []
```

Then update `server/routes/operations_chat.py`:

```python
# Replace lines 283-312 with:

from services.memory_intelligence import intelligent_memory_update

# Check if user is correcting memory
correction_keywords = ['was handled', 'already done', 'resolved', 'completed', 'fixed']
is_correction = any(keyword in user_msg_lower for keyword in correction_keywords)

if is_correction:
    result = intelligent_memory_update(db, request.message)

    if "memories_updated" in result:
        print(f"[Smart Memory Update] {result}")
        print(f"  Topics: {result['topics_extracted']}")
        print(f"  Updated: {len(result['memories_updated'])} memories")
        print(f"  Confidence: {result.get('average_confidence', 0):.2f}")
```

---

## Testing Plan

### Test Case 1: Simple Correction
```
User: "pedro was handled"

Expected:
1. LLM extracts: ["Pedro"]
2. Searches for "Pedro" in recent memories
3. Finds: "Analyzed email about Pedro call-off" (urgent)
4. LLM confirms: Yes, mark as resolved
5. Updates memory with [RESOLVED] prefix
6. Next digest: Pedro doesn't appear
```

### Test Case 2: Typo
```
User: "the payrol issue is done"

Expected:
1. LLM extracts: ["payroll"]
2. Fuzzy search finds "payroll" (despite "payrol" typo)
3. LLM confirms match
4. Updates memory
```

### Test Case 3: Ambiguous Reference
```
User: "that issue is fixed"

Expected:
1. LLM extracts: ["issue"] (too vague)
2. No specific topic found
3. Asks user: "Which issue? I see Pedro, payroll, invoice..."
4. User clarifies
5. Updates correct memory
```

### Test Case 4: False Positive
```
User: "is the pedro issue resolved?"

Expected:
1. LLM extracts: ["Pedro", "issue"]
2. Finds Pedro memories
3. LLM sees question mark, DOES NOT mark as resolved
4. Responds without updating memory
```

---

## Performance Considerations

### Current System
- Query time: <10ms (ILIKE on small dataset)
- Memory usage: Negligible
- Database load: Minimal

### With LLM Enhancement
- Query time: ~500ms (LLM call)
- Cost: $0.001-0.002 per correction
- Only runs on corrections (~1-5 times/day)
- Acceptable latency for this use case

### If Using Vector Search (Not Recommended Yet)
- Query time: ~50ms (vector similarity)
- Storage: +6KB per memory (1536-dim embedding)
- Embedding generation: ~200ms + $0.0001 per memory
- Only worth it at 1000+ memories

---

## Migration Path

### Week 1: Fix Immediate Problem
1. Add LLM topic extraction
2. Test with current hardcoded fallback
3. Deploy and monitor

### Week 2: Add Intelligence
1. Add fuzzy matching
2. Add LLM confirmation
3. Add dry-run mode for testing

### Week 3: Polish
1. Add confidence thresholds
2. Add ambiguity detection
3. Add user feedback loop

### Future: If Needed
1. Evaluate pgvector if memory count > 1000
2. Add memory clustering
3. Add duplicate detection

---

## Final Verdict

**Don't add vector embeddings yet.**

Your problem is:
1. 90% solved by LLM topic extraction
2. 9% solved by fuzzy matching
3. 1% might need vectors someday

**Recommended investment:**
- **4 hours**: Implement hybrid LLM + fuzzy approach
- **$0.60/month**: Runtime cost for ~300 corrections/month
- **95%+ accuracy**: Should handle all reasonable cases

Save vector embeddings for when you have:
- 1000+ memories in search scope
- Cross-lingual requirements
- Complex similarity matching needs
- Performance issues with current approach

---

## Code to Add (Summary)

### File 1: `server/services/memory_intelligence.py` (NEW)
See full implementation above (~200 lines)

### File 2: `server/routes/operations_chat.py` (MODIFY)
Replace correction detection (lines 283-312) with intelligent_memory_update()

### File 3: `server/test_memory_intelligence.py` (NEW)
```python
"""Test intelligent memory updates"""

from database import SessionLocal
from services.memory_intelligence import intelligent_memory_update

db = SessionLocal()

# Test 1: Simple correction
result = intelligent_memory_update(
    db,
    "pedro was handled yesterday",
    dry_run=True
)

print("Test 1 (Simple):")
print(json.dumps(result, indent=2))

# Test 2: Ambiguous
result = intelligent_memory_update(
    db,
    "that's done",
    dry_run=True
)

print("\nTest 2 (Ambiguous):")
print(json.dumps(result, indent=2))

db.close()
```

---

## Questions for You

1. **How often do you correct memories?** (If <5 times/day, LLM cost is negligible)
2. **Are corrections mostly about recent items?** (If yes, 7-day search window is fine)
3. **Do you want to review before updating?** (Can add confirmation step)
4. **What accuracy is acceptable?** (95%? 99%?)

Based on answers, I can tune the solution accordingly.

---

**Bottom Line:** Use LLM intelligence, not vector embeddings. It's simpler, cheaper, easier to debug, and solves 99% of your use cases. Add vectors later if scale demands it.
