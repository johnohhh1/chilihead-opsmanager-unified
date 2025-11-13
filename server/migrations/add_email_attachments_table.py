"""
Migration: Add email_attachments table
Created: 2025-01-12
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import engine
from models import Base, EmailAttachment

def run_migration():
    """Create email_attachments table"""
    print("Creating email_attachments table...")
    EmailAttachment.__table__.create(engine, checkfirst=True)
    print("[OK] Migration complete")

if __name__ == "__main__":
    run_migration()
