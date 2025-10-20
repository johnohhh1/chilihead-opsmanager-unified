"""Add chat tables

Revision ID: 002
Revises: 001
Create Date: 2024-10-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, server_default='john'),
        sa.Column('title', sa.String(255)),
        sa.Column('context_snapshot', postgresql.JSON),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('message_count', sa.Integer, server_default='0'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
    )

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('context_used', postgresql.JSON),
        sa.Column('model_used', sa.String(50)),
        sa.Column('tokens_used', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_message_role'),
    )

    # Create indexes
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_is_active', 'chat_sessions', ['is_active'])


def downgrade():
    op.drop_index('ix_chat_sessions_is_active', 'chat_sessions')
    op.drop_index('ix_chat_sessions_user_id', 'chat_sessions')
    op.drop_index('ix_chat_messages_session_id', 'chat_messages')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
