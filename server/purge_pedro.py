"""
PURGE ALL PEDRO REFERENCES FROM DATABASE
This script removes all Pedro test data from the database
"""

from sqlalchemy import create_engine, text, or_
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import sys

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment
load_dotenv()

# Import models
from models import Task, Delegation, DismissedItem
from services.agent_memory import AgentMemory

def purge_pedro():
    """Remove all Pedro references from the database"""

    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/chilihead_ops')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*60)
    print("PURGING ALL PEDRO REFERENCES FROM DATABASE")
    print("="*60)

    total_deleted = 0

    # 1. Check and delete tasks
    print("\n1. Checking tasks table...")
    pedro_tasks = db.query(Task).filter(
        or_(
            Task.title.ilike('%pedro%'),
            Task.description.ilike('%pedro%')
        )
    ).all()

    if pedro_tasks:
        print(f"   Found {len(pedro_tasks)} tasks with Pedro:")
        for task in pedro_tasks:
            print(f"     - {task.title[:50]}...")
            db.delete(task)
        total_deleted += len(pedro_tasks)
    else:
        print("   No Pedro tasks found")

    # 2. Check and delete agent memory
    print("\n2. Checking agent_memory table...")
    pedro_memories = db.execute(text("""
        SELECT id, agent_type, summary FROM agent_memory
        WHERE summary ILIKE '%pedro%'
        OR context_data::text ILIKE '%pedro%'
        OR key_findings::text ILIKE '%pedro%'
        OR related_entities::text ILIKE '%pedro%'
    """)).fetchall()

    if pedro_memories:
        print(f"   Found {len(pedro_memories)} memory records with Pedro:")
        for mem in pedro_memories:
            # Clean summary for safe printing
            summary = str(mem.summary).encode('ascii', 'ignore').decode('ascii')
            print(f"     - [{mem.agent_type}] {summary[:50]}...")

        # Delete them
        db.execute(text("""
            DELETE FROM agent_memory
            WHERE summary ILIKE '%pedro%'
            OR context_data::text ILIKE '%pedro%'
            OR key_findings::text ILIKE '%pedro%'
            OR related_entities::text ILIKE '%pedro%'
        """))
        total_deleted += len(pedro_memories)
    else:
        print("   No Pedro memories found")

    # 3. Check and delete delegations
    print("\n3. Checking delegations table...")
    pedro_delegations = db.query(Delegation).filter(
        or_(
            Delegation.task_description.ilike('%pedro%'),
            Delegation.assigned_to.ilike('%pedro%')
        )
    ).all()

    if pedro_delegations:
        print(f"   Found {len(pedro_delegations)} delegations with Pedro:")
        for deleg in pedro_delegations:
            print(f"     - {deleg.task_description[:50]}...")
            db.delete(deleg)
        total_deleted += len(pedro_delegations)
    else:
        print("   No Pedro delegations found")

    # 4. Check and delete dismissed items
    print("\n4. Checking dismissed_items table...")
    pedro_dismissed = db.query(DismissedItem).filter(
        DismissedItem.identifier.ilike('%pedro%')
    ).all()

    if pedro_dismissed:
        print(f"   Found {len(pedro_dismissed)} dismissed items with Pedro:")
        for item in pedro_dismissed:
            print(f"     - {item.identifier[:50]}...")
            db.delete(item)
        total_deleted += len(pedro_dismissed)
    else:
        print("   No Pedro dismissed items found")

    # Commit all deletions
    if total_deleted > 0:
        db.commit()
        print("\n" + "="*60)
        print(f"SUCCESS: Deleted {total_deleted} total Pedro references!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("Database is clean - no Pedro references found!")
        print("="*60)

    db.close()

if __name__ == "__main__":
    purge_pedro()