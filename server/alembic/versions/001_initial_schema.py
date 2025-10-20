"""Initial schema - email_state, tasks, delegations, watch_config, ai_analysis_cache

Revision ID: 001
Revises: 
Create Date: 2025-10-19 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_state table
    op.create_table(
        'email_state',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email_id', sa.String(255), nullable=False, unique=True),
        sa.Column('thread_id', sa.String(255)),
        sa.Column('subject', sa.Text()),
        sa.Column('sender', sa.String(255)),
        sa.Column('received_at', sa.DateTime()),
        sa.Column('first_seen_at', sa.DateTime()),
        sa.Column('last_viewed_at', sa.DateTime()),
        sa.Column('is_acknowledged', sa.Boolean(), default=False),
        sa.Column('acknowledged_at', sa.DateTime()),
        sa.Column('ai_analysis', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_email_state_email_id', 'email_state', ['email_id'])
    op.create_index('ix_email_state_thread_id', 'email_state', ['thread_id'])
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('due_date', sa.Date()),
        sa.Column('priority', sa.String(20)),
        sa.Column('status', sa.String(20), default='todo'),
        sa.Column('source', sa.String(50)),
        sa.Column('source_id', sa.String(255)),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('gcal_event_id', sa.String(255)),
        sa.Column('eisenhower_quadrant', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='check_priority'),
        sa.CheckConstraint("status IN ('todo', 'in_progress', 'completed', 'cancelled')", name='check_status'),
    )
    
    # Create delegations table
    op.create_table(
        'delegations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_description', sa.Text(), nullable=False),
        sa.Column('assigned_to', sa.String(255)),
        sa.Column('assigned_to_email', sa.String(255)),
        sa.Column('due_date', sa.Date()),
        sa.Column('follow_up_date', sa.Date()),
        sa.Column('priority', sa.String(20)),
        sa.Column('status', sa.String(20), default='planning'),
        sa.Column('chilihead_progress', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('notification_sent_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("status IN ('planning', 'active', 'completed', 'on_hold')", name='check_delegation_status'),
    )
    
    # Create watch_config table
    op.create_table(
        'watch_config',
        sa.Column('id', sa.Integer(), primary_key=True, default=1),
        sa.Column('priority_senders', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('priority_domains', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('priority_keywords', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('excluded_subjects', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint('id = 1', name='single_row_constraint'),
    )
    
    # Create ai_analysis_cache table
    op.create_table(
        'ai_analysis_cache',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email_id', sa.String(255), nullable=False, unique=True),
        sa.Column('prompt_hash', sa.String(64)),
        sa.Column('analysis_result', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('model_used', sa.String(50)),
        sa.Column('tokens_used', sa.Integer()),
        sa.Column('analyzed_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_ai_analysis_cache_email_id', 'ai_analysis_cache', ['email_id'])
    
    # Insert default watch_config row
    op.execute("""
        INSERT INTO watch_config (id, priority_senders, priority_domains, priority_keywords, excluded_subjects)
        VALUES (1, '[]'::json, '[]'::json, '[]'::json, '[]'::json)
    """)


def downgrade() -> None:
    op.drop_table('ai_analysis_cache')
    op.drop_table('watch_config')
    op.drop_table('delegations')
    op.drop_table('tasks')
    op.drop_table('email_state')
