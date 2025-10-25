"""Test Google Tasks API connection"""
import sys
sys.path.insert(0, '.')

from services.google_tasks import get_tasks_service
from googleapiclient.errors import HttpError

def test_google_tasks():
    print("Testing Google Tasks API...")

    try:
        service = get_tasks_service()
        print("[OK] Service connection established")

        # Try to create a test task
        task_body = {
            'title': 'Test from ChiliHead OpsManager',
            'notes': 'This is a test task to verify API access'
        }

        print(f"\nAttempting to create task in '@default' list...")
        result = service.tasks().insert(
            tasklist='@default',
            body=task_body
        ).execute()

        print("[SUCCESS] Task created:")
        print(f"  - ID: {result['id']}")
        print(f"  - Title: {result['title']}")
        print(f"  - Link: {result.get('selfLink', 'N/A')}")

        return True

    except HttpError as e:
        print(f"\n[ERROR] HTTP Error occurred:")
        print(f"  - Status Code: {e.resp.status}")
        print(f"  - Reason: {e.resp.reason}")

        if hasattr(e, 'error_details') and e.error_details:
            print(f"  - Details: {e.error_details}")
        else:
            print(f"  - Error: {e}")

        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error:")
        print(f"  - {type(e).__name__}: {e}")
        return False

if __name__ == '__main__':
    success = test_google_tasks()
    sys.exit(0 if success else 1)
