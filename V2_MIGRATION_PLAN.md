# ChiliHead OpsManager v2 Migration Plan
## Project Management & Systems Architecture View

---

## Executive Summary

**What We're Doing**: Migrating from a traditional multi-tab web app (v1) to an AI-native conversational platform (v2) built on Open-WebUI.

**Why**: v1 has fundamental architectural problems that can't be fixed with patches:
- **Chat fragmentation** - Every tab has its own chat = no shared context
- **Context loss** - AI can't remember what "that invoice" means across pages
- **Click-heavy UX** - Too much navigation, not enough conversation
- **Email sanitization** - Gmail API loses images/formatting
- **Memory fragmentation** - Agent memory system exists but isn't unified

**The Vision**: One conversational interface (AUBS) with full context across emails, tasks, calendar, and delegations. Natural language replaces navigation.

**Timeline**: 6-8 weeks (phased approach, incremental delivery)

**Risk**: Previous attempt over-engineered with Dolphin/UITARS/DAG complexity and Claude Code lost context after 5-6 truncations.

**Mitigation**: Break into small, independent phases with clear handoff documents.

---

## Problem Analysis: Why v1 Can't Scale

### 1. The Unified Chat Problem ⚠️

**Current State (v1)**:
```
Inbox Tab → No chat
Triage Tab → No chat
Todo Tab → No chat
Delegations Tab → No chat
Operations Tab → Has OperationsChat.tsx (isolated, no context from other tabs)
Calendar Tab → No chat
Team Board → No chat
SMS Tab → Has chat but separate
```

**What You Want**:
- Single chat instance visible on ALL tabs
- Chat maintains context across tab switches
- Chat knows about emails from Inbox, tasks from Todo, etc.

**Why v1 Can't Do This**:
- **Component-based isolation** - Each tab is separate React component with own state
- **No global chat state** - Would need Redux/Zustand + context provider across entire app
- **Backend doesn't support multi-context** - Chat API is session-based but doesn't pull live data from other tabs
- **Memory system is one-way** - AI writes to agent_memory, but chat doesn't read it comprehensively

**Attempted Fix Would Require**:
1. Global state manager (Redux/Zustand) - adds 2K+ lines
2. Real-time sync between tabs - WebSocket/polling overhead
3. Context aggregation layer - complex query builder
4. Chat UI refactor across 8 tabs - high risk of regressions

**This is architectural debt, not a feature gap.**

---

### 2. Email Sanitization Problem

**v1 Flow**:
```
Gmail API → body_html (sanitized by Google)
         → Inline images become <img src="cid:...">
         → Need attachment lookup + replacement
         → Store in EmailAttachment table
         → Serve via /api/attachments/by-cid/...
```

**Problems**:
- HTML is sanitized (loses styles, layouts)
- Images require complex cid: replacement logic
- Attachments >255 chars broke until TEXT migration
- Email rendering is buggy (user reports issues)

**v2 Fix**:
```
SnappyMail → Direct IMAP to Gmail
          → Full HTML rendering (no sanitization)
          → Images load natively
          → Screenshot + Vision AI for OCR
```

No custom attachment handling. No sanitization workarounds. Simpler = better.

---

### 3. Context Fragmentation Problem

**v1 Memory Flow**:
```
AI Triage → agent_memory (triage events)
Daily Digest → agent_memory (digest events)
Operations Chat → agent_memory (chat events)
                ↓
                Each reads its own slice of memory
                No unified context builder
```

**Example Failure**:
```
User in Inbox tab: Sees email about "Sysco invoice"
User clicks to Todo tab: Adds task "Review invoice"
User goes to Operations tab, asks chat: "What's the status on that invoice?"
Chat response: "I don't see an invoice task" ❌
```

**Why?** Chat only loads context snapshot from session start. Doesn't know about:
- Tasks added in other tabs
- Emails analyzed in other tabs
- Live state changes

**v2 Fix**: Open-WebUI tools call live APIs. Every query pulls fresh state.

