#!/usr/bin/env python
"""
Purge cached analysis for RAP Mobile emails to force fresh vision analysis
"""

import sys
import os
sys.path.append('server')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment from server directory
load_dotenv('server/.env')

def purge_rap_mobile_cache():
    """Delete cached analysis for RAP Mobile emails"""

    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://openinbox:devpass123@localhost:5432/openinbox_dev')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*60)
    print("PURGING RAP MOBILE CACHED ANALYSIS")
    print("="*60)

    # Find and delete cached analysis for RAP Mobile threads
    result = db.execute(text("""
        DELETE FROM email_analysis_cache
        WHERE thread_id IN (
            SELECT DISTINCT thread_id
            FROM email_cache
            WHERE LOWER(subject) LIKE '%rap mobile%'
               OR LOWER(subject) LIKE '%tableau%'
               OR LOWER(subject) LIKE '%dashboard%'
        )
        RETURNING thread_id, model_used
    """)).fetchall()

    if result:
        print(f"\nDeleted {len(result)} cached analyses:")
        for thread_id, model in result:
            print(f"  - Thread: {thread_id[:20]}... (model: {model})")
    else:
        print("\nNo cached RAP Mobile analyses found")

    # Also clear AI analysis from email_state
    result2 = db.execute(text("""
        UPDATE email_state
        SET ai_analysis = NULL
        WHERE thread_id IN (
            SELECT DISTINCT thread_id
            FROM email_cache
            WHERE LOWER(subject) LIKE '%rap mobile%'
               OR LOWER(subject) LIKE '%tableau%'
               OR LOWER(subject) LIKE '%dashboard%'
        )
        RETURNING thread_id
    """)).fetchall()

    if result2:
        print(f"\nCleared AI analysis for {len(result2)} email states")

    # Commit changes
    db.commit()

    print("\n" + "="*60)
    print("CACHE PURGED!")
    print("="*60)
    print("\nNext steps:")
    print("1. Go to Smart Inbox")
    print("2. Find a RAP Mobile email")
    print("3. Select GPT-4o from dropdown")
    print("4. Click 'Re-analyze'")
    print("5. This will now force fresh vision analysis")

    db.close()

if __name__ == "__main__":
    purge_rap_mobile_cache()