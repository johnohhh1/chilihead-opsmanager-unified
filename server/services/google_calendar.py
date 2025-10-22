"""
Google Calendar integration for creating events from deadlines
"""

import os
import json
import pathlib
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKENS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tokens"

def get_calendar_service():
    """Get authenticated Google Calendar service"""
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

    return build('calendar', 'v3', credentials=creds)

def create_calendar_event(
    title: str,
    date: str,
    time: str = "10:00 AM",
    description: str = "",
    location: str = "",
    reminder_days: int = 3
) -> dict:
    """
    Create a Google Calendar event

    Args:
        title: Event title
        date: Date in format "YYYY-MM-DD" or "Mon DD YYYY"
        time: Time in format "HH:MM AM/PM" (default: 10:00 AM)
        description: Event description
        location: Event location
        reminder_days: Days before event to send reminder (default: 3)

    Returns:
        dict with event details including link
    """
    try:
        service = get_calendar_service()

        # Parse date and time
        start_datetime = parse_datetime(date, time)
        end_datetime = start_datetime + timedelta(hours=1)  # 1 hour duration

        # Build event
        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'America/Detroit',  # Eastern Time
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'America/Detroit',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': reminder_days * 24 * 60},  # Email reminder
                    {'method': 'popup', 'minutes': 24 * 60},  # 1 day before popup
                ],
            },
        }

        # Create event
        event_result = service.events().insert(calendarId='primary', body=event).execute()

        return {
            'success': True,
            'event_id': event_result['id'],
            'event_link': event_result.get('htmlLink'),
            'title': title,
            'start': start_datetime.isoformat(),
        }

    except HttpError as error:
        return {
            'success': False,
            'error': f'Calendar API error: {error}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def list_calendar_events(days_ahead: int = 30) -> dict:
    """
    List upcoming calendar events

    Args:
        days_ahead: Number of days ahead to fetch events (default: 30)

    Returns:
        dict with events list or error
    """
    try:
        service = get_calendar_service()

        # Get events from now to X days ahead
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        time_max = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        return {
            'success': True,
            'events': events,
            'count': len(events)
        }

    except HttpError as error:
        return {
            'success': False,
            'error': f'Calendar API error: {error}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_datetime(date_str: str, time_str: str) -> datetime:
    """Parse date and time strings into datetime object"""

    # Try parsing YYYY-MM-DD format
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # Try parsing "Mon DD YYYY" format
        try:
            date_obj = datetime.strptime(date_str, '%b %d %Y')
        except ValueError:
            # Try parsing "Month DD YYYY" format
            date_obj = datetime.strptime(date_str, '%B %d %Y')

    # Parse time
    time_obj = datetime.strptime(time_str, '%I:%M %p')

    # Combine date and time
    combined = datetime(
        date_obj.year, date_obj.month, date_obj.day,
        time_obj.hour, time_obj.minute
    )

    return combined
