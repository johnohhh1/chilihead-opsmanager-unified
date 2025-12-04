# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
**ChiliHead OpsManager** - AI-powered email triage and leadership delegation tracking system for restaurant operations management.

## Tech Stack
- **Backend**: FastAPI (Python 3.11+) on port **8002**
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS on port **3001**
- **Database**: PostgreSQL 15 in Docker on port **5432**
- **AI**: OpenAI GPT-4o for email analysis, chat, and daily digests
- **Email**: Gmail API integration with OAuth2
- **Migrations**: Alembic for database schema management

## Port Configuration (CRITICAL)
- Backend: `http://localhost:8002`
- Frontend: `http://localhost:3001`
- Database: `postgresql://localhost:5432`
- SnappyMail: `http://localhost:8888` (webmail interface)

## Development Commands

### Database
```bash
# Start PostgreSQL in Docker
scripts\start_database.bat  # or: docker-compose up -d

# Stop database
scripts\stop_database.bat  # or: docker-compose down

# Run migrations (apply schema changes)
cd server
.venv\Scripts\activate
alembic upgrade head

# Create new migration
alembic revision -m "description of changes"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Database backup
docker exec openinbox-postgres pg_dump -U openinbox openinbox_dev > backup.sql

# Database restore
docker exec -i openinbox-postgres psql -U openinbox openinbox_dev < backup.sql
```

### Backend Development
```bash
# Install dependencies (in .venv)
cd server
.venv\Scripts\activate
pip install -r requirements.txt

# Run development server
.venv\Scripts\python -m uvicorn app:app --reload --port 8002

# Test database connection
.venv\Scripts\python database.py

# Initialize database tables
.venv\Scripts\python -c "from database import init_db; init_db()"
```

### Frontend Development
```bash
# Install dependencies
cd client
npm install

# Run development server
npm run dev  # Starts on port 3001

# Build for production
npm run build

# Run production build
npm start
```

### Unified Startup
```bash
# Start everything at once (backend + frontend + Ollama)
scripts\start_unified.bat
```

## Architecture

### High-Level Structure
```
Backend (FastAPI)
├── app.py                      # Main application, route registration
├── models.py                   # SQLAlchemy ORM models
├── database.py                 # Database connection & session management
├── routes/                     # API route handlers
│   ├── oauth.py                # Gmail OAuth flow
│   ├── mail.py                 # Email fetching/threading
│   ├── inbox.py                # Smart Inbox with AI triage
│   ├── tasks.py                # Todo list management
│   ├── delegations.py          # ChiliHead 5-pillar system
│   ├── operations_chat.py      # AI chat assistant
│   └── calendar.py             # Google Calendar integration
├── services/                   # Business logic layer
│   ├── agent_memory.py         # Centralized AI agent memory (CRITICAL)
│   ├── smart_assistant.py      # AI triage & daily digest
│   ├── ai_triage.py            # Email analysis
│   ├── gmail.py                # Gmail API wrapper
│   ├── email_sync.py           # Email caching & sync
│   ├── state_manager.py        # In-memory task state
│   └── model_provider.py       # Multi-model support (OpenAI, Anthropic)
└── alembic/                    # Database migrations
    └── versions/               # Migration files

Frontend (Next.js)
├── app/
│   ├── page.tsx                # Main dashboard
│   ├── layout.tsx              # Root layout with dark mode
│   ├── components/
│   │   ├── SmartInboxPage.tsx  # Email triage UI
│   │   ├── TodoPage.tsx        # Task management
│   │   ├── OperationsChat.tsx  # AI chat interface
│   │   └── PortalPage.tsx      # RAP Mobile dashboard
│   └── api/                    # Next.js API routes (proxy to backend)
```

### Agent Memory System (CRITICAL ARCHITECTURE)
The **Agent Memory System** is a PostgreSQL-based coordination layer that enables all AI agents (email triage, daily digest, chat) to share context and avoid redundant work.

**Key Concepts:**
- **AgentMemory** table: Stores every AI action (email analyzed, task created, deadline identified)
- **Memory Search**: Agents query recent memories to understand what other agents have done
- **Resolution Tracking**: When user says "Pedro was handled", system marks related memories as `[RESOLVED]`
- **Entity Extraction**: Summaries automatically extract entity names for fuzzy search

