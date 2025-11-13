# 🌶️ ChiliHead OpsManager Unified

> **The Ultimate Restaurant Operations Platform**
> AI-Powered Email Triage + ChiliHead 5-Pillar Delegation System + Operations Chat Assistant

---

## 🎯 What This Does

**ChiliHead OpsManager Unified** combines the best of restaurant operations management:

1. **AI Email Triage** - GPT-4 powered email analysis for restaurant operations
2. **ChiliHead Commitments** - 5-Pillar delegation system for leadership development
3. **Smart Todo Lists** - Eisenhower Matrix task management with deadlines
4. **Operations Chat** - AI assistant to discuss and plan your daily operations
5. **Seamless Workflow** - Extract tasks from emails → Delegate with purpose → Chat for guidance

Built specifically for operations managers who need to:
- Process high volumes of operational emails quickly
- Delegate effectively using proven leadership frameworks
- Track accountability and follow-through
- Get intelligent answers about daily operations
- Turn email chaos into actionable plans

---

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI** REST API
- **PostgreSQL** database (Docker) for persistent storage
- **Gmail API** integration for email access
- **OpenAI GPT-4** for intelligent email analysis and chat
- **SQLAlchemy** ORM with Alembic migrations
- **OAuth 2.0** authentication flow

### Frontend (Next.js/React/TypeScript)
- **Next.js 14** with App Router
- **React** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons

### Database (PostgreSQL)
- **Docker containerized** PostgreSQL 15
- **Persistent storage** for tasks, emails, delegations, and chat history
- **Alembic migrations** for schema management

---

## 📁 Project Structure

```
chilihead-opsmanager-unified/
├── server/                     # Python/FastAPI backend
│   ├── app.py                 # Main FastAPI application
│   ├── models.py              # SQLAlchemy database models
│   ├── database.py            # Database connection & sessions
│   ├── routes/                # API routes
│   │   ├── oauth.py           # Gmail OAuth flow
│   │   ├── mail.py            # Email/thread endpoints
│   │   ├── state.py           # Task & state management
│   │   ├── tasks.py           # Todo list API
│   │   ├── delegations.py     # ChiliHead delegations API
│   │   └── operations_chat.py # AI chat assistant API
│   ├── services/              # Business logic
│   │   ├── smart_assistant.py # GPT-4 AI analysis
│   │   ├── gmail.py           # Gmail integration
│   │   ├── state_manager.py   # Task/email state
│   │   └── deadline_scanner.py # Deadline detection
│   └── alembic/               # Database migrations
│       └── versions/          # Migration files
│
├── client/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx          # Main dashboard with tabs
│   │   ├── components/
│   │   │   ├── TriagePage.tsx       # Email triage interface
│   │   │   ├── TodoPage.tsx         # Todo list management
│   │   │   └── OperationsChat.tsx   # Chat assistant UI
│   │   ├── delegations/      # ChiliHead delegation system
│   │   └── api/              # Next.js API routes
│   └── components/
│
├── docker-compose.yml         # PostgreSQL database setup
└── docs/                      # Documentation
    └── CHAT_FEATURE_COMPLETE.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Gmail API credentials (OAuth 2.0)
- OpenAI API key

### 1. Database Setup (PostgreSQL in Docker)

```bash
# Start PostgreSQL database
docker-compose up -d

# Verify it's running
docker ps
```

This creates a PostgreSQL database at `localhost:5432`:
- **Database**: `openinbox_dev`
- **User**: `openinbox`
- **Password**: `devpass123`

### 2. Backend Setup

```bash
cd server
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

Create `.env` file in `server/`:
```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
DATABASE_URL=postgresql://openinbox:devpass123@localhost:5432/openinbox_dev
```

Run database migrations:
```bash
cd server
alembic upgrade head
```

### 3. Frontend Setup

```bash
cd client
npm install
```

Create `.env.local` in `client/`:
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### 4. Running the App

**Start Database:**
```bash
docker-compose up -d
```

**Backend:**
```bash
cd server
.venv\Scripts\activate
python -m uvicorn app:app --reload --port 8000
```

**Frontend:**
```bash
cd client
npm run dev
```

