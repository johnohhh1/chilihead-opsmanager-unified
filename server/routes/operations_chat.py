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

# AUBS PERSONA for chatbot - SIMPLE AND DIRECT
AUBS_PERSONA = """
You are AUBS (Auburn Hills Assistant) - John's operations AI for Chili's #605.

CORE RULES:
- Answer questions directly with facts
- Don't lecture or explain why things matter (John already knows)
- Don't tell John what he "needs to do" unless he asks for advice
- Don't make up procedures or requirements that don't exist
- If John says something is resolved, it's resolved - don't argue

COMMUNICATION:
- State facts clearly
- Provide specific details when asked
- Skip the preamble and get to the point
- Trust John to make his own decisions
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
    Uses EmailCache and EmailAnalysisCache for comprehensive context
    """
    from models import EmailCache, EmailAnalysisCache
    from datetime import datetime, timedelta

    # Get emails from last 48 hours
    cutoff = datetime.now() - timedelta(hours=48)

    recent_emails = db.query(EmailCache).filter(
        EmailCache.received_at >= cutoff
    ).order_by(EmailCache.received_at.desc()).limit(limit).all()

    if not recent_emails:
        return "No recent emails in database."

    email_context = f"RECENT EMAILS (Last 48 hours, {len(recent_emails)} emails):\n\n"

    for email in recent_emails:
        email_context += f"---\n"
        email_context += f"FROM: {email.sender}\n"
        email_context += f"SUBJECT: {email.subject}\n"
        if email.received_at:
            email_context += f"RECEIVED: {email.received_at.strftime('%b %d, %I:%M %p')}\n"

        # Add email body preview
        if email.body_text:
            preview = email.body_text[:200].replace('\n', ' ').strip()
            email_context += f"PREVIEW: {preview}...\n"

        # Add AI analysis if available
        analysis_cache = db.query(EmailAnalysisCache).filter(
            EmailAnalysisCache.thread_id == email.thread_id
        ).first()

        if analysis_cache and analysis_cache.analysis_json:
            analysis = analysis_cache.analysis_json
            if isinstance(analysis, dict):
                # Try to get the analysis text
                analysis_text = analysis.get('analysis', '')
                if analysis_text:
                    email_context += f"AI ANALYSIS: {str(analysis_text)[:300]}...\n"

                # Add priority and category
                if analysis_cache.priority_score:
                    email_context += f"PRIORITY: {analysis_cache.priority_score}/100 ({analysis_cache.category})\n"

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

            # Check if user is correcting/updating memory
            correction_keywords = [
                'was handled', 'already done', 'not urgent', 'resolved', 'completed',
                'fixed', 'update the memory', 'mark as done', 'taken care of',
                'all set', 'no longer needed', 'false alarm', 'ignore that',
                'scratch that', 'never mind', 'cancel', 'disregard'
            ]
            user_msg_lower = request.message.lower()

            is_correction = any(keyword in user_msg_lower for keyword in correction_keywords)

            total_resolved = 0
            resolved_topics = []

            if is_correction:
                # Try to extract what they're referring to
                # Common patterns: "the pedro issue", "payroll problem", etc.
                import re

                # Look for key nouns/topics
                topics = []
                if 'pedro' in user_msg_lower:
                    topics.append('Pedro')
                if 'payroll' in user_msg_lower or 'pay' in user_msg_lower:
                    topics.append('payroll')
                if 'schedule' in user_msg_lower:
                    topics.append('schedule')
                if 'invoice' in user_msg_lower:
                    topics.append('invoice')
                if 'hannah' in user_msg_lower or 'zimmerman' in user_msg_lower:
                    topics.append('Hannah')
                if 'coverage' in user_msg_lower or 'call' in user_msg_lower:
                    topics.append('coverage')

                # Mark related memories as resolved
                for topic in topics:
                    resolved_count = AgentMemoryService.mark_resolved(
                        db=db,
                        summary_text=topic,
                        annotation=f"User update: {request.message}"
                    )
                    if resolved_count > 0:
                        total_resolved += resolved_count
                        resolved_topics.append(f"{topic} ({resolved_count})")
                        print(f"[Memory Update] Marked {resolved_count} '{topic}' memories as resolved")

                # FIX: Force immediate database flush and commit
                if total_resolved > 0:
                    db.flush()
                    db.commit()
                    db.expire_all()
                    print(f"[Memory System] ✓ Committed {total_resolved} memory updates to database")

            # Add memory update info to chat record
            AgentMemoryService.record_event(
                db=db,
                agent_type='operations_chat',
                event_type='question_answered',
                summary=f"Answered: {request.message[:80]}..." + (f" [Updated {total_resolved} memories]" if total_resolved > 0 else ""),
                context_data={
                    'user_question': request.message,
                    'assistant_response': assistant_response[:500],
                    'model_used': request.model,
                    'was_correction': is_correction,
                    'memory_updates': {
                        'total_resolved': total_resolved,
                        'topics': resolved_topics
                    } if is_correction else {}
                },
                key_findings={},
                model_used=request.model,
                confidence_score=80
            )
        except Exception as mem_error:
            print(f"Warning: Failed to record chat to agent memory: {mem_error}")

        db.commit()

        # Add memory update confirmation to response
        memory_update_note = ""
        if total_resolved > 0:
            memory_update_note = f"\n\n✅ **Memory Updated**: Marked {total_resolved} item{'s' if total_resolved != 1 else ''} as resolved ({', '.join(resolved_topics)}). This will be reflected in your next daily digest."

        return {
            "response": assistant_response + memory_update_note,
            "session_id": session.id,
            "timestamp": datetime.now().isoformat(),
            "memory_updates": total_resolved if is_correction else 0
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


@router.post("/api/operations-chat/mark-resolved")
async def mark_resolved(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Manually mark items as resolved in agent memory

    Body:
        {
            "topic": "Pedro" | "payroll" | etc.,
            "annotation": "User note about resolution"
        }
    """
    from services.agent_memory import AgentMemoryService

    topic = request.get('topic')
    annotation = request.get('annotation', 'Marked as resolved by user')

    if not topic:
        raise HTTPException(400, "Topic is required")

    resolved_count = AgentMemoryService.mark_resolved(
        db=db,
        summary_text=topic,
        annotation=annotation
    )

    return {
        "success": True,
        "resolved_count": resolved_count,
        "topic": topic,
        "message": f"Marked {resolved_count} memories related to '{topic}' as resolved"
    }


@router.get("/api/operations-chat/debug-memory/{topic}")
async def debug_memory_state(topic: str, db: Session = Depends(get_db)):
    """
    Debug endpoint to see current memory state for a specific topic
    Helps troubleshoot why items aren't being marked as resolved
    """
    from services.agent_memory import AgentMemoryService

    # Force fresh read from database
    db.expire_all()

    # Search for topic (case-insensitive)
    memories = AgentMemoryService.search_memory(db, topic, limit=50)

    return {
        "topic": topic,
        "total_found": len(memories),
        "resolved_count": len([m for m in memories if "[RESOLVED]" in m.summary]),
        "active_count": len([m for m in memories if "[RESOLVED]" not in m.summary]),
        "memories": [
            {
                "id": m.id,
                "summary": m.summary,
                "is_resolved": "[RESOLVED]" in m.summary,
                "created_at": m.created_at.isoformat(),
                "agent_type": m.agent_type,
                "event_type": m.event_type,
                "annotations": m.context_data.get('annotations', []) if m.context_data else [],
                "email_id": m.email_id,
                "task_id": m.task_id
            }
            for m in memories
        ]
    }


@router.get("/api/operations-chat/memory-status")
async def get_memory_status(db: Session = Depends(get_db)):
    """
    Get current status of agent memory (active vs resolved items)
    """
    from services.agent_memory import AgentMemoryService
    from models import AgentMemory
    from datetime import datetime, timedelta

    # Force fresh read
    db.expire_all()

    cutoff = datetime.now() - timedelta(hours=48)

    # Count active and resolved
    all_recent = db.query(AgentMemory).filter(
        AgentMemory.created_at >= cutoff
    ).all()

    resolved = [m for m in all_recent if "[RESOLVED]" in m.summary]
    active = [m for m in all_recent if "[RESOLVED]" not in m.summary]

    # Group active by agent type
    by_agent = {}
    for mem in active:
        if mem.agent_type not in by_agent:
            by_agent[mem.agent_type] = []
        by_agent[mem.agent_type].append({
            'id': mem.id,
            'summary': mem.summary,
            'created_at': mem.created_at.isoformat(),
            'event_type': mem.event_type
        })

    return {
        "total_active": len(active),
        "total_resolved": len(resolved),
        "by_agent": by_agent,
        "resolved_items": [
            {
                'summary': m.summary,
                'resolved_at': m.context_data.get('annotations', [{}])[-1].get('timestamp') if m.context_data else None
            }
            for m in resolved[:10]  # Last 10 resolved
        ]
    }
