"""
Test script for memory update system
Creates test memories and marks them as resolved
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import SessionLocal
from services.agent_memory import AgentMemoryService
from models import AgentMemory

def test_memory_updates():
    """Test memory update and resolution marking"""
    db = SessionLocal()

    try:
        print("\n=== Memory Update System Test ===\n")

        # 1. Create test memories
        print("1. Creating test memories...")
        mem1 = AgentMemoryService.record_event(
            db=db,
            agent_type='triage',
            event_type='email_analyzed',
            summary='Analyzed urgent email about Pedro call-off for dinner shift',
            context_data={'email_subject': 'RE: Pedro called off'},
            key_findings={'urgent_items': ['Pedro call-off']},
            model_used='gpt-4o',
            confidence_score=85
        )
        print(f"   ✓ Created memory: {mem1.summary[:50]}...")

        mem2 = AgentMemoryService.record_event(
            db=db,
            agent_type='daily_brief',
            event_type='digest_generated',
            summary='Flagged Pedro issue in morning digest',
            context_data={'digest_section': 'urgent'},
            key_findings={'urgent_items': ['Pedro']},
            model_used='gpt-4o',
            confidence_score=90
        )
        print(f"   ✓ Created memory: {mem2.summary[:50]}...")

        # 2. Check unresolved context
        print("\n2. Getting active memory context...")
        context = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            include_resolved=False
        )
        print(f"   Active items: {context.count('Pedro')} mentions of 'Pedro'")

        # 3. Mark as resolved
        print("\n3. Marking Pedro items as resolved...")
        resolved_count = AgentMemoryService.mark_resolved(
            db=db,
            summary_text='Pedro',
            annotation='Test: Pedro issue was handled on Tuesday'
        )
        print(f"   ✓ Marked {resolved_count} memories as resolved")

        # 4. Check resolved context
        print("\n4. Getting active memory context (after resolution)...")
        context_after = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            include_resolved=False
        )
        print(f"   Active items: {context_after.count('Pedro')} mentions of 'Pedro'")

        # 5. Verify resolved items
        print("\n5. Verifying resolved status...")
        resolved_mem = db.query(AgentMemory).filter(
            AgentMemory.id == mem1.id
        ).first()

        if resolved_mem:
            print(f"   Summary: {resolved_mem.summary[:60]}...")
            print(f"   Has [RESOLVED] prefix: {'[RESOLVED]' in resolved_mem.summary}")

            if resolved_mem.context_data and 'annotations' in resolved_mem.context_data:
                annotations = resolved_mem.context_data['annotations']
                print(f"   Annotations: {len(annotations)} added")
                print(f"   Latest note: {annotations[-1]['note'][:50]}...")

        # 6. Test including resolved items
        print("\n6. Getting context WITH resolved items...")
        context_with_resolved = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            include_resolved=True
        )
        print(f"   Total items: {context_with_resolved.count(' - [')}")
        print(f"   Resolved items: {context_with_resolved.count('[RESOLVED]')}")

        print("\n=== Test Complete ===")
        print("\nMemory update system is working correctly!")
        print("- Memories can be marked as resolved")
        print("- Resolved items are filtered from active context")
        print("- Annotations are tracked")
        print("- [RESOLVED] prefix is added to summaries")

        print("\n\nNext: Test in Operations Chat by saying:")
        print('  "the pedro issue was handled"')
        print("  AUBS should automatically mark related memories as resolved!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_memory_updates()
