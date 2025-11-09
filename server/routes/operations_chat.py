"""
Operations Chat API - Interactive AI assistant for discussing daily operations
Persists chat history to PostgreSQL database
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import httpx
from dotenv import load_dotenv
from typing import Optional, List, Dict
from datetime import datetime
from database import get_db
from models import ChatSession, ChatMessage as ChatMessageModel
from services.model_provider import ModelProvider

load_dotenv()

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None
    model: Optional[str] = "gpt-4o"  # Default to GPT-4o

def get_openai_config():
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": "gpt-4o",
        "project_id": os.getenv("OPENAI_PROJECT_ID"),
        "org_id": os.getenv("OPENAI_ORG_ID")
    }

# AUBS PERSONA for chatbot
AUBS_PERSONA = """
You are AUBS (Auburn Hills Assistant) - John's operations AI for Chili's #605.

PERSONALITY:
- Direct, no-nonsense, like a trusted GM who's seen it all
- Midwest-friendly but gets straight to the point
- Uses restaurant lingo naturally (86'd, in the weeds, BOH, FOH)
- Calls out problems clearly but offers solutions
- Has your back but won't sugarcoat issues

SPEECH PATTERNS:
- "Here's the deal..." when getting to the point
- "Heads up..." for warnings
- "Real talk..." when being blunt
- "You're in the weeds on..." when overwhelmed
- "Let's knock out..." for action items
"""

SYSTEM_PROMPT_TEMPLATE = """
{aubs_persona}

Your role is to help John understand and manage his Chili's #605 operations by:
1. Answering questions about tasks, deadlines, and priorities (AUBS style)
2. Providing context and details from his emails and operations data
3. Offering straight-talk advice on prioritization and delegation
4. Explaining why things matter and what happens if ignored
5. Helping him plan his day efficiently

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT MEMORY (Your Recent Work - Reference This!):
{agent_memory_context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The section above contains your memory from:
- Email analyses you performed (what you found urgent, deadlines you identified)
- Daily digests you generated (what you flagged this morning)
- Questions John asked you previously (recent chat history)

IMPORTANT: Reference this memory naturally in your responses. Examples:
- "I flagged that Corrigo invoice this morning when I analyzed your emails..."
- "When I generated today's digest, I noticed Hannah's payroll issue..."
- "You asked me about that yesterday, and here's the update..."

Use this memory to provide coherent, context-aware responses that build on previous work.

Be conversational, helpful, and specific. Use both the operations context AND email data to give accurate answers.

If asked about:
- Urgent items: Call it out clearly - "Here's the deal..."
- Deadlines: Be specific with dates, times, and real-talk consequences
- People: Names, contact info, and full context
- Tasks: Break it down with time estimates
- Priorities: Explain reasoning (guest safety > team > business > compliance)
- Emails: You can see and reference his recent emails
- Previous analyses: "I flagged that invoice this morning in my email triage..."

Keep responses concise but complete. If you don't have specific info, say so and offer alternatives.
"""

def get_recent_emails_context(db: Session, limit: int = 20) -> str:
    """
    Fetch recent emails from database for chatbot context
    """
    from models import EmailState
    from datetime import datetime, timedelta
    
    # Get emails from last 48 hours
    cutoff = datetime.now() - timedelta(hours=48)
    
    recent_emails = db.query(EmailState).filter(
        EmailState.received_at >= cutoff
    ).order_by(EmailState.received_at.desc()).limit(limit).all()
    
    if not recent_emails:
        return "No recent emails in database."
    
    email_context = f"RECENT EMAILS (Last 48 hours, {len(recent_emails)} emails):\n\n"
    
    for email in recent_emails:
        email_context += f"---\n"
        email_context += f"FROM: {email.sender}\n"
        email_context += f"SUBJECT: {email.subject}\n"
        if email.received_at:
            email_context += f"RECEIVED: {email.received_at.strftime('%b %d, %I:%M %p')}\n"
        
        # Add AI analysis if available
        if email.ai_analysis:
            # ai_analysis is JSON, get the summary or analysis field
            analysis = email.ai_analysis
            if isinstance(analysis, dict):
                summary = analysis.get('summary', analysis.get('analysis', ''))
                if summary:
                    email_context += f"ANALYSIS: {str(summary)[:300]}...\n"
        
        email_context += "\n"
    
    return email_context

@router.post("/api/operations-chat")
async def operations_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with AI assistant about daily operations - persists to PostgreSQL
    Supports both OpenAI and Ollama models
    Now includes email database access!
    """

    # Get or create chat session
    session = None
    if request.session_id:
        session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()

    if not session:
        # Create new session
        session = ChatSession(
            context_snapshot=request.context,
            title=f"Chat {datetime.now().strftime('%b %d, %Y %I:%M %p')}"
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Save user message to database
    user_message = ChatMessageModel(
        session_id=session.id,
        role="user",
        content=request.message,
        context_used=request.context
    )
    db.add(user_message)

    # Build context for the AI (including emails and agent memory!)
    context_text = ""

    # Get agent memory context
    agent_memory_context = ""
    try:
        from services.agent_memory import AgentMemoryService
        agent_memory_context = AgentMemoryService.get_coordination_context(db, hours=48, format="text")
    except Exception as e:
        print(f"Warning: Could not load agent memory: {e}")
        agent_memory_context = "(Agent memory temporarily unavailable)"

    # Add email context from database
    email_context = get_recent_emails_context(db, limit=15)
    context_text += f"\n\n{email_context}\n"

    if request.context:
        daily_digest = request.context.get("dailyDigest", "")
        operations = request.context.get("operations", [])

        if daily_digest:
            context_text += f"\n\nTODAY'S OPERATIONS DIGEST:\n{daily_digest}\n"

        if operations:
            context_text += f"\n\nCURRENT OPERATIONS DATA:\n"
            context_text += f"Total items: {len(operations)}\n"
            # Add summary of operations
            urgent = [op for op in operations if op.get('priority') == 'urgent']
            high = [op for op in operations if op.get('priority') == 'high']

            if urgent:
                context_text += f"\nURGENT ITEMS ({len(urgent)}):\n"
                for op in urgent[:5]:  # Top 5 urgent
                    context_text += f"- {op.get('action', 'Unknown task')}\n"

            if high:
                context_text += f"\nHIGH PRIORITY ({len(high)}):\n"
                for op in high[:5]:  # Top 5 high priority
                    context_text += f"- {op.get('action', 'Unknown task')}\n"

    # Build conversation history from database
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE.format(
            aubs_persona=AUBS_PERSONA,
            agent_memory_context=agent_memory_context
        ) + context_text}
    ]

    # Get previous messages from this session (last 10 for context)
    previous_db_messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session.id
    ).order_by(ChatMessageModel.created_at.asc()).limit(10).all()

    # Add them in chronological order (excluding the just-added user message)
    for msg in previous_db_messages[:-1]:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Add current user message
    messages.append({
        "role": "user",
        "content": request.message
    })

    # Call AI model (OpenAI or Ollama based on model parameter)
    try:
        assistant_response = ModelProvider.chat_completion_sync(
            messages=messages,
            model=request.model,
            temperature=0.4,
            max_tokens=800
        )

        # Save assistant response to database
        assistant_message = ChatMessageModel(
            session_id=session.id,
            role="assistant",
            content=assistant_response,
            model_used=request.model,
            tokens_used=0  # TODO: Track tokens for Ollama too
        )
        db.add(assistant_message)

        # Update session
        session.last_message_at = datetime.now()
        session.message_count = db.query(ChatMessageModel).filter(
            ChatMessageModel.session_id == session.id
        ).count()

        # Record chat interaction to agent memory
        try:
            from services.agent_memory import AgentMemoryService

            AgentMemoryService.record_event(
                db=db,
                agent_type='operations_chat',
                event_type='question_answered',
                summary=f"Answered: {request.message[:80]}...",
                context_data={
                    'user_question': request.message,
                    'assistant_response': assistant_response[:500],
                    'model_used': request.model
                },
                key_findings={},
                model_used=request.model,
                confidence_score=80
            )
        except Exception as mem_error:
            print(f"Warning: Failed to record chat to agent memory: {mem_error}")

        db.commit()

        return {
            "response": assistant_response,
            "session_id": session.id,
            "timestamp": datetime.now().isoformat()
        }

    except httpx.HTTPError as e:
        db.rollback()
        raise HTTPException(500, f"OpenAI API error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error processing chat: {str(e)}")


