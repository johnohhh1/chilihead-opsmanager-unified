from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db
from models import EmailState as EmailStateModel
import uuid

router = APIRouter()

class EmailStateCreate(BaseModel):
    email_id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    received_at: Optional[str] = None
    ai_analysis: Optional[dict] = None

class EmailAcknowledge(BaseModel):
    email_id: str

def email_state_to_dict(email: EmailStateModel):
    """Convert SQLAlchemy model to dict for API response"""
    return {
        "id": email.id,
        "email_id": email.email_id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "sender": email.sender,
        "received_at": email.received_at.isoformat() if email.received_at else None,
        "first_seen_at": email.first_seen_at.isoformat() if email.first_seen_at else None,
        "last_viewed_at": email.last_viewed_at.isoformat() if email.last_viewed_at else None,
        "is_acknowledged": email.is_acknowledged,
        "acknowledged_at": email.acknowledged_at.isoformat() if email.acknowledged_at else None,
        "ai_analysis": email.ai_analysis,
        "created_at": email.created_at.isoformat() if email.created_at else None,
        "updated_at": email.updated_at.isoformat() if email.updated_at else None,
    }

@router.post("/email/track")
async def track_email_view(email_data: EmailStateCreate, db: Session = Depends(get_db)):
    """Track that an email was viewed"""
    try:
        # Check if email already exists
        email = db.query(EmailStateModel).filter(EmailStateModel.email_id == email_data.email_id).first()
        
        if email:
            # Update last_viewed_at
            email.last_viewed_at = datetime.utcnow()
            email.updated_at = datetime.utcnow()
        else:
            # Create new email state
            received_at_obj = None
            if email_data.received_at:
                try:
                    received_at_obj = datetime.fromisoformat(email_data.received_at.replace('Z', ''))
                except:
                    pass
            
            email = EmailStateModel(
                id=str(uuid.uuid4()),
                email_id=email_data.email_id,
                thread_id=email_data.thread_id,
                subject=email_data.subject,
                sender=email_data.sender,
                received_at=received_at_obj,
                first_seen_at=datetime.utcnow(),
                last_viewed_at=datetime.utcnow(),
                ai_analysis=email_data.ai_analysis,
            )
            db.add(email)
        
        db.commit()
        db.refresh(email)
        
        return {
            "success": True,
            "email_state": email_state_to_dict(email)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.post("/email/acknowledge")
async def acknowledge_email(ack_data: EmailAcknowledge, db: Session = Depends(get_db)):
    """Mark an email as acknowledged"""
    try:
        email = db.query(EmailStateModel).filter(EmailStateModel.email_id == ack_data.email_id).first()
        
        if not email:
            # Create if doesn't exist
            email = EmailStateModel(
                id=str(uuid.uuid4()),
                email_id=ack_data.email_id,
                first_seen_at=datetime.utcnow(),
                last_viewed_at=datetime.utcnow(),
            )
            db.add(email)
        
        email.is_acknowledged = True
        email.acknowledged_at = datetime.utcnow()
        email.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(email)
        
        return {
            "success": True,
            "message": "Email acknowledged",
            "email_state": email_state_to_dict(email)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.get("/email/{email_id}/state")
async def get_email_state(email_id: str, db: Session = Depends(get_db)):
    """Get the state of a specific email"""
    try:
        email = db.query(EmailStateModel).filter(EmailStateModel.email_id == email_id).first()
        
        if not email:
            return {
                "exists": False,
                "is_new": True,
                "is_acknowledged": False
            }
        
        return {
            "exists": True,
            "is_new": email.first_seen_at is None,
            "is_acknowledged": email.is_acknowledged,
            "email_state": email_state_to_dict(email)
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/email/unacknowledged")
async def get_unacknowledged_emails(db: Session = Depends(get_db)):
    """Get all unacknowledged emails"""
    try:
        emails = db.query(EmailStateModel).filter(
            EmailStateModel.is_acknowledged == False
        ).order_by(EmailStateModel.received_at.desc()).all()
        
        return {
            "emails": [email_state_to_dict(e) for e in emails],
            "count": len(emails)
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/email/stats")
async def get_email_stats(db: Session = Depends(get_db)):
    """Get statistics about email states"""
    try:
        total = db.query(EmailStateModel).count()
        acknowledged = db.query(EmailStateModel).filter(EmailStateModel.is_acknowledged == True).count()
        unacknowledged = total - acknowledged
        
        return {
            "total": total,
            "acknowledged": acknowledged,
            "unacknowledged": unacknowledged
        }
    except Exception as e:
        raise HTTPException(500, str(e))