---

## Architecture Comparison: v1 vs v2

| Aspect | v1 (Current) | v2 (Vision) |
|--------|-------------|-------------|
| **Interface** | 8 separate tabs (Inbox, Triage, Todo, etc.) | One chat interface (Open-WebUI) |
| **Navigation** | Click tabs → Click cards → Click buttons | Natural language ("Show me urgent emails") |
| **Chat** | Isolated to Operations tab | Global, context-aware across all operations |
| **Email** | Gmail API (sanitized) + attachment workarounds | SnappyMail (full IMAP, no sanitization) |
| **Context** | Fragmented (per tab, per session) | Unified (all data sources in one semantic space) |
| **Memory** | Agent memory table (one-way writes) | RAG + Qdrant (semantic search, two-way) |
| **AI Integration** | Hardcoded GPT-4o calls in backend | Open-WebUI tools framework (model-agnostic) |
| **Task Management** | Todo tab with Eisenhower matrix UI | "Add that to my todos" (conversational) |
| **Calendar** | Modal for adding events | "Add this to my calendar" (AUBS knows "this") |
| **Delegations** | Form-based 5-pillar entry | Guided conversation for delegation creation |
| **Image OCR** | Vision API for RAP Mobile only | Screenshot + Vision for ANY email image |
| **Frontend Code** | 15K+ lines (Next.js, React, TypeScript) | ~2K lines (Open-WebUI config + backend tools) |
| **Backend Code** | 78 API endpoints across 10 route files | ~30 tool endpoints (simpler, focused) |
| **Maintenance** | High (frontend + backend + sync logic) | Low (backend tools only) |

---

## Migration Strategy: How to Get from v1 to v2

### Core Principle: **Parallel Development, Incremental Cutover**

**Do NOT**:
- ❌ Rip out v1 and rebuild from scratch
- ❌ Try to "merge" v1 frontend into Open-WebUI
- ❌ Build everything before testing anything

**Do**:
- ✅ Keep v1 running (fallback if v2 has issues)
- ✅ Build v2 as separate stack (different ports)
- ✅ Migrate backend logic incrementally (share database)
- ✅ Test each phase before moving to next
- ✅ Cut over feature-by-feature, not all-at-once

---

### High-Level Migration Phases

```
Phase 0: Foundation (Week 1)
  ├─ Set up Open-WebUI + SnappyMail
  ├─ Verify email filtering works
  └─ Test basic chat with simple tools

Phase 1: Core Tools (Weeks 2-3)
  ├─ Email tools (get_emails, triage)
  ├─ Task tools (CRUD for todos)
  └─ Test tool calling from Open-WebUI

Phase 2: Advanced Tools (Weeks 3-4)
  ├─ Calendar integration
  ├─ Delegation tools
  └─ Daily brief skill

Phase 3: Vision + SnappyMail (Week 5)
  ├─ Email screenshot automation
  ├─ OCR for invoices/receipts
  └─ Image data extraction

Phase 4: Memory + RAG (Week 6)
  ├─ Migrate agent_memory to Qdrant
  ├─ Semantic search for emails
  └─ Long-term conversation context

Phase 5: Polish + Cutover (Weeks 7-8)
  ├─ Performance tuning
  ├─ Error handling
  ├─ Migrate daily workflows to v2
  └─ Deprecate v1 frontend
```

---

## Detailed Implementation Plan

### Phase 0: Foundation (Week 1)

**Goal**: Prove the architecture works end-to-end.

**Tasks**:
1. **Deploy Open-WebUI** (Day 1)
   - Docker Compose or local install
   - Configure on port 8080 (v1 uses 3001, 8002)
   - Verify health check