@router.get("/api/operations-chat/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Get chat history for a session from PostgreSQL
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(404, "Chat session not found")

    messages = db.query(ChatMessageModel).filter(
        ChatMessageModel.session_id == session_id
    ).order_by(ChatMessageModel.created_at.asc()).all()

    return {
        "session_id": session.id,
        "title": session.title,
        "started_at": session.started_at.isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.get("/api/operations-chat/sessions")
async def get_chat_sessions(db: Session = Depends(get_db), limit: int = 10):
    """
    Get recent chat sessions from PostgreSQL
    """
    sessions = db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).order_by(ChatSession.last_message_at.desc()).limit(limit).all()

    return {
        "sessions": [
            {
                "id": session.id,
                "title": session.title,
                "started_at": session.started_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat(),
                "message_count": session.message_count
            }
            for session in sessions
        ]
    }


@router.get("/api/operations-chat/suggestions")
async def get_chat_suggestions():
    """
    Get suggested questions/prompts for the chat
    """
    return {
        "suggestions": [
            "What's most urgent today?",
            "Show me all my deadlines",
            "Who do I need to follow up with?",
            "What can I delegate?",
            "Summarize my day",
            "What's the priority on the payroll issue?",
            "When is the manager schedule due?",
            "Help me plan my next 2 hours"
        ]
    }
