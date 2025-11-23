"""
Test the new entity extraction system
"""

# Add parent directory to path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.entity_schema import EntityExtractor, extract_entity_names

def test_entity_extraction():
    print("Testing Entity Extraction System")
    print("="*50)

    # Test 1: Real email content with actual names
    test_email = """
    Subject: Urgent staffing issue

    Maria called off for tonight's shift from 5-10pm.
    I've reached out to Carlos and Jennifer to see if they can cover.
    Carlos confirmed he can work but Jennifer hasn't responded yet.

    Also, the District Manager Thompson wants the P5 schedule by Friday.
    """

    print("\nTest 1: Real email with actual names")
    print("-"*30)
    entities = EntityExtractor.extract_entities(test_email, 'email')
    for entity in entities:
        print(f"  {entity.name}: confidence={entity.confidence:.1f}%, "
              f"frequency={entity.frequency}, is_example={entity.is_example}")

    # Test 2: Content with example names (from prompts)
    test_prompt = """
    Examples of good summaries:
    ✓ "Hannah's pay card failed - she hasn't been paid in 48 hours"
    ✗ "Pedro called off for tonight"

    When Blake requests schedule changes, notify immediately.
    """

    print("\nTest 2: Prompt with example names")
    print("-"*30)
    entities = EntityExtractor.extract_entities(test_prompt, 'prompt')
    for entity in entities:
        print(f"  {entity.name}: confidence={entity.confidence:.1f}%, "
              f"frequency={entity.frequency}, is_example={entity.is_example}")

    # Test 3: Mixed content (real + examples)
    test_mixed = """
    Email Analysis:

    Robert submitted his availability for next week. He can work any shift
    except Tuesday evening. Robert also mentioned he's available for overtime.

    This is similar to the Pedro situation from last week where we had coverage issues.
    Hannah and Blake were examples in our training materials.

    Please confirm with Robert about his Tuesday restriction.
    """

    print("\nTest 3: Mixed content (real + examples)")
    print("-"*30)
    entities = EntityExtractor.extract_entities(test_mixed, 'email')
    for entity in entities:
        print(f"  {entity.name}: confidence={entity.confidence:.1f}%, "
              f"frequency={entity.frequency}, is_example={entity.is_example}")

    # Test 4: Backward compatibility function
    print("\nTest 4: Backward compatibility (extract_entity_names)")
    print("-"*30)
    names = extract_entity_names(test_email, 'email')
    print(f"  Extracted names: {names}")

    # Test 5: No false positives from common words
    test_common = """
    The Monday schedule shows that Sales exceeded Budget by 15%.
    Labor variance for December was unfavorable.
    Food cost for Friday Evening was within target.
    The System reported an Error in the Database.
    """

    print("\nTest 5: Common words (should not extract these)")
    print("-"*30)
    entities = EntityExtractor.extract_entities(test_common, 'email')
    if entities:
        for entity in entities:
            print(f"  {entity.name}: confidence={entity.confidence:.1f}%")
    else:
        print("  [OK] No false positives - working correctly!")

    # Test 6: User corrections (like "pedro was handled")
    test_correction = """
    The pedro issue was resolved yesterday.
    That hannah thing is taken care of.
    """

    print("\nTest 6: User corrections mentioning old examples")
    print("-"*30)
    entities = EntityExtractor.extract_entities(test_correction, 'user_input')
    for entity in entities:
        print(f"  {entity.name}: confidence={entity.confidence:.1f}%, "
              f"is_example={entity.is_example}")

if __name__ == "__main__":
    test_entity_extraction()