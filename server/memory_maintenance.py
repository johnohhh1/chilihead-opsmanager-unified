"""
Memory Maintenance Script
Run this to clean up, resolve, and maintain agent memory
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from services.memory_manager import MemoryManager
from datetime import datetime
import argparse

# Load environment
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='Maintain agent memory system')
    parser.add_argument('--cleanup', action='store_true', help='Clean up resolved memories')
    parser.add_argument('--expire', action='store_true', help='Expire old memories')
    parser.add_argument('--dedupe', action='store_true', help='Remove duplicate memories')
    parser.add_argument('--resolve', help='Resolve memories about a topic (e.g., "pedro")')
    parser.add_argument('--auto-resolve', action='store_true', help='Apply auto-resolution rules')
    parser.add_argument('--status', action='store_true', help='Show active issues')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without doing it')
    parser.add_argument('--all', action='store_true', help='Run all maintenance tasks')

    args = parser.parse_args()

    # Connect to database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/chilihead_ops')
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("="*60)
    print("AGENT MEMORY MAINTENANCE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # If no specific action, show status
    if not any([args.cleanup, args.expire, args.dedupe, args.resolve,
                args.auto_resolve, args.all]):
        args.status = True

    # Show active issues
    if args.status or args.all:
        print("\nACTIVE ISSUES:")
        print("-"*40)
        issues = MemoryManager.get_active_issues(db)

        if issues:
            for issue in issues[:10]:  # Show top 10
                urgency = "[URGENT]" if issue['urgent'] else "[Normal]"
                age = f"{issue['age_days']}d ago" if issue['age_days'] > 0 else "Today"
                # Clean summary for safe printing
                summary = str(issue['summary']).encode('ascii', 'ignore').decode('ascii')
                print(f"{urgency} [{age}] {summary[:60]}...")

            if len(issues) > 10:
                print(f"... and {len(issues) - 10} more active issues")
        else:
            print("[OK] No active issues found!")

    # Resolve specific topic
    if args.resolve:
        print(f"\nRESOLVING '{args.resolve}':")
        print("-"*40)
        count = MemoryManager.smart_resolve(db, args.resolve)
        print(f"Resolved {count} memories about '{args.resolve}'")

    # Apply auto-resolution rules
    if args.auto_resolve or args.all:
        print("\nAUTO-RESOLUTION:")
        print("-"*40)
        count = MemoryManager.apply_resolution_rules(db)
        print(f"Auto-resolved {count} memories based on patterns")

    # Clean up resolved memories
    if args.cleanup or args.all:
        print("\nCLEANUP RESOLVED:")
        print("-"*40)
        stats = MemoryManager.cleanup_resolved_memories(db, dry_run=args.dry_run)
        print(f"Deleted: {stats['deleted']} old resolved memories")
        print(f"Kept: {stats['kept']} recent resolved memories")

        if args.dry_run and stats['details']:
            print("\nWould delete:")
            for detail in stats['details'][:5]:
                print(f"  - {detail['summary']} (resolved {detail['age_days']} days ago)")

    # Expire old memories
    if args.expire or args.all:
        print("\nEXPIRE OLD MEMORIES:")
        print("-"*40)
        stats = MemoryManager.expire_old_memories(db, dry_run=args.dry_run)
        print(f"Expired: {stats['expired']} old memories")

        if stats['by_type']:
            print("By type:")
            for event_type, count in stats['by_type'].items():
                print(f"  - {event_type}: {count}")

    # Deduplicate
    if args.dedupe or args.all:
        print("\nDEDUPLICATE:")
        print("-"*40)
        stats = MemoryManager.deduplicate_memories(db, dry_run=args.dry_run)
        print(f"Removed: {stats['duplicates_removed']} duplicate memories")
        print(f"Kept: {stats['unique_kept']} unique memories")

    # Summary
    print("\n" + "="*60)
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes were made")
    else:
        print("MAINTENANCE COMPLETE")
    print("="*60)

    db.close()

if __name__ == "__main__":
    main()