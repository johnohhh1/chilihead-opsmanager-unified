# ChiliHead OpsManager v2.0 - Vision Document

> **Building the Ultimate AI-Native Operations Platform**

---

## The Problem

Restaurant operations managers drown in email chaos:
- 50-100+ operational emails per day
- Critical deadlines buried in threads
- Team coverage gaps hidden in messages
- Leadership communications mixed with routine noise
- Invoice images that need manual data entry
- Calendar conflicts and missed follow-ups
- Context switching between 10+ tools

**Current solutions fail because:**
- Gmail sanitization loses formatting and images
- Assistants are blind to each other's context
- Memory issues prevent long-term understanding
- Tools require manual context re-entry
- No unified semantic understanding

---

## The Vision

**AUBS (Auburn Hills Business System)** - Your AI operations partner who:

- **Sees everything** - Emails, calendar, todos, delegations, team status
- **Remembers everything** - Context persists across conversations, days, weeks
- **Acts on your behalf** - "Add that to my calendar" - she knows what "that" means
- **Reads like you do** - OCR invoices, receipts, schedules from images
- **Thinks ahead** - Proactive daily briefings: "Here's what needs attention today"
- **Speaks naturally** - Conversational, not robotic. Understands intent.
- **Works 24/7** - Never forgets, never drops the ball

**Built on Open-WebUI ecosystem** - The only platform with:
- Multi-model brain swapping (GPT-4, Claude, Llama, cloud models)
- Native vision capabilities for reading images
- Tools/skills/MCP for seamless integrations
- RAG system for long-term memory
- Centralized semantic understanding

---

## Core Philosophy

### 1. AI-Native Architecture
**Not:** Traditional web app with AI features
**But:** AI-first platform where natural language is the interface

Everything happens through conversation:
- "What's urgent today?" → AUBS reads emails, calendar, todos, synthesizes
- "Show me that invoice" → Opens SnappyMail, screenshots, OCR, presents
- "Add reviewing it to my todos" → Maintains context, executes
- "When is Blake's shift?" → Checks schedule, responds
- "Send the team a reminder about tomorrow" → Composes, sends via Google Chat

### 2. Centralized Semantic Understanding
One conversation thread with full context:
- No context switching between apps
- AUBS remembers what "that", "it", "the one from yesterday" means
- All data sources available in one semantic space
- Memory persists across sessions

### 3. Ecosystem Over Custom Code
Leverage Open-WebUI's superpowers:
- Vision built-in (no custom OCR pipeline)
- Multi-model support (pick best brain per task)
- Tools/skills framework (no custom UI framework)
- RAG system (no custom memory architecture)
- MCP integrations (standard protocol)

**Result:** 80% less code, 10x more capable

### 4. SnappyMail for Email Truth
No sanitization. No lost formatting. No broken images.
- IMAP/SMTP direct to Gmail
- Filter work emails (brinker.com, chilis.com, hotschedules.com)
- Full HTML rendering
- Screenshot + Vision for image data extraction

---

## User Experience Vision

### Morning Routine
```
User: "AUBS, good morning. What's my day look like?"

AUBS: "Good morning! Here's what needs your attention:

🔴 URGENT (Due Today):
- Manager schedule due by 3pm (from Stephanie's email)
- Blake called out - dinner shift needs coverage
- Invoice review: Sysco delivery $2,847.32 (I can read the details if you want)

📅 CALENDAR:
- 10am: District call with RVP
- 2pm: Prep walk with Carmen
- 4pm: Team huddle

✅ COMPLETED YESTERDAY:
- Submitted P&L review
- Followed up with Devon on training
- Added 3 delegation commitments

💭 SHOULD FOCUS ON:
1. Finding Blake's coverage (call Tiffany?)
2. Manager schedule (you have draft from last week)
3. Reviewing that Sysco invoice before approving

Want me to pull up any of these?"
```