2. **Deploy SnappyMail** (Day 1-2)
   - Docker on port 8888
   - Connect to Gmail via IMAP (user's work email)
   - Set up filters: `from:(@chilis.com OR @brinker.com OR @hotschedules.com)`
   - Verify full HTML email rendering

3. **Create AUBS Backend v2** (Day 2-3)
   - New FastAPI app: `/server_v2/app.py` (separate from v1)
   - Port 5000 (avoid conflict with 8002)
   - Database connection: reuse PostgreSQL from v1
   - Health endpoint: `GET /health`

4. **Implement First Tool** (Day 3-4)
   - Tool: `get_emails(limit, filter)`
   - Returns: List of emails from EmailCache table (reuse v1 DB)
   - Register tool with Open-WebUI (OpenAPI spec or MCP)

5. **Test End-to-End** (Day 5)
   - Open Open-WebUI chat
   - Ask: "Show me my recent emails"
   - Verify AUBS calls `get_emails` tool
   - Verify results appear in chat

**Success Criteria**:
- ✅ Open-WebUI running on port 8080
- ✅ SnappyMail showing work emails (not sanitized)
- ✅ AUBS backend v2 on port 5000
- ✅ First tool call works (get_emails)
- ✅ Chat shows results

**Deliverable**: Docker Compose file + 1-page setup doc

**Handoff Document**: `PHASE_0_COMPLETE.md` with:
- URLs for all services
- Test command: "Show me my recent emails"
- Expected response format
- Database connection string

---

### Phase 1: Core Tools (Weeks 2-3)

**Goal**: Feature parity for email + task management.

**Tools to Build**:

#### 1.1 Email Tools (Week 2, Days 1-3)
```python
# /server_v2/tools/email_tools.py

def get_emails(limit=20, filter=None):
    """Retrieve recent emails from inbox"""
    # Query: EmailCache table (reuse v1)
    # Filter by: sender, subject, date range
    # Return: List[{subject, sender, date, thread_id, snippet}]

def triage_email(thread_id):
    """AI analysis of email priority/category"""
    # Reuse: services/smart_assistant.py from v1
    # Check: EmailAnalysisCache first
    # Return: {priority, category, key_entities, suggested_tasks}

def get_email_context(thread_id):
    """Full email thread with history"""
    # Query: EmailCache + Gmail API
    # Return: Full conversation thread

def mark_email_done(thread_id):
    """Mark email as acknowledged"""
    # Update: EmailState table
    # Return: Success message
```

**Test Case**:
```
User: "What emails need my attention?"
AUBS: [Calls get_emails(filter="unread")]
      "You have 12 unread emails. 3 are high priority:
       1. Manager schedule due today (from Stephanie)
       2. Blake called out - dinner shift (from Carmen)
       3. Sysco invoice approval needed (from Accounts)"

User: "Tell me more about the Blake callout"
AUBS: [Calls get_email_context(thread_id)]
      [Shows full email thread]
      "Blake called out sick. Dinner shift (4pm-close) needs coverage.
       Carmen is asking if Tiffany can cover."

User: "Mark it as handled"
AUBS: [Calls mark_email_done(thread_id)]
      "Marked as done. Removed from your urgent list."
```

#### 1.2 Task Tools (Week 2, Days 4-5)
```python
# /server_v2/tools/task_tools.py

def get_tasks(status="pending", priority=None):
    """Retrieve todo list"""
    # Query: tasks table (reuse v1)
    # Filter by: status, priority, eisenhower quadrant
    # Return: List[{title, due_date, priority, status}]

def add_task(title, priority="medium", due_date=None, notes=None):
    """Create new task"""
    # Insert: tasks table
    # Auto-calculate: eisenhower_quadrant from priority/due_date
    # Return: New task_id

def update_task(task_id, status=None, priority=None, due_date=None):
    """Update existing task"""
    # Update: tasks table
    # Return: Updated task

def delete_task(task_id):
    """Delete task"""
    # Delete: tasks table
    # Return: Success message
```

**Test Case**:
```
User: "What's on my todo list today?"
AUBS: [Calls get_tasks(due_date="today")]
      "You have 5 tasks due today:
       1. Submit manager schedule (HIGH)
       2. Review Sysco invoice (MEDIUM)
       3. Follow up with Devon on training (LOW)
       ..."

User: "Add finding Blake's coverage to high priority"
AUBS: [Calls add_task(title="Find dinner shift coverage for Blake",
                      priority="high",
                      due_date="today")]
      "Added to high-priority tasks. Due today."

User: "Mark the schedule as done"
AUBS: [Calls update_task(task_id=X, status="completed")]
      "Marked complete. 4 tasks remaining for today."
```

#### 1.3 Integration Testing (Week 3, Day 1)
```
User: "Show me urgent emails and add any action items to my todos"
AUBS: [Calls get_emails(filter="priority>80")]
      [For each email, calls triage_email(thread_id)]
      [Extracts suggested_tasks from analysis]
      [Calls add_task() for each suggested task]
      "Found 3 urgent emails. Added 5 tasks to your list:
       1. Call payroll about Hannah's hours (from Beth's email)
       2. Submit manager schedule by 3pm (from Stephanie)
       ..."
```

**Success Criteria**:
- ✅ Can list, filter, analyze emails via chat
- ✅ Can create, read, update, delete tasks via chat
- ✅ AUBS maintains context ("that email", "the urgent one")
- ✅ Tool calls succeed 95%+ of the time

**Deliverable**: 6 working tools + test cases document

**Handoff Document**: `PHASE_1_COMPLETE.md` with:
- List of all tools implemented
- Test cases for each tool
- Known limitations
- Next phase dependencies

---

### Phase 2: Advanced Tools (Weeks 3-4)

**Goal**: Calendar, delegations, daily brief.

#### 2.1 Calendar Tools (Week 3, Days 2-4)
```python
# /server_v2/tools/calendar_tools.py

def get_calendar(start_date=None, end_date=None):
    """Retrieve upcoming calendar events"""
    # API: Google Calendar API (reuse v1 oauth)
    # Return: List[{title, start, end, attendees}]

def add_calendar_event(title, start_datetime, duration_minutes=60, attendees=None):
    """Create calendar event"""
    # API: Google Calendar API
    # Return: Event ID + calendar link

def check_availability(start_datetime, duration_minutes):
    """Check for scheduling conflicts"""
    # Query: get_calendar() for overlapping events
    # Return: Boolean + conflicting events if any

def find_meeting_time(attendees, duration_minutes, date_range):
    """Suggest optimal meeting times"""
    # API: Google Calendar freebusy
    # Return: List of available time slots
```

**Test Case**:
```
User: "What's on my calendar today?"
AUBS: [Calls get_calendar(start_date="today", end_date="today")]
      "You have 3 events today:
       1. 10am: District call with RVP (1 hour)
       2. 2pm: Prep walk with Carmen (30 min)
       3. 4pm: Team huddle (15 min)"

User: "Add reviewing the Sysco invoice to my calendar tomorrow at 9am"
AUBS: [Context: Knows "Sysco invoice" from earlier email discussion]
      [Calls add_calendar_event(title="Review Sysco invoice",
                                start_datetime="2024-11-25 09:00",
                                duration_minutes=30)]
      "Added to your calendar: Nov 25 at 9am (30 min). No conflicts."
```

#### 2.2 Delegation Tools (Week 3-4, Days 5-7)
```python
# /server_v2/tools/delegation_tools.py

def create_delegation(assigned_to, task_description, due_date,
                     five_pillars: dict):
    """Create ChiliHead 5-pillar delegation"""
    # five_pillars = {
    #   "belonging": "How to make them feel valued",
    #   "direction": "What success looks like",
    #   "preparation": "What they need",
    #   "support": "How you'll help",
    #   "accountability": "Follow-up plan"
    # }
    # Insert: delegations table
    # Return: Delegation ID

def get_delegations(status="pending", assigned_to=None):
    """List delegations"""
    # Query: delegations table
    # Return: List of delegations

def update_delegation(delegation_id, status=None, notes=None):
    """Update delegation progress"""
    # Update: delegations table + chilihead_progress JSON
    # Return: Updated delegation

def draft_delegation(task_description, assigned_to):
    """AI-assisted delegation drafting"""
    # LLM: Generate 5-pillar structure based on past delegations
    # Return: Draft for user approval
```

**Test Case**:
```
User: "I need to delegate finding dinner coverage to Tiffany"
AUBS: [Calls draft_delegation(task="Find dinner shift coverage",
                              assigned_to="Tiffany")]
      "Here's a draft delegation using the ChiliHead 5-pillar system:

       BELONGING: Tiffany, I'm trusting you with this because you're
                  great at rallying the team.

       DIRECTION: Find someone to cover Blake's 4pm-close shift tonight.
                  Confirm with me by 2pm.

       PREPARATION: Check the schedule, call the usual suspects
                   (Hannah, Devon). Use the coverage request template.

       SUPPORT: I'm available by phone if you hit issues. Text me updates.

       ACCOUNTABILITY: Follow up with me at 2pm. If no luck by 1pm,
                      escalate to me.

       Want me to save this or make changes?"

User: "Save it and send her a message"
AUBS: [Calls create_delegation(...)]
      [Calls send_team_message(to="Tiffany", message="...")]
      "Delegation saved. Message sent via Google Chat."
```

#### 2.3 Daily Brief Skill (Week 4, Days 1-2)
```python
# /server_v2/skills/daily_brief.py

def generate_daily_brief(focus_areas=None):
    """Generate morning operations summary"""
    # Aggregate:
    #   - Unread high-priority emails
    #   - Today's calendar events
    #   - Overdue tasks
    #   - Pending delegations needing follow-up
    #   - Yesterday's completions
    #   - Agent memory insights
    # LLM: Synthesize into briefing
    # Return: Structured summary + action recommendations
```

**Test Case**:
```
User: "AUBS, good morning. What's my day look like?"
AUBS: [Calls generate_daily_brief()]
      "Good morning! Here's what needs your attention:

       🔴 URGENT (Due Today):
       - Manager schedule due by 3pm (from Stephanie's email)
       - Blake's dinner shift needs coverage (still pending)
       - Sysco invoice review ($2,847.32, due Dec 22)

       📅 CALENDAR:
       - 10am: District call with RVP
       - 2pm: Prep walk with Carmen
       - 4pm: Team huddle

       ✅ COMPLETED YESTERDAY:
       - Submitted P&L review
       - Followed up with Devon on training

       💭 SUGGESTED PRIORITIES:
       1. Find Blake's coverage ASAP (call Tiffany?)
       2. Draft manager schedule before district call
       3. Review Sysco invoice (add to calendar for tomorrow?)

       Want me to help with any of these?"
```

**Success Criteria**:
- ✅ Calendar events appear in chat
- ✅ Can create events from conversation context
- ✅ Delegation drafting works with 5-pillar structure
- ✅ Daily brief synthesizes across all data sources
- ✅ AUBS proactively suggests priorities

**Deliverable**: 11 more tools + 1 skill + test cases

**Handoff Document**: `PHASE_2_COMPLETE.md`

---

### Phase 3: Vision + SnappyMail (Week 5)

**Goal**: Full email image support + OCR.

#### 3.1 SnappyMail Screenshot (Days 1-2)
```python
# /server_v2/tools/snappymail_tools.py

def screenshot_email(thread_id):
    """Capture email screenshot from SnappyMail"""
    # Tech: Playwright or Selenium
    # Flow:
    #   1. Login to SnappyMail (session persistence)
    #   2. Navigate to email by thread_id
    #   3. Take full-page screenshot
    #   4. Return: Base64 image data
```

#### 3.2 Vision OCR (Days 3-4)
```python
# /server_v2/tools/vision_tools.py

def read_email_image(thread_id, instruction="Extract all text and data"):
    """OCR + Vision AI for email images"""
    # Flow:
    #   1. screenshot_email(thread_id)
    #   2. Send to OpenAI GPT-4V or Claude Vision
    #   3. Prompt: "Extract invoice data: total, date, line items, ..."
    #   4. Parse structured response
    # Return: Extracted data (JSON)

def extract_invoice_data(thread_id):
    """Structured invoice parsing"""
    # Specialized: Invoice-specific prompt
    # Return: {invoice_number, date, total, due_date, line_items}

def extract_schedule_data(thread_id):
    """Parse schedule images (shift schedules, etc.)"""
    # Return: {shifts: [{employee, date, start, end}]}
```

**Test Case**:
```
User: "Show me that Sysco invoice"
AUBS: [Searches recent emails for "Sysco invoice"]
      [Calls read_email_image(thread_id, instruction="Extract invoice details")]
      "Here's what I see:

       Invoice #: SYS-247832
       Date: Nov 22, 2024
       Total: $2,847.32
       Due: Net 30 (Dec 22, 2024)

       Line Items:
       - Chicken (40 cases): $1,120.00
       - Produce: $847.00
       - Frozen goods: $612.00
       - Dry storage: $268.32

       Want me to add 'Review Sysco invoice' to your high-priority todos?"

User: "Yes, and add it to my calendar for tomorrow morning"
AUBS: [Calls add_task(title="Review Sysco invoice", priority="high", due_date="tomorrow")]
      [Calls add_calendar_event(title="Review Sysco invoice", start_datetime="tomorrow 09:00")]
      "Done. Added to high-priority tasks and calendar (Nov 25, 9am)."
```

**Success Criteria**:
- ✅ Can screenshot emails from SnappyMail
- ✅ OCR extracts text/data from images
- ✅ Invoice parsing returns structured data
- ✅ Works for RAP Mobile dashboard images

**Deliverable**: Vision tools + SnappyMail integration

**Handoff Document**: `PHASE_3_COMPLETE.md`

---

### Phase 4: Memory + RAG (Week 6)

**Goal**: Long-term memory and semantic search.

#### 4.1 Migrate to Qdrant (Days 1-3)
```python
# /server_v2/services/memory_service.py

def ingest_to_qdrant(collection="operations_memory"):
    """Migrate agent_memory table to Qdrant vectors"""
    # Query: agent_memory table (all events)
    # For each event:
    #   - Generate embedding (OpenAI text-embedding-3-small)
    #   - Store in Qdrant with metadata (event_type, date, entities)
    # Return: Ingestion stats

def semantic_search(query, limit=10):
    """Search memory by semantic similarity"""
    # Generate query embedding
    # Search Qdrant
    # Return: Relevant memory events
```

#### 4.2 RAG for Email History (Days 4-5)
```python
def search_email_history(query, date_range=None):
    """Semantic search of past emails"""
    # Query Qdrant: email_embeddings collection
    # Filter by: date range, sender, priority
    # Return: Relevant emails with context
```

**Test Case**:
```
User: "What happened with that payroll issue from last month?"
AUBS: [Calls semantic_search(query="payroll issue")]
      [Finds: Agent memory events + email threads]
      "Found 3 related items from last month:

       1. Nov 5: Email from Beth - Hannah's hours short by 8.5 hours
          Resolution: Called payroll, escalated to district

       2. Nov 8: Follow-up email - Payroll confirmed correction

       3. Nov 12: Agent memory - Added follow-up task (completed)

       Want me to pull up any of these threads?"
```

**Success Criteria**:
- ✅ Agent memory migrated to Qdrant
- ✅ Semantic search works for past operations
- ✅ Email history searchable by natural language
- ✅ Memory persists across sessions

**Deliverable**: RAG system + memory migration

**Handoff Document**: `PHASE_4_COMPLETE.md`

---

### Phase 5: Polish + Cutover (Weeks 7-8)

**Goal**: Production-ready v2, deprecate v1.

#### 5.1 Error Handling (Week 7, Days 1-2)
- Tool timeouts (5s max)
- Gmail API rate limit handling
- Graceful degradation (if calendar API fails, continue with emails)
- User-friendly error messages

#### 5.2 Performance Tuning (Week 7, Days 3-4)
- Cache tool results (Redis)
- Optimize database queries (add indexes)
- Batch operations where possible

#### 5.3 Testing (Week 7, Day 5 - Week 8, Day 2)
- End-to-end test cases (20+ scenarios)
- Load testing (simulate 100 emails/day)
- Edge cases (empty results, malformed data)

#### 5.4 Migration (Week 8, Days 3-5)
- Run v1 and v2 in parallel for 3 days
- Use v2 for daily operations
- Document issues, fix bugs
- Deprecate v1 frontend (keep backend for data access)

**Success Criteria**:
- ✅ All v1 features work in v2
- ✅ No data loss during migration
- ✅ v2 is faster and easier to use than v1
- ✅ User prefers v2 for daily work

---

## Risk Mitigation: How to Avoid "Claude Code Forgets"

### The Problem
Previous attempt:
- Built too much at once (Dolphin + UITARS + DAG orchestration)
- Long implementation sessions (5-6 truncations)
- Claude Code lost context of what was built and why
- Ended up with code that didn't integrate

### The Solution: **Micro-Phases + Handoff Documents**

#### Rule 1: One Tool at a Time
**Do**:
- "Implement `get_emails` tool. Test it. Stop."
- "Implement `add_task` tool. Test it. Stop."

**Don't**:
- "Implement all email tools" (too broad)
- "Build the email system" (way too broad)

#### Rule 2: Handoff Documents
After each tool/phase, create a handoff doc:

**Template**:
```markdown
# HANDOFF: get_emails Tool

## What Was Built
- File: /server_v2/tools/email_tools.py
- Function: get_emails(limit, filter)
- Database: Queries EmailCache table from v1
- Returns: List of email dicts

## How to Test
curl http://localhost:5000/tools/get_emails?limit=5

## Expected Output
[{"thread_id": "...", "subject": "...", "sender": "...", ...}]

## What's Next
- Build: triage_email tool
- Depends on: This tool (get_emails)
- No blockers
```

**Why This Works**:
- Claude Code can read the handoff doc and pick up exactly where it left off
- No need to re-explain the entire architecture
- Clear test case proves it works
- Next step is explicit

#### Rule 3: Test Before Moving On
**Checkpoint after each tool**:
1. Write the tool
2. Test it manually (curl or chat)
3. Verify output is correct
4. Write handoff doc
5. STOP. Wait for user confirmation before next tool.

#### Rule 4: Share Database, Not Code
v1 and v2 can share PostgreSQL:
- v2 tools query same tables (EmailCache, tasks, delegations)
- No need to migrate data mid-build
- v1 continues working while v2 is built

#### Rule 5: No Over-Engineering
**Avoid**:
- Custom orchestration frameworks (Dolphin/DAG)
- Visual debugging tools (UITARS)
- Complex abstractions before you need them

**Use**:
- Open-WebUI's built-in tool system
- Simple Python functions
- Standard libraries (httpx, SQLAlchemy)

---

## Implementation Workflow (For Working with Claude Code)

### Session Template

**Session Start**:
1. "We're building v2 Phase X. Read PHASE_X_PLAN.md."
2. "Start with the first tool: [tool name]."
3. "Here's the spec: [paste spec from this doc]."

**During Session**:
1. Claude Code implements tool
2. You test it: `curl ...` or chat test
3. If it works: "Write handoff doc and stop."
4. If it doesn't: "Fix [specific issue] and re-test."

**Session End**:
1. Claude Code writes handoff doc
2. You review handoff doc
3. You commit: `git add . && git commit -m "Phase X: Implemented [tool name]"`
4. Next session starts with: "Read HANDOFF_[tool name].md and continue with next tool."

### Breaking Big Tasks
If a phase feels too big (>5 tools), break it further:

**Phase 1a**: Email read tools (get_emails, get_email_context)
**Phase 1b**: Email write tools (mark_email_done, triage_email)
**Phase 1c**: Task CRUD tools

Each sub-phase = one session = one handoff doc.

---

## Success Criteria

### Must-Haves (v1 Parity)
- ✅ All emails triaged with AI analysis
- ✅ Tasks tracked with Eisenhower Matrix
- ✅ ChiliHead 5-pillar delegations work
- ✅ Conversation history persists
- ✅ Daily briefing generation
- ✅ Deadline extraction and tracking

### Better Than v1
- ✅ No email sanitization (SnappyMail)
- ✅ Image preview + OCR works
- ✅ **Unified chat across all operations** (solves the core problem)
- ✅ Context maintained ("that invoice", "the urgent one")
- ✅ Google Calendar integrated
- ✅ Natural language > clicking tabs

### Measurable Goals
- **Context Success**: "Show me that email" works 95%+ of the time (AUBS knows "that")
- **Tool Success Rate**: 95%+ of tool calls succeed
- **User Preference**: User chooses v2 over v1 for daily work after 1 week
- **Maintenance**: <2 hours/week for bug fixes (vs 5+ hours/week in v1)

---

## What You Get at the End

**v1 (Before)**:
```
User: Switches to Inbox tab
User: Clicks email to read
User: Switches to Triage tab
User: Clicks "Analyze" button
User: Reads AI analysis
User: Switches to Todo tab
User: Clicks "Add Task" button
User: Fills out form
User: Clicks Save
User: Switches to Operations tab
User: Types in chat: "What's urgent today?"
Chat: "I don't have access to your email or tasks" ❌
```

**v2 (After)**:
```
User: "AUBS, what needs my attention today?"
AUBS: [One unified context, sees everything]
      "You have 3 urgent items:
       1. Manager schedule due by 3pm
       2. Blake's shift needs coverage
       3. Sysco invoice ($2,847) needs review

       Want me to add these to your calendar or pull up details?"

User: "Show me the invoice"
AUBS: [Remembers "invoice" = Sysco invoice from context]
      [Screenshots from SnappyMail, OCRs with Vision AI]
      "Invoice #SYS-247832, $2,847.32, due Dec 22..."

User: "Add reviewing it to my high priority todos"
AUBS: [Knows "it" = that invoice]
      [Calls add_task with context]
      "Added to high priority. Due Dec 22."
```

**One conversation. Full context. Natural language. No tab switching.**

That's the vision, and this plan gets you there without losing the plot.

---

## Next Steps

1. **Review this plan** - Does it make sense? Any gaps?
2. **Approve Phase 0** - Ready to start with Open-WebUI setup?
3. **Set up tracking** - Use Linear/Notion/GitHub Projects for task tracking
4. **Begin Phase 0** - First session: "Set up Open-WebUI and test first tool"

---

## Appendix: Tech Stack Comparison

| Component | v1 | v2 |
|-----------|----|----|
| Frontend | Next.js (15K lines) | Open-WebUI (config only) |
| Backend | FastAPI (78 endpoints) | FastAPI (30 tools) |
| Database | PostgreSQL | PostgreSQL (shared) |
| Email | Gmail API (sanitized) | SnappyMail (IMAP) |
| AI | OpenAI hardcoded | Multi-model via Open-WebUI |
| Memory | agent_memory table | Qdrant + RAG |
| Chat | Component-based | Unified (Open-WebUI) |
| Calendar | Google Calendar API | Google Calendar API (reuse) |
| Vision | RAP Mobile only | All images (Vision AI) |
| Deploy | Manual start scripts | Docker Compose |

**Lines of Code Estimate**:
- v1: ~20K lines (15K frontend + 5K backend)
- v2: ~3K lines (0 frontend + 3K backend tools)

**Maintenance Burden**:
- v1: High (frontend + backend + sync + state)
- v2: Low (backend tools only, Open-WebUI handles UI)

---

**Built with lessons learned from v1. Keep it simple. Leverage ecosystems. Ship incrementally.**
