"""
Migration: Fix gmail_attachment_id column length
Gmail attachment IDs can be longer than 255 characters
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import engine
from sqlalchemy import text

def migrate():
    """Alter gmail_attachment_id from VARCHAR(255) to TEXT"""

    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE email_attachments
            ALTER COLUMN gmail_attachment_id TYPE TEXT;
        """))
        conn.commit()
        print("[OK] Changed gmail_attachment_id to TEXT")

if __name__ == "__main__":
    migrate()
