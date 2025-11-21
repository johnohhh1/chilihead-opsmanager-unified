"""
Initialize database and run all migrations
Run this script to set up the database properly
"""

import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import engine, Base
from models import (
    Task, Delegation, ChatSession, ChatMessage,
    EmailCache, EmailAnalysisCache, EmailAttachment,
    WatchedDomain, PortalDashboardMetrics, DismissedItem,
    AgentMemory
)
from sqlalchemy import text

def init_database():
    """Create all tables if they don't exist"""
    print("🔧 Initializing database...")

    try:
        # Create all tables from models
        print("Creating tables from models...")
        Base.metadata.create_all(engine)
        print("✅ All tables created successfully")

        # Check if email_attachments table exists and has correct column type
        with engine.connect() as conn:
            try:
                # Check if gmail_attachment_id column type is TEXT
                result = conn.execute(text("""
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_name = 'email_attachments'
                    AND column_name = 'gmail_attachment_id'
                """))
                row = result.fetchone()

                if row:
                    data_type = row[0]
                    if data_type != 'text':
                        print(f"⚠️  gmail_attachment_id is {data_type}, migrating to TEXT...")
                        conn.execute(text("""
                            ALTER TABLE email_attachments
                            ALTER COLUMN gmail_attachment_id TYPE TEXT;
                        """))
                        conn.commit()
                        print("✅ Migrated gmail_attachment_id to TEXT")
                    else:
                        print("✅ gmail_attachment_id is already TEXT")
                else:
                    print("ℹ️  email_attachments table created fresh with TEXT column")

            except Exception as e:
                print(f"Note: {e}")
                # Table might not exist yet, which is fine

        print("\n✅ Database initialization complete!")
        print("\n📋 Tables created:")
        print("   - tasks")
        print("   - delegations")
        print("   - chat_sessions")
        print("   - chat_messages")
        print("   - email_cache")
        print("   - email_analysis_cache")
        print("   - email_attachments (with TEXT gmail_attachment_id)")
        print("   - watched_domains")
        print("   - portal_dashboard_metrics")
        print("   - dismissed_items")
        print("   - agent_memory")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()
