"""Add google_task_id to tasks

Revision ID: 003
Revises: 002
Create Date: 2025-10-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add google_task_id column to tasks table
    op.add_column('tasks', sa.Column('google_task_id', sa.String(255), nullable=True))


def downgrade():
    # Remove google_task_id column from tasks table
    op.drop_column('tasks', 'google_task_id')
