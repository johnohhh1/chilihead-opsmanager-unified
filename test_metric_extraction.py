#!/usr/bin/env python
"""
Test script to verify RAP Mobile dashboard metric extraction
"""

import sys
import os
sys.path.append('server')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_rap_mobile_analysis():
    """Test if AI extracts metrics from RAP Mobile dashboards"""

    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/chilihead_ops')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*60)
    print("RAP MOBILE METRIC EXTRACTION TEST")
    print("="*60)

    # Find a recent RAP Mobile email thread
    result = db.execute(text("""
        SELECT DISTINCT et.thread_id, et.subject
        FROM email_threads et
        WHERE LOWER(et.subject) LIKE '%rap mobile%'
           OR LOWER(et.subject) LIKE '%tableau%'
           OR LOWER(et.subject) LIKE '%dashboard%'
        ORDER BY et.last_message_date DESC
        LIMIT 3
    """)).fetchall()

    if not result:
        print("No RAP Mobile threads found in database!")
        print("Please sync emails first to get dashboard emails.")
        db.close()
        return

    print(f"\nFound {len(result)} RAP Mobile threads:")
    for thread_id, subject in result:
        print(f"  - {thread_id}: {subject}")

    # Test the first thread
    test_thread = result[0][0]
    print(f"\nTesting thread: {test_thread}")
    print("-" * 40)

    # Import the triage service
    from services.ai_triage import summarize_thread_advanced

    # Analyze with vision enabled
    print("\n[TEST] Calling AI with vision analysis...")
    result = summarize_thread_advanced(test_thread, use_vision=True, db=db)

    # Check if metrics were extracted
    summary = result.get('summary', '')

    print("\n" + "="*60)
    print("ANALYSIS RESULTS:")
    print("="*60)
    print(summary[:2000])  # First 2000 chars

    print("\n" + "="*60)
    print("METRIC EXTRACTION CHECK:")
    print("="*60)

    # Check for specific metric indicators
    has_dollars = '$' in summary
    has_percents = '%' in summary

    if has_dollars:
        # Count dollar amounts
        dollar_count = summary.count('$')
        print(f"✅ Found {dollar_count} dollar amounts in analysis")
    else:
        print("❌ No dollar amounts found - AI did not extract financial metrics!")

    if has_percents:
        # Count percentages
        percent_count = summary.count('%')
        print(f"✅ Found {percent_count} percentages in analysis")
    else:
        print("❌ No percentages found - AI did not extract performance metrics!")

    # Check for specific metric keywords
    metric_keywords = [
        'Sales:', 'Labor:', 'Food Cost:', 'Bar Cost:',
        'Guest Count:', 'Check Average:', 'COGS:'
    ]

    found_metrics = []
    for keyword in metric_keywords:
        if keyword in summary:
            found_metrics.append(keyword)

    if found_metrics:
        print(f"\n✅ Detected metrics: {', '.join(found_metrics)}")
    else:
        print("\n❌ No specific metrics detected - prompt may not be working!")

    # Overall assessment
    print("\n" + "="*60)
    print("ASSESSMENT:")
    print("="*60)

    if has_dollars and has_percents and len(found_metrics) > 2:
        print("✅ SUCCESS: AI is extracting dashboard metrics!")
        print("The prompt changes are working correctly.")
    else:
        print("⚠️ PARTIAL: AI sees the dashboard but isn't extracting all metrics.")
        print("The prompt may need to be even more forceful.")
        print("\nSuggestion: The AI might be using a cached response.")
        print("Try re-analyzing a thread from Smart Inbox to force a fresh analysis.")

    db.close()

if __name__ == "__main__":
    test_rap_mobile_analysis()