**Usage Pattern:**
```python
from services.agent_memory import AgentMemoryService

# Record an AI action
AgentMemoryService.record_event(
    db=db,
    agent_type='smart_triage',
    event_type='email_analyzed',
    summary='Analyzed urgent payroll email from Pedro',
    context_data={'email': email_data},
    key_findings={'priority': 'urgent', 'deadline': '2025-12-10'},
    email_id=thread_id,
    model_used='gpt-4o'
)

# Get recent context for coordination
context = AgentMemoryService.get_coordination_context(db, hours=24)

# Mark items as resolved
AgentMemoryService.mark_resolved(db, summary_text='Pedro', annotation='Handled by user')
```

**Why This Matters:**
- Without this, AI agents would re-flag resolved items in daily digests
- Enables natural language resolution ("pedro was handled" → marks memories as resolved)
- Provides cross-agent context awareness

### Email Analysis Pipeline
1. **Fetch**: Gmail API fetches emails via `services/gmail.py`
2. **Cache**: Raw email stored in `EmailCache` table for offline access
3. **Triage**: AI analyzes via `smart_triage()` → structured extraction
4. **Cache Analysis**: Result stored in `EmailAnalysisCache` with trust scores
5. **Memory**: Action recorded in `AgentMemory` for coordination
6. **Display**: Smart Inbox shows prioritized emails with AI insights

### Multi-Model Support
The system supports multiple AI providers via `ModelProvider` class:
- **OpenAI**: GPT-4o, GPT-4o-mini (trusted, production)
- **Anthropic**: Claude Sonnet, Claude Haiku (trusted)
- **Ollama**: Local models via HTTP (experimental)

Model selection happens at request time (user selects from dropdown in UI).

## Database Models

### Core Tables
- **email_cache** - Mirror of Gmail emails (offline access)
- **email_analysis_cache** - AI analysis results with trust scores
- **email_state** - Read/acknowledged tracking
- **tasks** - Todo list with Eisenhower Matrix categories
- **delegations** - ChiliHead 5-pillar delegation tracking
- **agent_memory** - Centralized AI agent coordination (CRITICAL)
- **agent_sessions** - Batch work tracking (e.g., daily digest generation)
- **chat_sessions** - Operations chat conversation history
- **chat_messages** - Individual chat messages with context
- **dismissed_items** - User-dismissed digest items (prevent re-flagging)

### Important Constraints
- **gmail_attachment_id** in `email_attachments` is TEXT (not VARCHAR) - Gmail IDs can exceed 255 chars
- **agent_memory.summary** supports `[RESOLVED]` prefix for filtering
- All UUIDs generated via `generate_uuid()` helper

## Design & Branding
- **Dark Mode ONLY** - User lives in a dark mode world
- **Chili's Red**: `#C8102E` (use for buttons, accents, branding)
- **Background**: Gray-900/Gray-800 gradients
- **Text**: White/Gray-300 for readability
- **Cards**: Gray-800 with Gray-700 borders

## User Preferences
- User has dyslexia - prioritize readability and clear layouts
- Personal project for operations management
- Prefers concise, functional code over excessive documentation
- Dark mode is mandatory across all pages

## Key Features
1. **Smart Inbox** - AI analyzes emails with context understanding (not just keywords)
2. **Todo List** - Task management with Eisenhower Matrix categories
3. **Delegations** - 5-Pillar ChiliHead methodology for team development
4. **Operations Chat** - AI assistant aware of daily digest and current tasks
5. **Daily Brief** - Morning operations summary in Eastern Time
6. **RAP Mobile Portal** - Vision AI extracts metrics from dashboard screenshots

## Environment Variables

### Backend (.env in server/)
```bash
# Required
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
DATABASE_URL=postgresql://openinbox:devpass123@localhost:5432/openinbox_dev

# Optional
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_BASE_URL=http://localhost:11434
```

