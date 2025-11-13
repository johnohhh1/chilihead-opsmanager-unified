"""
Centralized Agent Memory System
Enables AI agents to share context, coordinate, and avoid redundant work
"""

from sqlalchemy.orm import Session
from models import AgentMemory, AgentSession
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json


class AgentMemoryService:
    """Service for managing centralized AI agent memory"""

    @staticmethod
    def record_event(
        db: Session,
        agent_type: str,
        event_type: str,
        summary: str,
        context_data: Optional[Dict] = None,
        key_findings: Optional[Dict] = None,
        related_entities: Optional[Dict] = None,
        email_id: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        confidence_score: Optional[int] = None
    ) -> AgentMemory:
        """
        Record an agent action/event to centralized memory

        Args:
            agent_type: 'triage', 'daily_brief', 'operations_chat', 'delegation_advisor', 'smart_triage'
            event_type: 'email_analyzed', 'task_created', 'digest_generated', etc.
            summary: Human-readable summary (e.g., "Analyzed urgent payroll email")
            context_data: Full context dict (email content, analysis, etc.)
            key_findings: Extracted important info (deadlines, urgent items, etc.)
            related_entities: {people: [], emails: [], tasks: [], deadlines: []}

        Returns:
            Created AgentMemory instance
        """
        try:
            memory = AgentMemory(
                agent_type=agent_type,
                event_type=event_type,
                summary=summary,
                context_data=context_data or {},
                key_findings=key_findings or {},
                related_entities=related_entities or {},
                session_id=session_id,
                email_id=email_id,
                task_id=task_id,
                model_used=model_used,
                tokens_used=tokens_used,
                confidence_score=confidence_score
            )

            db.add(memory)
            db.commit()
            db.refresh(memory)

            return memory
        except Exception as e:
            db.rollback()
            print(f"Warning: Failed to record agent memory: {e}")
            raise

    @staticmethod
    def get_recent_context(
        db: Session,
        agent_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 50
    ) -> List[AgentMemory]:
        """
        Get recent agent memories for context building

        Args:
            agent_type: Filter by agent (None = all agents)
            hours: How far back to look
            limit: Max memories to return

        Returns:
            List of recent AgentMemory records
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        query = db.query(AgentMemory).filter(
            AgentMemory.created_at >= cutoff
        )

        if agent_type:
            query = query.filter(AgentMemory.agent_type == agent_type)

        return query.order_by(AgentMemory.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_related_memory(
        db: Session,
        email_id: Optional[str] = None,
        task_id: Optional[str] = None,
        delegation_id: Optional[str] = None
    ) -> List[AgentMemory]:
        """
        Get all agent memories related to a specific entity

        Example: "What do all my agents know about this email?"

        Returns:
            List of AgentMemory records for this entity
        """
        query = db.query(AgentMemory)

        filters = []
        if email_id:
            filters.append(AgentMemory.email_id == email_id)
        if task_id:
            filters.append(AgentMemory.task_id == task_id)
        if delegation_id:
            filters.append(AgentMemory.delegation_id == delegation_id)

        if not filters:
            return []

        # OR logic: get memories matching any of the IDs
        from sqlalchemy import or_
        query = query.filter(or_(*filters))

        return query.order_by(AgentMemory.created_at.asc()).all()

    @staticmethod
    def get_coordination_context(
        db: Session,
        hours: int = 24,
        format: str = "text"
    ) -> str:
        """
        Build coordination context for agents showing what others have done

        Args:
            hours: How far back to look
            format: "text" or "json"

        Returns:
            Formatted context string showing recent agent activity
        """
        memories = AgentMemoryService.get_recent_context(db, hours=hours, limit=100)

        if format == "json":
            return json.dumps([{
                "agent": m.agent_type,
                "event": m.event_type,
                "summary": m.summary,
                "time": m.created_at.isoformat(),
                "findings": m.key_findings
            } for m in memories], indent=2)

        # Text format for LLM system prompts
        context_lines = [f"AGENT MEMORY (Last {hours}h):\n"]

        # Group by agent
        by_agent = {}
        for m in memories:
            if m.agent_type not in by_agent:
                by_agent[m.agent_type] = []
            by_agent[m.agent_type].append(m)

        for agent_type, agent_memories in by_agent.items():
            context_lines.append(f"\n{agent_type.upper()} Agent:")
            for mem in agent_memories[:10]:  # Top 10 per agent
                time_str = mem.created_at.strftime('%b %d, %I:%M %p')
                context_lines.append(f"  - [{time_str}] {mem.summary}")

                # Add key findings if present
                if mem.key_findings:
                    if 'urgent_items' in mem.key_findings and mem.key_findings['urgent_items']:
                        context_lines.append(f"    🚨 Urgent: {', '.join(mem.key_findings['urgent_items'][:2])}")
                    if 'deadlines' in mem.key_findings and mem.key_findings['deadlines']:
                        context_lines.append(f"    📅 Deadlines: {len(mem.key_findings['deadlines'])} identified")

        return "\n".join(context_lines)

    @staticmethod
    def search_memory(
        db: Session,
        query_text: str,
        agent_type: Optional[str] = None,
        limit: int = 20
    ) -> List[AgentMemory]:
        """
        Search agent memories by text (simple keyword search)

        For production: Replace with pgvector semantic search

        Returns:
            Memories matching the search query
        """
        query = db.query(AgentMemory)

        if agent_type:
            query = query.filter(AgentMemory.agent_type == agent_type)

        # Simple ILIKE search on summary
        query = query.filter(AgentMemory.summary.ilike(f"%{query_text}%"))

        return query.order_by(AgentMemory.created_at.desc()).limit(limit).all()

    @staticmethod
    def start_session(
        db: Session,
        agent_type: str,
        session_type: str,
        model_used: Optional[str] = None
    ) -> AgentSession:
        """
        Start a batch work session (like processing multiple emails)

        Returns:
            Created AgentSession instance
        """
        session = AgentSession(
            agent_type=agent_type,
            session_type=session_type,
            model_used=model_used,
            status='running'
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def complete_session(
        db: Session,
        session_id: str,
        items_processed: int,
        summary: str,
        findings_json: Optional[Dict] = None,
        total_tokens: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Mark a session as completed and record results
        """
        session = db.query(AgentSession).filter(AgentSession.id == session_id).first()

        if not session:
            return None

        session.completed_at = datetime.now()
        session.items_processed = items_processed
        session.summary = summary
        session.findings_json = findings_json or {}
        session.total_tokens = total_tokens
        session.status = 'error' if error_message else 'completed'
        session.error_message = error_message

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def get_digest_context(db: Session, hours: int = 24) -> str:
        """
        Build context specifically for daily digest generation
        Includes what triage/chat agents found recently

        Returns:
            Formatted context string for digest AI
        """
        triage_memories = AgentMemoryService.get_recent_context(
            db, agent_type='triage', hours=hours, limit=30
        )

        chat_memories = AgentMemoryService.get_recent_context(
            db, agent_type='operations_chat', hours=hours, limit=10
        )

        context = ["CONTEXT FROM OTHER AGENTS:\n"]

        if triage_memories:
            context.append(f"\nEmail Triage Agent (analyzed {len(triage_memories)} emails):")
            urgent_count = 0
            deadline_count = 0

            for mem in triage_memories:
                if mem.key_findings:
                    if mem.key_findings.get('priority') == 'urgent':
                        urgent_count += 1
                        context.append(f"  🚨 {mem.summary}")
                    if 'deadline' in mem.key_findings:
                        deadline_count += 1

            if urgent_count > 0:
                context.append(f"\n  Total urgent items flagged: {urgent_count}")
            if deadline_count > 0:
                context.append(f"  Total deadlines identified: {deadline_count}")

        if chat_memories:
            context.append(f"\nRecent Questions John Asked:")
            for mem in chat_memories[:5]:
                if mem.event_type == 'question_answered':
                    context.append(f"  - {mem.summary}")

        return "\n".join(context)
