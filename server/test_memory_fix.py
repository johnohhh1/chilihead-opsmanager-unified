"""
Test script to verify memory coordination fixes work correctly
Run this to ensure memory updates propagate between agents
"""

from database import SessionLocal
from services.agent_memory import AgentMemoryService
from datetime import datetime

def test_memory_coordination():
    """
    Test the complete memory update flow:
    1. Create test memories (simulating email triage + daily brief)
    2. Mark them as resolved (simulating user chat correction)
    3. Verify daily brief context excludes resolved items
    """
    db = SessionLocal()

    try:
        print("\n" + "="*70)
        print("MEMORY COORDINATION FIX - VERIFICATION TEST")
        print("="*70 + "\n")

        # Step 1: Create test memories (simulate triage agent flagging Pedro issue)
        print("1. Creating test memories (simulating email triage)...")
        mem1 = AgentMemoryService.record_event(
            db=db,
            agent_type='triage',
            event_type='email_analyzed',
            summary='Analyzed urgent email about Pedro calling off dinner shift',
            context_data={'email_subject': 'RE: Pedro called off - need coverage ASAP'},
            key_findings={'urgent': True, 'coverage_needed': True},
            email_id='test_email_123',
            model_used='gpt-4o',
            confidence_score=90
        )
        print(f"   ✓ Triage memory created: {mem1.summary[:60]}...")

        mem2 = AgentMemoryService.record_event(
            db=db,
            agent_type='daily_brief',
            event_type='digest_generated',
            summary='Flagged Pedro coverage issue in morning digest',
            context_data={'digest_section': 'urgent_action_needed'},
            key_findings={'urgent_items': ['Pedro coverage']},
            model_used='gpt-4o',
            confidence_score=95
        )
        print(f"   ✓ Daily brief memory created: {mem2.summary[:60]}...")
        print()

        # Step 2: Verify memories appear in coordination context (should be ACTIVE)
        print("2. Checking initial memory state (should be ACTIVE)...")
        context_before = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            format="text",
            include_resolved=False  # Should include our memories (not resolved yet)
        )

        if 'Pedro' in context_before and '[RESOLVED]' not in context_before:
            print("   ✓ Pedro issue appears in active memory context")
        else:
            print("   ✗ ISSUE: Pedro not found in active context!")
            print(f"   Context preview: {context_before[:300]}")
        print()

        # Step 3: Simulate user correcting via chat (mark as resolved)
        print("3. User tells chat: 'update the memory that pedro was handled'")
        print("   Marking Pedro memories as resolved...")
        resolved_count = AgentMemoryService.mark_resolved(
            db=db,
            summary_text='Pedro',
            annotation="User correction: Pedro issue was handled"
        )
        print(f"   ✓ Marked {resolved_count} memories as resolved")
        print()

        # Step 4: Verify memories are NOW excluded from context (should be RESOLVED)
        print("4. Checking memory state after update (should be RESOLVED)...")
        context_after = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            format="text",
            include_resolved=False  # Should NOT include our memories now
        )

        # Check that Pedro is NOT in the active context anymore
        pedro_in_active = 'Pedro' in context_after and '[RESOLVED]' not in context_after

        if not pedro_in_active:
            print("   ✓ Pedro issue NO LONGER appears in active memory context")
            print("   ✓ Memory update propagated correctly!")
        else:
            print("   ✗ ISSUE: Pedro STILL appears in active context after resolution!")
            print(f"   Context preview: {context_after[:300]}")
        print()

        # Step 5: Verify we can still see resolved items if requested
        print("5. Verifying resolved items are tracked (include_resolved=True)...")
        context_with_resolved = AgentMemoryService.get_coordination_context(
            db=db,
            hours=24,
            format="text",
            include_resolved=True  # Should include resolved items
        )

        if '[RESOLVED]' in context_with_resolved and 'Pedro' in context_with_resolved:
            print("   ✓ Resolved items are properly tracked with [RESOLVED] prefix")
        else:
            print("   ✗ ISSUE: Resolved items not tracked properly!")
        print()

        # Step 6: Test search memory (for debugging)
        print("6. Testing search_memory() for 'Pedro'...")
        search_results = AgentMemoryService.search_memory(db, 'Pedro', limit=10)
        print(f"   Found {len(search_results)} memory entries")
        for mem in search_results:
            status = "[RESOLVED]" if "[RESOLVED]" in mem.summary else "[ACTIVE]"
            print(f"   {status} {mem.agent_type}: {mem.summary[:60]}...")
        print()

        # Final Summary
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✓ Created {2} test memories")
        print(f"✓ Marked {resolved_count} memories as resolved")
        print(f"✓ Memory updates propagated: {'YES' if not pedro_in_active else 'NO'}")
        print(f"✓ Daily brief will exclude resolved items: {'YES' if not pedro_in_active else 'NO'}")
        print()

        if not pedro_in_active:
            print("🎉 SUCCESS! Memory coordination is working correctly.")
            print("   User corrections now propagate to all agents!")
        else:
            print("⚠️  FAILED! Memory coordination still has issues.")
            print("   Check database session isolation and cache expiry.")

        print("="*70 + "\n")

        # Cleanup test data
        print("Cleaning up test memories...")
        db.query(AgentMemoryService).filter(
            AgentMemoryService.id.in_([mem1.id, mem2.id])
        ).delete()
        db.commit()
        print("✓ Test cleanup complete\n")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    test_memory_coordination()
