"""add delegation phone number

Revision ID: 004
Revises: 003
Create Date: 2025-11-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add assigned_to_phone column to delegations table
    op.add_column('delegations', sa.Column('assigned_to_phone', sa.String(20), nullable=True))


def downgrade():
    # Remove assigned_to_phone column from delegations table
    op.drop_column('delegations', 'assigned_to_phone')
