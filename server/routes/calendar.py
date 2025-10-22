"""
Google Calendar API routes
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.google_calendar import create_calendar_event, list_calendar_events

router = APIRouter()

class CreateEventRequest(BaseModel):
    title: str
    date: str
    time: str = "10:00 AM"
    description: str = ""
    location: str = ""
    reminder_days: int = 3

@router.post("/calendar/create-event")
async def create_event(request: CreateEventRequest):
    """Create a Google Calendar event"""
    try:
        result = create_calendar_event(
            title=request.title,
            date=request.date,
            time=request.time,
            description=request.description,
            location=request.location,
            reminder_days=request.reminder_days
        )

        if not result.get('success'):
            raise HTTPException(500, result.get('error', 'Failed to create event'))

        return result

    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/calendar/events")
async def get_events(days_ahead: int = Query(default=30, ge=1, le=365)):
    """Get upcoming calendar events"""
    try:
        result = list_calendar_events(days_ahead=days_ahead)

        if not result.get('success'):
            raise HTTPException(500, result.get('error', 'Failed to fetch events'))

        return result

    except Exception as e:
        raise HTTPException(500, str(e))
