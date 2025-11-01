from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from database import get_db
from models import Delegation as DelegationModel
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Twilio credentials from environment
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# Check if Twilio is configured
TWILIO_ENABLED = all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER])

if TWILIO_ENABLED:
    try:
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except ImportError:
        TWILIO_ENABLED = False
        twilio_client = None
else:
    twilio_client = None


class Manager(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    active_delegations: int = 0


class SendSMSRequest(BaseModel):
    manager_id: str
    message: str
    phone_number: Optional[str] = None


@router.get("/sms/managers")
async def get_managers(db: Session = Depends(get_db)):
    """Get list of all managers from delegations"""
    try:
        # Get all delegations
        delegations = db.query(DelegationModel).all()

        # Group by assigned_to to get unique managers
        managers_dict = {}
        for delegation in delegations:
            if delegation.assigned_to:
                if delegation.assigned_to not in managers_dict:
                    managers_dict[delegation.assigned_to] = {
                        "id": delegation.id,  # Using first delegation ID as manager ID
                        "name": delegation.assigned_to,
                        "email": delegation.assigned_to_email,
                        "phone": getattr(delegation, 'assigned_to_phone', None),
                        "active_delegations": 0
                    }

                # Count active delegations
                if delegation.status in ['active', 'planning']:
                    managers_dict[delegation.assigned_to]["active_delegations"] += 1

        managers = list(managers_dict.values())

        return {
            "success": True,
            "managers": managers,
            "total": len(managers)
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch managers: {str(e)}")


@router.get("/sms/status")
async def get_sms_status():
    """Check if Twilio SMS is configured and available"""
    return {
        "enabled": TWILIO_ENABLED,
        "configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "phone_number": TWILIO_PHONE_NUMBER if TWILIO_ENABLED else None,
        "message": "Twilio SMS is ready" if TWILIO_ENABLED else "Twilio credentials not configured"
    }


@router.post("/sms/send")
async def send_sms(request: SendSMSRequest):
    """Send SMS message to a manager"""
    if not TWILIO_ENABLED:
        raise HTTPException(
            400,
            "Twilio is not configured. Please add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to your .env file"
        )

    try:
        # Validate phone number
        if not request.phone_number:
            raise HTTPException(400, "Phone number is required")

        # Send SMS via Twilio
        message = twilio_client.messages.create(
            body=request.message,
            from_=TWILIO_PHONE_NUMBER,
            to=request.phone_number
        )

        return {
            "success": True,
            "message_sid": message.sid,
            "status": message.status,
            "to": request.phone_number,
            "message": "SMS sent successfully"
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to send SMS: {str(e)}")


@router.post("/sms/send-bulk")
async def send_bulk_sms(manager_ids: List[str], message: str, db: Session = Depends(get_db)):
    """Send SMS to multiple managers"""
    if not TWILIO_ENABLED:
        raise HTTPException(
            400,
            "Twilio is not configured. Please add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER to your .env file"
        )

    results = []
    errors = []

    try:
        # Get delegations for the manager IDs
        delegations = db.query(DelegationModel).filter(
            DelegationModel.id.in_(manager_ids)
        ).all()

        for delegation in delegations:
            phone = getattr(delegation, 'assigned_to_phone', None)
            if not phone:
                errors.append({
                    "manager": delegation.assigned_to,
                    "error": "No phone number on file"
                })
                continue

            try:
                msg = twilio_client.messages.create(
                    body=message,
                    from_=TWILIO_PHONE_NUMBER,
                    to=phone
                )
                results.append({
                    "manager": delegation.assigned_to,
                    "phone": phone,
                    "status": "sent",
                    "message_sid": msg.sid
                })
            except Exception as e:
                errors.append({
                    "manager": delegation.assigned_to,
                    "error": str(e)
                })

        return {
            "success": True,
            "sent": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to send bulk SMS: {str(e)}")
