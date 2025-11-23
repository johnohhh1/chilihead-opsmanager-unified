"""
Migration to add resolution tracking to agent_memory table
Run this to add the new columns to your existing database
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

def migrate():
    """Add resolution tracking columns to agent_memory table"""

    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/chilihead_ops')
    engine = create_engine(DATABASE_URL)

    print("Adding resolution tracking to agent_memory table...")

    with engine.connect() as conn:
        # Add updated_at column
        try:
            conn.execute(text("""
                ALTER TABLE agent_memory
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP
            """))
            print("✓ Added updated_at column")
        except Exception as e:
            print(f"  Column might already exist: {e}")

        # Add is_resolved column
        try:
            conn.execute(text("""
                ALTER TABLE agent_memory
                ADD COLUMN IF NOT EXISTS is_resolved BOOLEAN DEFAULT FALSE
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_agent_memory_is_resolved
                ON agent_memory(is_resolved)
            """))
            print("✓ Added is_resolved column with index")
        except Exception as e:
            print(f"  Column might already exist: {e}")

        # Add resolution_timestamp column
        try:
            conn.execute(text("""
                ALTER TABLE agent_memory
                ADD COLUMN IF NOT EXISTS resolution_timestamp TIMESTAMP
            """))
            print("✓ Added resolution_timestamp column")
        except Exception as e:
            print(f"  Column might already exist: {e}")

        # Add resolution_reason column
        try:
            conn.execute(text("""
                ALTER TABLE agent_memory
                ADD COLUMN IF NOT EXISTS resolution_reason TEXT
            """))
            print("✓ Added resolution_reason column")
        except Exception as e:
            print(f"  Column might already exist: {e}")

        # Commit all changes
        conn.commit()

    print("\nMigration complete! Your agent_memory table now supports resolution tracking.")

if __name__ == "__main__":
    migrate()