# ChiliHead OpsManager - Project Memory

## Project Overview
**ChiliHead OpsManager** - AI-powered email triage and leadership delegation tracking system for restaurant operations management.

## Tech Stack
- **Backend**: FastAPI (Python 3.11+) on port **8002**
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS on port **3001**
- **Database**: PostgreSQL 15 in Docker on port **5432**
- **AI**: OpenAI GPT-4o for email analysis, chat, and daily digests
- **Email**: Gmail API integration with OAuth2

## Port Configuration (CRITICAL)
- Backend: `http://localhost:8002`
- Frontend: `http://localhost:3001`
- Database: `postgresql://localhost:5432`

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
1. **Email Triage** - AI analyzes emails with context understanding (not just keywords)
2. **Todo List** - Task management with Eisenhower Matrix categories
3. **Delegations** - 5-Pillar ChiliHead methodology for team development
4. **Operations Chat** - AI assistant aware of daily digest and current tasks
5. **Daily Brief** - Morning operations summary in Eastern Time

## Database Models
- `chat_sessions` - Chat history with context snapshots
- `chat_messages` - Individual messages with token tracking
- Task state management (in-memory, persisted to DB)
- Email thread state (acknowledged, analyzed, tasks_added)

## Important Implementation Notes
- **Backend runs in `.venv` virtual environment** - Always install packages there
- Daily digest uses Eastern Time (`pytz` timezone awareness)
- Frontend proxies `/api/backend/*` to port 8002
- Chat history persists to PostgreSQL (not in-memory)
- Navigation tabs on all pages for easy switching
- Daily Brief regenerates fresh each time (timestamp cache-busting)

## Startup Commands
- Database: `scripts/start_database.bat`
- Backend + Frontend: `start_unified.bat`
- Backend only: `cd server && .venv/Scripts/python -m uvicorn app:app --reload --port 8002`
- Frontend only: `cd client && npm run dev`

## Recent Changes
- Implemented full dark mode (Oct 20, 2025)
- Changed Daily Operations Brief to cobalt blue (less intense)
- Fixed AI timezone to use Eastern Time for correct dates
- Added navigation tabs to all pages
- Fixed daily digest caching issue

## Common Pitfalls
- ❌ Don't use port 8000 (backend is on 8002)
- ❌ Don't install packages globally (use `.venv`)
- ❌ Don't create bright color schemes (dark mode only)
- ❌ Don't forget timezone awareness for date/time operations
