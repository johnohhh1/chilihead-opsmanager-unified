"""SQLAlchemy database models for OpenInbox OpsManager AI"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, Integer, JSON, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


class EmailState(Base):
    """Track email read/acknowledged status"""
    __tablename__ = 'email_state'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email_id = Column(String(255), unique=True, nullable=False, index=True)
    thread_id = Column(String(255), index=True)
    subject = Column(Text)
    sender = Column(String(255))
    received_at = Column(DateTime)
    first_seen_at = Column(DateTime)
    last_viewed_at = Column(DateTime)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime)
    ai_analysis = Column(JSON)  # Store the AI analysis result
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Task(Base):
    """User's actual todo list"""
    __tablename__ = 'tasks'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(Text, nullable=False)
    description = Column(Text)
    due_date = Column(Date)
    priority = Column(String(20))  # 'low', 'medium', 'high', 'urgent'
    status = Column(String(20), default='todo')  # 'todo', 'in_progress', 'completed', 'cancelled'
    source = Column(String(50))  # 'manual', 'email', 'ai_suggested', 'delegated'
    source_id = Column(String(255))  # email_id or delegation_id if applicable
    completed_at = Column(DateTime)
    gcal_event_id = Column(String(255))  # Google Calendar event ID
    google_task_id = Column(String(255))  # Google Tasks ID
    eisenhower_quadrant = Column(String(20))  # 'urgent_important', 'not_urgent_important', etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='check_priority'),
        CheckConstraint("status IN ('todo', 'in_progress', 'completed', 'cancelled')", name='check_status'),
    )


class Delegation(Base):
    """ChiliHead 5-Pillar delegation system"""
    __tablename__ = 'delegations'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_description = Column(Text, nullable=False)
    assigned_to = Column(String(255))
    assigned_to_email = Column(String(255))  # For email notifications
    due_date = Column(Date)
    follow_up_date = Column(Date)
    priority = Column(String(20))
    status = Column(String(20), default='planning')  # 'planning', 'active', 'completed', 'on_hold'
    chilihead_progress = Column(JSON)  # Your 5-pillar system
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("status IN ('planning', 'active', 'completed', 'on_hold')", name='check_delegation_status'),
    )


class WatchConfig(Base):
    """Email watch configuration - replaces watch_config.json"""
    __tablename__ = 'watch_config'
    
    id = Column(Integer, primary_key=True, default=1)
    priority_senders = Column(JSON, default=list)
    priority_domains = Column(JSON, default=list)
    priority_keywords = Column(JSON, default=list)
    excluded_subjects = Column(JSON, default=list)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint('id = 1', name='single_row_constraint'),
    )


class AIAnalysisCache(Base):
    """Cache AI analysis results to avoid re-processing"""
    __tablename__ = 'ai_analysis_cache'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email_id = Column(String(255), unique=True, nullable=False, index=True)
    prompt_hash = Column(String(64))  # Hash of the prompt used
    analysis_result = Column(JSON)
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    analyzed_at = Column(DateTime, default=func.now())


class ChatSession(Base):
    """Chat sessions for operations assistant"""
    __tablename__ = 'chat_sessions'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(255), default='john')  # For future multi-user support
    title = Column(String(255))  # Auto-generated summary of chat
    context_snapshot = Column(JSON)  # Daily digest and operations at session start
    started_at = Column(DateTime, default=func.now())
    last_message_at = Column(DateTime, default=func.now())
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class ChatMessage(Base):
    """Individual chat messages"""
    __tablename__ = 'chat_messages'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    context_used = Column(JSON)  # What context was available for this message
    model_used = Column(String(50))  # e.g., 'gpt-4o'
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_message_role'),
    )
