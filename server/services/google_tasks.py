"""
Google Tasks integration for syncing todo items
"""

import os
import json
import pathlib
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tokens"

def get_tasks_service():
    """Get authenticated Google Tasks service"""
    from google.auth.transport.requests import Request

    token_path = TOKENS_DIR / "user_dev.json"

    if not token_path.exists():
        raise Exception("Not authenticated with Google")

    with open(token_path, "r") as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    # Refresh token if expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(token_path, "w") as f:
                json.dump(json.loads(creds.to_json()), f, indent=2)
        else:
            raise Exception("Invalid credentials - please re-authenticate")

    return build('tasks', 'v1', credentials=creds)

def create_google_task(
    title: str,
    description: str = "",
    due_date: str = None,
    priority: str = "normal"
) -> dict:
    """
    Create a Google Task

    Args:
        title: Task title
        description: Task description/notes
        due_date: Due date in ISO format (YYYY-MM-DD) or None
        priority: Task priority (used for sorting/context, not directly mapped)

    Returns:
        dict with task details including ID
    """
    try:
        service = get_tasks_service()

        # Build task object
        task_body = {
            'title': title,
        }

        # Add notes (description) if provided
        if description:
            task_body['notes'] = description

        # Add due date if provided (must be RFC 3339 timestamp format)
        if due_date:
            try:
                # Parse date and convert to RFC 3339 format (midnight UTC)
                if 'T' in due_date:
                    # Already in ISO format with time
                    due_datetime = datetime.fromisoformat(due_date.replace('Z', ''))
                else:
                    # Just a date, add time component
                    due_datetime = datetime.strptime(due_date, '%Y-%m-%d')

                # Google Tasks wants RFC 3339 format (YYYY-MM-DDTHH:MM:SS.000Z)
                task_body['due'] = due_datetime.strftime('%Y-%m-%dT00:00:00.000Z')
            except Exception as e:
                print(f"Warning: Could not parse due_date '{due_date}': {e}")

        # Create task in default task list
        result = service.tasks().insert(
            tasklist='@default',
            body=task_body
        ).execute()

        return {
            'success': True,
            'task_id': result['id'],
            'title': result['title'],
            'self_link': result.get('selfLink'),
            'due': result.get('due'),
        }

    except HttpError as error:
        error_detail = error.error_details[0] if error.error_details else {}
        error_message = error_detail.get('message', str(error))

        # Check if it's a permission issue
        if error.resp.status == 403 or 'Insufficient Permission' in error_message or 'insufficient authentication scopes' in error_message.lower():
            return {
                'success': False,
                'error': "Google Tasks permission not granted. Please re-authenticate with Google to enable Tasks access.",
                'needs_reauth': True
            }

        return {
            'success': False,
            'error': f"Google Tasks API error: {error_message}"
        }
    except Exception as e:
        error_str = str(e)
        if 'not authenticated' in error_str.lower() or 'invalid credentials' in error_str.lower():
            return {
                'success': False,
                'error': "Google authentication required. Please re-authenticate with Google.",
                'needs_reauth': True
            }
        return {
            'success': False,
            'error': error_str
        }

def get_google_task(task_id: str) -> dict:
    """
    Get a specific Google Task by ID

    Args:
        task_id: Google Task ID

    Returns:
        dict with task details or error
    """
    try:
        service = get_tasks_service()

        result = service.tasks().get(
            tasklist='@default',
            task=task_id
        ).execute()

        return {
            'success': True,
            'task': result
        }

    except HttpError as error:
        return {
            'success': False,
            'error': f"Google Tasks API error: {error}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def list_google_tasks(max_results: int = 100) -> dict:
    """
    List all tasks from the default task list

    Args:
        max_results: Maximum number of tasks to return

    Returns:
        dict with tasks list or error
    """
    try:
        service = get_tasks_service()

        result = service.tasks().list(
            tasklist='@default',
            maxResults=max_results
        ).execute()

        tasks = result.get('items', [])

        return {
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        }

    except HttpError as error:
        return {
            'success': False,
            'error': f"Google Tasks API error: {error}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