Then open: **http://localhost:3001**

---

## 🔑 Key Features

### ✅ AI Email Triage
- GPT-4 powered email analysis
- Priority scoring and categorization
- Smart task extraction with deadlines
- Daily operations briefing
- Automatic deadline scanning

### ✅ Operations Chat Assistant (NEW!)
- **AI-powered chat** about your daily operations
- **Context-aware responses** using daily digest and current tasks
- **Full conversation history** stored in PostgreSQL
- **Session management** - pick up where you left off
- **Ask anything**: priorities, deadlines, delegations, planning

Example questions:
- "What's most urgent today?"
- "Show me all my deadlines"
- "Who do I need to follow up with?"
- "When is the manager schedule due?"
- "Help me plan my next 2 hours"

### ✅ Smart Todo List
- Eisenhower Matrix prioritization
- Deadline tracking with date/time
- Task status management
- Google Calendar integration ready
- Bulk add from email analysis

### ✅ ChiliHead 5-Pillar Delegations
- **Sense of Belonging** - Create ownership
- **Clear Direction** - Define success
- **Preparation** - Provide resources
- **Support** - Enable success
- **Accountability** - Follow through

### ✅ Smart Workflow
1. Gmail → AI analyzes emails
2. Extract actionable tasks with deadlines
3. Add to todo list or delegate
4. Chat with AI about priorities
5. Track and follow up

---

## 🗄️ Database Schema

### Tables
- **`email_state`** - Email read/acknowledged tracking
- **`tasks`** - Todo list items with deadlines and priorities
- **`delegations`** - ChiliHead 5-pillar delegation tracking
- **`chat_sessions`** - Operations chat conversation sessions
- **`chat_messages`** - Individual chat messages with context
- **`watch_config`** - Email priority configuration
- **`ai_analysis_cache`** - Cached AI analysis results

All data persisted to PostgreSQL in Docker for reliability and scalability.

---

## 🌶️ ChiliHead Commitment Philosophy

Every delegation follows the proven 5-Pillar framework:

1. **🤝 Sense of Belonging** - Make them feel valued
2. **🎯 Clear Direction** - Define what success looks like
3. **📚 Preparation** - Provide tools and training
4. **🛠️ Support** - Ongoing help available
5. **✅ Accountability** - Crystal-clear follow-up

---

## 💬 Using the Operations Chat

The chat assistant is available on every page (floating button in bottom-right):

**Features:**
- Full conversation history from PostgreSQL
- Context-aware about your operations
- Knows current tasks, deadlines, and priorities
- Helps with planning and prioritization
- Tracks token usage and session metrics

**How it works:**
1. Click the chat button
2. Ask questions about your operations
3. Get intelligent, context-aware responses
4. Conversation automatically saved to database
5. Return anytime - history is preserved

---

## 🔧 Maintenance

### Database Migrations
```bash
# Create a new migration
cd server
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Backup Database
```bash
# Backup
docker exec chilihead_opsmanager_db pg_dump -U openinbox openinbox_dev > backup.sql

# Restore
docker exec -i chilihead_opsmanager_db psql -U openinbox openinbox_dev < backup.sql
```

### Stop/Start Database
```bash
# Stop
docker-compose down

# Start
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## 🔒 Security & Privacy

- **Private Repository** - Keep this private
- **OAuth 2.0** - Secure Gmail access
- **PostgreSQL** - Database credentials in environment variables
- **Docker Isolation** - Database runs in container
- **.gitignore** - Sensitive data excluded
- **No Data Sharing** - Everything stays on your machine

---

## 📊 Technology Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy ORM
- Alembic migrations
- PostgreSQL 15
- OpenAI GPT-4
- Gmail API
- OAuth 2.0

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide React icons

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL in container
- Local development environment

---

## 📞 Contact

**John Olenski** - Managing Partner
Chili's Auburn Hills (#605)
📧 John.olenski@gmail.com
🐙 GitHub: [@johnohhh1](https://github.com/johnohhh1)

---

## 📄 License

Private & Confidential - All Rights Reserved

---

**Built with ❤️ by a GM who believes great people deserve great tools.**

*🌶️ "Excellence Through Leadership & Accountability"*
