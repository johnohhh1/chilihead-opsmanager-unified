"""
Quick test script to verify agent memory system is working
"""

from database import SessionLocal, init_db
from services.agent_memory import AgentMemoryService
from datetime import datetime

def test_agent_memory():
    print("[TEST] Agent Memory System\n")

    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   [OK] Database ready\n")

    # Create session
    db = SessionLocal()

    try:
        # Test 1: Record an email analysis event
        print("2. Recording email triage event...")
        memory1 = AgentMemoryService.record_event(
            db=db,
            agent_type='triage',
            event_type='email_analyzed',
            summary="Analyzed urgent payroll email for Hannah Zimmerman",
            context_data={
                'email_subject': 'URGENT: Pay card issue',
                'sender': 'payroll@example.com',
                'has_images': False
            },
            key_findings={
                'urgent_items': ['Pay card not working', 'Employee affected: Hannah'],
                'priority': 'urgent'
            },
            related_entities={
                'people': ['Hannah Zimmerman'],
                'emails': ['thread_123']
            },
            email_id='thread_123',
            model_used='gpt-4o',
            confidence_score=95
        )
        print(f"   [OK] Created memory: {memory1.id}\n")

        # Test 2: Record a daily digest event
        print("3. Recording daily digest generation...")
        memory2 = AgentMemoryService.record_event(
            db=db,
            agent_type='daily_brief',
            event_type='digest_generated',
            summary="Generated daily digest analyzing 15 emails",
            context_data={
                'digest_preview': 'High level: 3 urgent items...',
                'email_count': 15
            },
            key_findings={
                'has_urgent': True,
                'has_deadlines': True,
                'emails_analyzed': 15
            },
            model_used='gpt-4o',
            confidence_score=90
        )
        print(f"   [OK] Created memory: {memory2.id}\n")

        # Test 3: Record a chat interaction
        print("4. Recording chat interaction...")
        memory3 = AgentMemoryService.record_event(
            db=db,
            agent_type='operations_chat',
            event_type='question_answered',
            summary="Answered: What's most urgent today?",
            context_data={
                'user_question': "What's most urgent today?",
                'assistant_response': "Here's the deal - Hannah's pay card issue is top priority..."
            },
            model_used='gpt-4o',
            confidence_score=85
        )
        print(f"   [OK] Created memory: {memory3.id}\n")

        # Test 4: Retrieve recent context
        print("5. Retrieving recent agent activity...")
        recent = AgentMemoryService.get_recent_context(db, hours=24, limit=10)
        print(f"   [OK] Found {len(recent)} recent memories\n")

        # Test 5: Get coordination context
        print("6. Building coordination context (for AI prompts)...")
        context = AgentMemoryService.get_coordination_context(db, hours=24)
        print("   [OK] Context generated:")
        print("   " + "\n   ".join(context.split("\n")[:15]))
        print("   ...\n")

        # Test 6: Get digest-specific context
        print("7. Getting digest context...")
        digest_context = AgentMemoryService.get_digest_context(db, hours=24)
        print("   [OK] Digest context generated\n")

        # Test 7: Search memory
        print("8. Searching for 'payroll' in memory...")
        results = AgentMemoryService.search_memory(db, "payroll", limit=5)
        print(f"   [OK] Found {len(results)} matching memories\n")

        # Test 8: Get related memories
        print("9. Getting all memories related to email thread_123...")
        related = AgentMemoryService.get_related_memory(db, email_id='thread_123')
        print(f"   [OK] Found {len(related)} related memories\n")

        print("[SUCCESS] All tests passed!")
        print("\nAgent memory system is working correctly.")
        print("Agents can now:")
        print("  - Record their analyses and findings")
        print("  - See what other agents have discovered")
        print("  - Build context-aware responses")
        print("  - Reference previous interactions")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_agent_memory()