### During the Day
```
User: "Show me that Sysco invoice"

AUBS: [Opens SnappyMail tab, screenshots email, uses GPT-4V]

"Here's what I see:
- Invoice #: SYS-247832
- Date: Nov 22, 2024
- Total: $2,847.32
- Items: Chicken (40 cases), Produce ($847), Frozen ($612)...
- Due: Net 30 (Dec 22)

Want me to add 'Review Sysco invoice' to your todos or flag for approval?"

User: "Add it to high priority todos"

AUBS: "Done. Added to high-priority with deadline Dec 22."
```

### Delegation Flow
```
User: "I need to delegate dinner coverage to Tiffany"

AUBS: "Got it. Using the ChiliHead 5-Pillar system. Let me help you structure this:

1. SENSE OF BELONGING: How will you make Tiffany feel valued?
2. CLEAR DIRECTION: What does success look like?
3. PREPARATION: What does she need?
4. SUPPORT: How will you help?
5. ACCOUNTABILITY: When's the follow-up?

Want to go through these together or should I draft based on past delegations?"

User: "Draft it"

AUBS: [Creates delegation with all 5 pillars filled in, saves to database]

"Created delegation for Tiffany - Blake's coverage.
Scheduled follow-up for tomorrow 5pm.
Want me to send her a Google Chat message about it?"
```

---

## Core Capabilities

### 1. Email Intelligence
**Via AUBS Backend + SnappyMail**

- Email ingestion filtering (work domains only)
- AI-powered triage (priority, category, urgency)
- Deadline extraction with date/time parsing
- Task identification with context
- Full email viewing in SnappyMail (no sanitization)
- Image OCR via screenshot + vision models
- Email context in conversation memory

**Tools:**
- `get_emails(filter, limit)` - Retrieve emails
- `triage_emails()` - AI analysis of recent emails
- `read_email_image(email_id)` - Screenshot + OCR
- `get_email_context(email_id)` - Full thread context

### 2. Task Management
**Eisenhower Matrix + Calendar Integration**

- Smart todo list with priority quadrants
- Deadline tracking with date/time
- Bulk task creation from email analysis
- Google Calendar sync
- Context-aware task suggestions
- Delegation tracking (5-pillar system)

**Tools:**
- `get_todos(status, priority)` - Retrieve tasks
- `add_task(title, priority, deadline, notes)` - Create task
- `update_task(task_id, updates)` - Modify task
- `delegate_task(to, task, five_pillars)` - Create delegation
- `get_delegations(status)` - Track delegations

### 3. Calendar Intelligence
**Google Calendar API Integration**

- Read upcoming events
- Check for conflicts
- Add events from emails
- Suggest optimal meeting times
- Deadline awareness
- Recurring event management

**Tools:**
- `get_calendar(start_date, end_date)` - Retrieve events
- `add_calendar_event(title, datetime, attendees)` - Create event
- `check_availability(datetime)` - Conflict check
- `find_meeting_time(attendees, duration)` - Suggest times

### 4. Daily Briefing
**AUBS Proactive Summary**

Synthesizes across all data sources:
- Urgent emails requiring action
- Today's calendar events
- Overdue/upcoming deadlines
- Pending delegations needing follow-up
- Yesterday's completed items
- Suggested priorities

**Tool:**
- `get_daily_brief(date, focus_areas)` - Generate comprehensive briefing

### 5. Team Communication
**Google Chat Integration**

- Send messages to team members
- Group notifications
- Shift coverage requests
- Delegation notifications
- Reminder messages

**Tool:**
- `send_team_message(to, message, channel)` - Send via Google Chat

### 6. Vision + OCR
**Image Understanding**

- Read invoices, receipts, schedules
- Extract data from screenshots
- Parse handwritten notes
- Table/spreadsheet data extraction
- Menu/flyer information

**Tools:**
- `read_email_image(email_id)` - Screenshot + vision
- `ocr_document(image_url)` - Direct OCR
- `extract_invoice_data(email_id)` - Structured invoice parsing

### 7. Long-Term Memory
**RAG + Vector Database**

