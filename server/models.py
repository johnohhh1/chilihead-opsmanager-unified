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


class EmailCache(Base):
    """Mirror of Gmail emails - stores raw email data locally"""
    __tablename__ = 'email_cache'

    thread_id = Column(String(255), primary_key=True)
    gmail_message_id = Column(String(255), unique=True, index=True)
    subject = Column(Text)
    sender = Column(String(255), index=True)
    recipients = Column(JSON)  # {to: [], cc: [], bcc: []}
    body_text = Column(Text)
    body_html = Column(Text)
    attachments_json = Column(JSON)  # [{filename, size, mimetype, has_preview}]
    labels = Column(JSON)  # ['INBOX', 'IMPORTANT', 'UNREAD']
    received_at = Column(DateTime, index=True)
    gmail_synced_at = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)


class EmailAnalysisCache(Base):
    """Cache AI analysis results with model quality tracking"""
    __tablename__ = 'email_analysis_cache'

    thread_id = Column(String(255), primary_key=True)

    # Analysis content
    analysis_json = Column(JSON)  # Full AI response
    priority_score = Column(Integer, index=True)  # 0-100
    category = Column(String(50), index=True)  # 'urgent', 'important', 'routine', 'fyi'
    key_entities = Column(JSON)  # {people: [], deadlines: [], locations: [], amounts: []}
    suggested_tasks = Column(JSON)  # Tasks AI thinks should be created
    sentiment = Column(String(20))  # 'positive', 'neutral', 'negative', 'urgent'

    # Model tracking and quality
    model_used = Column(String(50), index=True)  # 'gpt-4o', 'oss-120b-cloud', 'llama3-70b-local'
    model_tier = Column(String(20), index=True)  # 'trusted', 'experimental', 'unreliable'
    trust_score = Column(Integer, default=50)  # 0-100, updated based on user feedback
    tokens_used = Column(Integer)
    analyzed_at = Column(DateTime, default=func.now())

    # Re-analysis tracking
    needs_reanalysis = Column(Boolean, default=False)
    reanalysis_reason = Column(String(100))  # 'user_requested', 'model_hallucinated', 'upgrade_to_better_model'
    analysis_version = Column(Integer, default=1)  # Increments on re-analysis
    previous_analysis = Column(JSON)  # Store previous version for comparison
    user_feedback = Column(String(20))  # 'accurate', 'missed_details', 'hallucinated', 'wrong_priority'

    __table_args__ = (
        CheckConstraint("model_tier IN ('trusted', 'experimental', 'unreliable')", name='check_model_tier'),
        CheckConstraint("category IN ('urgent', 'important', 'routine', 'fyi', 'spam')", name='check_category'),
    )


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


class AgentMemory(Base):
    """Centralized memory store for all AI agents to share context and coordinate"""
    __tablename__ = 'agent_memory'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_type = Column(String(50), nullable=False, index=True)  # 'triage', 'daily_brief', 'operations_chat', 'delegation_advisor'
    event_type = Column(String(50), nullable=False, index=True)  # 'email_analyzed', 'task_created', 'delegation_suggested', 'question_answered', 'digest_generated'

    # Core content
    summary = Column(Text)  # Human-readable summary of what happened
    context_data = Column(JSON)  # Full context: email content, analysis, etc.
    key_findings = Column(JSON)  # Extracted important info: deadlines, urgent items, action items
    related_entities = Column(JSON)  # {people: [], emails: [], tasks: [], deadlines: []}

    # Relationships
    session_id = Column(String(36), index=True)  # Links to AgentSession if part of batch work
    email_id = Column(String(255), index=True)  # Gmail message/thread ID if related to email
    task_id = Column(String(36), index=True)  # Task ID if related to a task
    delegation_id = Column(String(36), index=True)  # Delegation ID if related to delegation

    # Metadata
    model_used = Column(String(50))  # AI model that generated this memory
    tokens_used = Column(Integer)
    confidence_score = Column(Integer)  # 0-100, how confident the agent was
    created_at = Column(DateTime, default=func.now(), index=True)

    __table_args__ = (
        CheckConstraint("agent_type IN ('triage', 'daily_brief', 'operations_chat', 'delegation_advisor', 'smart_triage')", name='check_agent_type'),
        CheckConstraint("event_type IN ('email_analyzed', 'task_created', 'delegation_suggested', 'question_answered', 'digest_generated', 'deadline_identified', 'urgent_item_flagged')", name='check_event_type'),
    )


class AgentSession(Base):
    """Track batch work sessions (like processing 20 emails or generating daily digest)"""
    __tablename__ = 'agent_sessions'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_type = Column(String(50), nullable=False, index=True)
    session_type = Column(String(50), nullable=False)  # 'daily_digest', 'email_batch_triage', 'deadline_scan'

    # Session details
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    items_processed = Column(Integer, default=0)

    # Results
    summary = Column(Text)  # High-level summary of what was accomplished
    findings_json = Column(JSON)  # Structured findings: {urgent_items: [], deadlines: [], tasks_created: []}
    model_used = Column(String(50))
    total_tokens = Column(Integer)

    # Status
    status = Column(String(20), default='running')  # 'running', 'completed', 'error'
    error_message = Column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('running', 'completed', 'error')", name='check_session_status'),
    )


class DismissedItem(Base):
    """Track dismissed/archived items from daily digest to prevent re-flagging"""
    __tablename__ = 'dismissed_items'

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Item identification
    item_type = Column(String(50), nullable=False)  # 'email', 'urgent_item', 'deadline', 'pattern'
    identifier = Column(String(500), nullable=False, index=True)  # Email thread_id, task description hash, or unique identifier

    # Original context
    original_text = Column(Text)  # The text that was shown in the digest
    email_thread_id = Column(String(255), index=True)  # If related to an email
    email_subject = Column(String(500))

    # Dismissal details
    dismissed_by = Column(String(255), default='john')
    dismissed_at = Column(DateTime, default=func.now(), index=True)
    dismiss_reason = Column(String(100))  # 'resolved', 'not_relevant', 'duplicate', 'already_handled'
    notes = Column(Text)  # User's optional notes

    # Auto-expiry
    expires_at = Column(DateTime, index=True)  # Auto-show again after this date (optional)
    is_permanent = Column(Boolean, default=False)  # If true, never show again

    __table_args__ = (
        CheckConstraint("item_type IN ('email', 'urgent_item', 'deadline', 'pattern', 'suggestion')", name='check_item_type'),
        CheckConstraint("dismiss_reason IN ('resolved', 'not_relevant', 'duplicate', 'already_handled', 'other')", name='check_dismiss_reason'),
    )


class PortalMetrics(Base):
    """Daily portal results from Business Intelligence email (OCR-parsed)"""
    __tablename__ = 'portal_metrics'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_date = Column(Date, nullable=False, unique=True, index=True)  # Date of the report

    # Key Performance Indicators
    sales = Column(Integer)  # Daily sales in dollars
    labor_percent = Column(Integer)  # Labor % (stored as integer, e.g., 24.5 = 245)
    guest_satisfaction = Column(Integer)  # Guest satisfaction score (e.g., 85.2 = 852)
    food_cost_percent = Column(Integer)  # Food cost % (stored as integer)
    speed_of_service = Column(Integer)  # Speed of service metric (time or score)

    # Metadata
    raw_ocr_text = Column(Text)  # Raw OCR text for debugging
    email_sender = Column(String(255))  # c00605mgr@chilis.com
    email_subject = Column(String(500))
    parsed_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