### Frontend (.env.local in client/)
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8002
```

## Important Implementation Notes
- **Backend runs in `.venv` virtual environment** - Always install packages there
- Daily digest uses Eastern Time (`pytz` timezone awareness)
- Frontend proxies `/api/backend/*` to port 8002
- Chat history persists to PostgreSQL (not in-memory)
- Navigation tabs on all pages for easy switching
- Daily Brief regenerates fresh each time (timestamp cache-busting)
- Agent Memory System enables AI coordination (see Architecture section)

## Gmail API Integration
- **OAuth Flow**: User authorizes via `/authorize-gmail`, callback at `/oauth2callback`
- **Token Storage**: Saved to `token.pickle` in server directory
- **API Usage**: `services/gmail.py` wraps Google API client
- **Attachment Handling**: Inline images served via `/api/attachments/{id}`

## Common Development Workflows

### Adding a New API Endpoint
1. Create route handler in `routes/` directory
2. Import and register router in `app.py`
3. Add corresponding service logic in `services/`
4. Update database models if needed (and create migration)
5. Frontend proxies via `client/app/api/backend/[...path]/route.ts`

### Creating a Database Migration
```bash
cd server
.venv\Scripts\activate

# Make changes to models.py first
# Then create migration
alembic revision --autogenerate -m "add new_field to tasks table"

# Review generated migration in alembic/versions/
# Apply migration
alembic upgrade head
```

### Adding AI Agent Memory Events
When adding new AI features, record actions to agent memory:
```python
from services.agent_memory import AgentMemoryService

# After AI completes work
AgentMemoryService.record_event(
    db=db,
    agent_type='your_agent',  # triage, daily_brief, operations_chat
    event_type='your_event',  # email_analyzed, task_created, etc.
    summary='Human-readable what happened',
    context_data={'full': 'context'},
    key_findings={'important': 'data'},
    model_used='gpt-4o'
)
```

## Recent Changes (2025)
- **AUBS Personality**: Stripped down to be supportive, not condescending
  - No more "Real talk", "Here's the deal" lectures
  - No fake procedures or requirements
  - If user says it's resolved, it's resolved
- **RAP Mobile Images Fixed**: Database column `gmail_attachment_id` changed to TEXT (was VARCHAR(255))
  - Gmail attachment IDs can be >255 characters
  - Inline images now display in Smart Inbox
- **Memory Search Improved**: Triage summaries extract entity names (Pedro, Hannah, Blake, etc)
  - When you say "pedro was handled", memory system can find and resolve it
- **Agent Memory System**: Centralized PostgreSQL-based memory for AI coordination
  - Email triage, daily brief, and chat agents share context
  - Memory updates propagate across all agents
- Implemented full dark mode (Oct 20, 2025)
- Fixed AI timezone to use Eastern Time for correct dates

## Common Pitfalls
- ❌ Don't use port 8000 (backend is on 8002)
- ❌ Don't install packages globally (use `.venv`)
- ❌ Don't create bright color schemes (dark mode only)
- ❌ Don't forget timezone awareness for date/time operations
- ❌ Don't make AUBS condescending or preachy (user hates lectures)
- ❌ Don't make up fake procedures or requirements
- ❌ Don't modify agent memory summaries directly (use `mark_resolved()`)
- ❌ Don't forget to record AI actions to agent_memory table

## AUBS Personality Guidelines
**DO:**
- State facts clearly and directly
- Provide specific details (who, what, when, where)
- Trust John to make his own decisions
- If John says something is resolved, it's resolved

**DON'T:**
- Use phrases like "Real talk", "Here's the deal", "Let's knock out"
- Lecture about why things matter (John already knows)
- Tell John what he "needs to do" unless he asks for advice
- Make up procedures or requirements that don't exist
- Argue when John corrects you

## File Locations Reference

### Key Backend Files
- `app.py` - Main FastAPI app, route registration
- `models.py` - All SQLAlchemy models (single file)
- `database.py` - DB connection & session factory
- `services/agent_memory.py` - AI agent coordination (CRITICAL)
- `services/smart_assistant.py` - AI triage & daily digest
- `services/gmail.py` - Gmail API wrapper
- `services/email_sync.py` - Email caching & sync
- `routes/inbox.py` - Smart Inbox API
- `routes/operations_chat.py` - Chat assistant API

### Key Frontend Files
- `app/page.tsx` - Main dashboard
- `app/components/SmartInboxPage.tsx` - Email triage UI
- `app/components/OperationsChat.tsx` - Chat interface
- `app/components/TodoPage.tsx` - Task management
- `app/api/backend/[...path]/route.ts` - Backend proxy

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker ps | findstr openinbox-postgres

# Restart database
docker-compose down && docker-compose up -d

# View database logs
docker-compose logs -f postgres
```

### Backend Not Starting
```bash
# Activate virtual environment first
cd server
.venv\Scripts\activate

# Check for missing dependencies
pip install -r requirements.txt

# Test database connection
python database.py
```

### Frontend Build Errors
```bash
cd client
npm install  # Reinstall dependencies
npm run dev  # Try development mode first
```

## Production Deployment Notes
- Set `DATABASE_URL` to production PostgreSQL instance
- Configure `.env` with production API keys
- Use `npm run build` for frontend (Next.js static/server rendering)
- Consider Nginx reverse proxy for frontend and backend
- Enable PostgreSQL backups (pg_dump scheduled)
- Monitor agent_memory table size (consider archiving old records)
