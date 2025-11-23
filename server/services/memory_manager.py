"""
Memory Manager - Intelligent memory lifecycle management
Handles resolution, archiving, and expiration of memories
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import json

class MemoryManager:
    """
    Manages the lifecycle of memories - creation, resolution, archiving, and expiration
    """

    # Memory retention policies
    RETENTION_POLICIES = {
        'resolved': timedelta(days=3),      # Keep resolved items for 3 days then archive
        'chat': timedelta(days=7),          # Keep chat history for 7 days
        'email_analyzed': timedelta(days=14),  # Keep email analysis for 2 weeks
        'daily_brief': timedelta(days=30),  # Keep daily briefs for 30 days
        'urgent': timedelta(days=7),        # Keep urgent items for 1 week after resolution
    }

    @classmethod
    def cleanup_resolved_memories(cls, db: Session, dry_run: bool = False) -> Dict:
        """
        Clean up resolved memories that are past retention period

        Args:
            db: Database session
            dry_run: If True, only report what would be deleted

        Returns:
            Dict with cleanup statistics
        """
        from services.agent_memory import AgentMemory

        stats = {
            'archived': 0,
            'deleted': 0,
            'kept': 0,
            'details': []
        }

        # Find resolved memories
        resolved_memories = db.query(AgentMemory).filter(
            AgentMemory.is_resolved == True
        ).all()

        for memory in resolved_memories:
            # Calculate age since resolution
            if memory.updated_at:
                age = datetime.utcnow() - memory.updated_at
                retention = cls.RETENTION_POLICIES.get('resolved', timedelta(days=3))

                if age > retention:
                    stats['details'].append({
                        'id': memory.id,
                        'summary': memory.summary[:50],
                        'age_days': age.days,
                        'action': 'delete'
                    })

                    if not dry_run:
                        db.delete(memory)
                    stats['deleted'] += 1
                else:
                    stats['kept'] += 1
            else:
                stats['kept'] += 1

        if not dry_run:
            db.commit()

        return stats

    @classmethod
    def smart_resolve(cls, db: Session, topic: str, context: str = None) -> int:
        """
        Intelligently resolve memories based on topic and context

        Args:
            db: Database session
            topic: The topic/issue to resolve (e.g., "pedro", "payroll", "coverage")
            context: Additional context to help identify what to resolve

        Returns:
            Number of memories resolved
        """
        from services.agent_memory import AgentMemory

        # Build smart query based on topic
        query = db.query(AgentMemory).filter(
            AgentMemory.is_resolved == False
        )

        # Search in multiple fields
        topic_filter = or_(
            AgentMemory.summary.ilike(f'%{topic}%'),
            text(f"context_data::text ILIKE '%{topic}%'"),
            text(f"key_findings::text ILIKE '%{topic}%'"),
            text(f"related_entities::text ILIKE '%{topic}%'")
        )

        memories = query.filter(topic_filter).all()

        resolved_count = 0
        for memory in memories:
            # Check if this memory should be resolved based on context
            should_resolve = True

            # If context provided, verify it matches
            if context:
                memory_text = f"{memory.summary} {json.dumps(memory.context_data)}"
                if context.lower() not in memory_text.lower():
                    should_resolve = False

            if should_resolve:
                memory.is_resolved = True
                memory.resolution_timestamp = datetime.utcnow()
                memory.resolution_reason = f"Resolved: {topic}"
                resolved_count += 1

        db.commit()
        return resolved_count

    @classmethod
    def expire_old_memories(cls, db: Session, dry_run: bool = False) -> Dict:
        """
        Expire memories based on their type and age

        Args:
            db: Database session
            dry_run: If True, only report what would be expired

        Returns:
            Dict with expiration statistics
        """
        from services.agent_memory import AgentMemory

        stats = {
            'expired': 0,
            'kept': 0,
            'by_type': {}
        }

        for event_type, retention_period in cls.RETENTION_POLICIES.items():
            cutoff_date = datetime.utcnow() - retention_period

            # Find memories older than retention period
            old_memories = db.query(AgentMemory).filter(
                and_(
                    AgentMemory.event_type == event_type,
                    AgentMemory.created_at < cutoff_date,
                    AgentMemory.is_resolved == False  # Don't expire unresolved items
                )
            ).all()

            type_count = len(old_memories)
            if type_count > 0:
                stats['by_type'][event_type] = type_count
                stats['expired'] += type_count

                if not dry_run:
                    for memory in old_memories:
                        db.delete(memory)

        if not dry_run:
            db.commit()

        return stats

    @classmethod
    def get_active_issues(cls, db: Session) -> List[Dict]:
        """
        Get list of currently active (unresolved) issues

        Returns:
            List of active issues with details
        """
        from services.agent_memory import AgentMemory

        active_memories = db.query(AgentMemory).filter(
            and_(
                AgentMemory.is_resolved == False,
                or_(
                    AgentMemory.event_type == 'email_analyzed',
                    AgentMemory.event_type == 'task_created',
                    text("key_findings::text LIKE '%urgent%'")
                )
            )
        ).order_by(AgentMemory.created_at.desc()).limit(20).all()

        issues = []
        for memory in active_memories:
            # Extract key information
            issue = {
                'id': memory.id,
                'summary': memory.summary,
                'type': memory.event_type,
                'created': memory.created_at.isoformat() if memory.created_at else None,
                'age_days': (datetime.utcnow() - memory.created_at).days if memory.created_at else 0,
                'agent': memory.agent_type,
                'urgent': 'urgent' in str(memory.key_findings).lower() if memory.key_findings else False
            }

            # Extract specific issue details
            if memory.key_findings:
                if isinstance(memory.key_findings, dict):
                    issue['details'] = memory.key_findings.get('urgent_items', [])

            issues.append(issue)

        return issues

    @classmethod
    def deduplicate_memories(cls, db: Session, dry_run: bool = False) -> Dict:
        """
        Remove duplicate memories (same summary within 1 hour window)

        Returns:
            Dict with deduplication statistics
        """
        from services.agent_memory import AgentMemory
        from sqlalchemy import func

        stats = {
            'duplicates_removed': 0,
            'unique_kept': 0
        }

        # Find potential duplicates (same summary)
        duplicates = db.query(
            AgentMemory.summary,
            func.count(AgentMemory.id).label('count')
        ).group_by(
            AgentMemory.summary
        ).having(
            func.count(AgentMemory.id) > 1
        ).all()

        for dup_summary, count in duplicates:
            # Get all memories with this summary
            memories = db.query(AgentMemory).filter(
                AgentMemory.summary == dup_summary
            ).order_by(AgentMemory.created_at.desc()).all()

            # Keep the newest one, delete the rest
            for memory in memories[1:]:  # Skip first (newest)
                # Only delete if created within 1 hour of each other
                if memories[0].created_at and memory.created_at:
                    time_diff = memories[0].created_at - memory.created_at
                    if abs(time_diff.total_seconds()) < 3600:  # 1 hour
                        if not dry_run:
                            db.delete(memory)
                        stats['duplicates_removed'] += 1

            stats['unique_kept'] += 1

        if not dry_run:
            db.commit()

        return stats

    @classmethod
    def create_resolution_rule(cls, pattern: str, auto_expire_days: int = 7) -> Dict:
        """
        Create a rule for auto-resolving certain patterns

        Args:
            pattern: Pattern to match (e.g., "call-off", "coverage found")
            auto_expire_days: Days after which to auto-resolve

        Returns:
            Rule configuration
        """
        return {
            'pattern': pattern,
            'auto_expire_days': auto_expire_days,
            'created': datetime.utcnow().isoformat()
        }

    @classmethod
    def apply_resolution_rules(cls, db: Session) -> int:
        """
        Apply auto-resolution rules to memories

        Returns:
            Number of memories auto-resolved
        """
        from services.agent_memory import AgentMemory

        # Common patterns that indicate resolution
        resolution_patterns = [
            ('covered', 'Coverage has been arranged'),
            ('resolved', 'Issue marked as resolved'),
            ('completed', 'Task has been completed'),
            ('handled', 'Situation has been handled'),
            ('done', 'Action has been completed'),
            ('fixed', 'Problem has been fixed')
        ]

        resolved_count = 0

        for pattern, reason in resolution_patterns:
            # Find memories that mention resolution but aren't marked resolved
            memories = db.query(AgentMemory).filter(
                and_(
                    AgentMemory.is_resolved == False,
                    or_(
                        AgentMemory.summary.ilike(f'%{pattern}%'),
                        text(f"context_data::text ILIKE '%{pattern}%'")
                    )
                )
            ).all()

            for memory in memories:
                memory.is_resolved = True
                memory.resolution_timestamp = datetime.utcnow()
                memory.resolution_reason = reason
                resolved_count += 1

        db.commit()
        return resolved_count