- Conversation history across sessions
- Semantic search of past operations
- Learning patterns and preferences
- Context-aware suggestions
- "Remember when..." queries

**Powered by:**
- Open-WebUI conversation history
- Qdrant vector database
- Redis session cache
- PostgreSQL persistent storage

---

## Why Open-WebUI?

### Better Than ChatGPT Desktop
- ✅ Can read images in emails (ChatGPT can't)
- ✅ Can display items to add (ChatGPT just talks about it)
- ✅ Multi-model support (not locked to OpenAI)
- ✅ Self-hosted (full control, no data sharing)
- ✅ RAG system built-in
- ✅ MCP/Tools/Skills framework

### Better Than Claude Desktop
- ✅ Has tools/skills ecosystem (Claude focused elsewhere)
- ✅ Multi-model (Claude is single-provider)
- ✅ Vision capabilities (Claude has it but limited access)
- ✅ Calendar/task integrations ready
- ✅ Community extensions

### Better Than Custom UI
- ✅ No sanitization needed (native email viewing)
- ✅ Centralized semantic understanding
- ✅ Built-in memory/RAG
- ✅ Easier to maintain (80% less code)
- ✅ Natural language > clicking buttons
- ✅ Adaptable (new tools instantly available)

---

## Technical Architecture

### High-Level Flow
```
┌─────────────────────────────────────────────────┐
│         Open-WebUI (Port 8080)                  │
│         Central AI-Native Interface             │
│                                                  │
│  - Chat with AUBS (conversational)              │
│  - Tools (get_emails, add_task, etc.)           │
│  - Skills (daily_brief, triage, delegate)       │
│  - Vision (read images)                         │
│  - Memory (RAG + conversation history)          │
│  - Multi-Model (GPT-4, Claude, Llama)           │
└──────────────┬──────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│  AUBS Backend (Port 5000)                       │
│  FastAPI + Tool/Skill Provider                  │
│                                                  │
│  API Endpoints (called as tools):               │
│  - GET  /api/emails                             │
│  - POST /api/emails/triage                      │
│  - GET  /api/emails/{id}/image                  │
│  - GET  /api/tasks                              │
│  - POST /api/tasks                              │
│  - GET  /api/calendar                           │
│  - POST /api/calendar/events                    │
│  - POST /api/delegations                        │
│  - GET  /api/brief                              │
│  - POST /api/google-chat/send                   │
└──────────────┬──────────────────────────────────┘
               │
      ┌────────┼────────┬──────────┬──────────┐
      ▼        ▼        ▼          ▼          ▼
  ┌────────┐ ┌──────┐ ┌───────┐ ┌──────┐ ┌──────────┐
  │ Postgre│ │Qdrant│ │ Redis │ │ NATS │ │ SnappyMail│
  │   SQL  │ │Vector│ │ Cache │ │Events│ │  (8888)  │
  └────────┘ └──────┘ └───────┘ └──────┘ └──────────┘

External Integrations:
  ├─→ Gmail IMAP/SMTP (email ingestion)
  ├─→ Google Calendar API
  └─→ Google Chat API
```

### Data Flow Example
```
User: "What's urgent today?"
    ↓
Open-WebUI calls tool: get_daily_brief()
    ↓
AUBS Backend:
  ├─→ Queries PostgreSQL (tasks, delegations)
  ├─→ Queries Qdrant (email embeddings)
  ├─→ Calls Google Calendar API
  ├─→ Retrieves from Redis cache
  ├─→ Synthesizes with LLM
  └─→ Returns structured brief
    ↓
Open-WebUI presents to user
    ↓
User: "Show me that invoice"
    ↓
Open-WebUI calls: read_email_image(email_id)
    ↓
AUBS Backend:
  ├─→ Opens SnappyMail via MCP/Playwright
  ├─→ Takes screenshot of email
  ├─→ Sends to GPT-4V
  ├─→ Extracts structured data
  └─→ Returns invoice details
    ↓
Open-WebUI displays + keeps in context
    ↓
User: "Add reviewing it to todos"
    ↓
AUBS knows "it" = that invoice (context!)
    ↓
Calls: add_task(title="Review Sysco invoice", ...)
```

---

## Success Metrics

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
- ✅ Shared context across all operations
- ✅ Memory issues resolved
- ✅ Google Calendar integrated
- ✅ Google Chat messaging works
- ✅ Multi-model support (not locked to GPT-4)

### AI-Native Wins
- ✅ Natural language for all operations
- ✅ Proactive insights ("You should...")
- ✅ Context maintained across sessions
- ✅ Fewer clicks, more conversation
- ✅ Learns preferences over time

---

## Non-Goals (Keeping it Simple)

**Not Building:**
- ❌ Custom React frontend (Open-WebUI is the interface)
- ❌ Complex multi-agent orchestration (Dolphin removed)
- ❌ DAG workflows (unnecessary complexity)
- ❌ Visual debugging tools (UITARS removed)
- ❌ Text messaging via Twilio (use Google Chat instead)
- ❌ GPU acceleration (not needed for current use case)
- ❌ Custom memory architecture (use Open-WebUI + Qdrant)

**Why?**
- Leverage existing ecosystems (80% less code)
- Focus on business logic, not infrastructure
- Maintainable by one person
- Scalable without complexity

---

## Development Roadmap

### Phase 1: Foundation (Current)
- ✅ SnappyMail configured with Gmail
- ✅ Email ingestion filtering work emails
- ✅ AUBS backend with SimpleOrchestrator
- ✅ EmailAnalyzer (Claude/GPT-4)
- ✅ AUBS chat service
- ✅ Basic Open-WebUI setup

### Phase 2: Core Tools (Next 2 weeks)
- [ ] Email tools (get_emails, triage, read_image)
- [ ] Task tools (CRUD operations)
- [ ] Calendar tools (Google Calendar API)
- [ ] Daily brief tool
- [ ] PostgreSQL schema (tasks, delegations, email_state)

### Phase 3: Integrations (Week 3-4)
- [ ] Google Chat integration
- [ ] SnappyMail MCP/screenshot capability
- [ ] Vision OCR for invoices/receipts
- [ ] RAG system for email history
- [ ] Long-term memory (Qdrant)

### Phase 4: ChiliHead Features (Week 5-6)
- [ ] 5-pillar delegation system
- [ ] Daily briefing skill
- [ ] Proactive insights
- [ ] Team management features
- [ ] Deadline tracking + notifications

### Phase 5: Polish (Week 7-8)
- [ ] Performance optimization
- [ ] Error handling
- [ ] Testing
- [ ] Documentation
- [ ] Deployment automation

---

## Why This Will Work

### 1. Built on What Works
- v1 system is proven (used daily in production)
- Not rebuilding from scratch
- Fixing specific, known problems

### 2. Leverage Ecosystems
- Open-WebUI handles 80% of the hard stuff
- Google APIs are mature and reliable
- SnappyMail is battle-tested

### 3. AI-Native from the Start
- Natural language > custom UI
- Conversation > clicks
- Context > context switching

### 4. Realistic Scope
- No over-engineering
- No unnecessary complexity
- Focus on real problems

### 5. One Developer, Maintainable
- Simple architecture
- Standard tools
- Clear separation of concerns

---

## The End Result

**John asks AUBS:**
> "What should I focus on today?"

**AUBS responds** with full context from emails, calendar, todos, and past conversations:
> "Here's what needs your attention: Blake's shift coverage is critical, manager schedule due by 3pm, and that Sysco invoice needs review before Friday. Want me to pull up the invoice details or help you find Blake's coverage?"

**One conversation. Full context. Natural language. All data sources.**

That's the vision.

---

**Built with lessons learned: Start simple, leverage ecosystems, focus on real problems.**

*"The best operations assistant is one that thinks like you, sees what you see, and acts when you need it."*
