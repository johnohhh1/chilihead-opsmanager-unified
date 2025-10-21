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

SYSTEM_PROMPT = """
You are John's executive assistant AI for his Chili's restaurant operations.

Your role is to help John understand and manage his daily operations by:
1. Answering questions about his tasks, deadlines, and priorities
2. Providing context and details about operations
3. Offering advice on prioritization and delegation
4. Explaining why certain things are important or urgent
5. Helping him plan his day efficiently

Be conversational, helpful, and specific. Use the context provided about today's operations to give accurate, actionable answers.

If asked about:
- Urgent items: Focus on what needs immediate attention and why
- Deadlines: Be specific about dates, times, and consequences
- People: Mention names, contact info, and context
- Tasks: Break down what needs to be done and estimated time
- Priorities: Explain reasoning based on impact and urgency

Keep responses concise but complete. If you don't have specific information in the context, say so and offer to help in other ways.
"""

@router.post("/api/operations-chat")
async def operations_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with AI assistant about daily operations - persists to PostgreSQL
    Supports both OpenAI and Ollama models
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

    # Build context for the AI
    context_text = ""

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
        {"role": "system", "content": SYSTEM_PROMPT + context_text}
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
        assistant_response = await ModelProvider.chat_completion(
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
