from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from database import get_db
from models import Delegation as DelegationModel
import uuid

router = APIRouter()

class ChiliHeadProgress(BaseModel):
    completed: bool
    notes: str

class ChiliHeadProgressFull(BaseModel):
    senseOfBelonging: ChiliHeadProgress
    clearDirection: ChiliHeadProgress
    preparation: ChiliHeadProgress
    support: ChiliHeadProgress
    accountability: ChiliHeadProgress

class Delegation(BaseModel):
    taskDescription: str
    assignedTo: str
    assignedToEmail: Optional[str] = None  # NEW: For email notifications
    assignedToPhone: Optional[str] = None  # NEW: For SMS notifications
    dueDate: Optional[str] = None
    followUpDate: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    status: str = "planning"  # planning, active, completed, on-hold
    chiliheadProgress: ChiliHeadProgressFull

class DelegationUpdate(BaseModel):
    taskDescription: Optional[str] = None
    assignedTo: Optional[str] = None
    assignedToEmail: Optional[str] = None
    assignedToPhone: Optional[str] = None  # NEW: For SMS notifications
    dueDate: Optional[str] = None
    followUpDate: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    chiliheadProgress: Optional[ChiliHeadProgressFull] = None

def delegation_to_dict(delegation: DelegationModel):
    """Convert SQLAlchemy model to dict for API response"""
    return {
        "id": delegation.id,
        "task_description": delegation.task_description,
        "assigned_to": delegation.assigned_to,
        "assigned_to_email": delegation.assigned_to_email,
        "assigned_to_phone": getattr(delegation, 'assigned_to_phone', None),
        "due_date": delegation.due_date.isoformat() if delegation.due_date else None,
        "follow_up_date": delegation.follow_up_date.isoformat() if delegation.follow_up_date else None,
        "priority": delegation.priority,
        "status": delegation.status,
        "chilihead_progress": delegation.chilihead_progress,
        "notification_sent": delegation.notification_sent,
        "notification_sent_at": delegation.notification_sent_at.isoformat() if delegation.notification_sent_at else None,
        "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
        "updated_at": delegation.updated_at.isoformat() if delegation.updated_at else None,
    }

@router.get("/delegations")
async def get_delegations(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all delegations, optionally filtered by status"""
    try:
        query = db.query(DelegationModel)
        
        if status:
            query = query.filter(DelegationModel.status == status)
        
        delegations = query.order_by(DelegationModel.created_at.desc()).all()
        
        return {
            "delegations": [delegation_to_dict(d) for d in delegations],
            "count": len(delegations)
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/delegations/{delegation_id}")
async def get_delegation(delegation_id: str, db: Session = Depends(get_db)):
    """Get a specific delegation by ID"""
    try:
        delegation = db.query(DelegationModel).filter(DelegationModel.id == delegation_id).first()
        
        if not delegation:
            raise HTTPException(404, f"Delegation {delegation_id} not found")
        
        return delegation_to_dict(delegation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/delegations")
async def create_delegation(delegation: Delegation, db: Session = Depends(get_db)):
    """Create a new delegation"""
    try:
        # Parse dates if provided
        due_date_obj = None
        if delegation.dueDate:
            due_date_obj = datetime.fromisoformat(delegation.dueDate.replace('Z', '')).date()
        
        follow_up_date_obj = None
        if delegation.followUpDate:
            follow_up_date_obj = datetime.fromisoformat(delegation.followUpDate.replace('Z', '')).date()
        
        # Create new delegation
        new_delegation = DelegationModel(
            id=str(uuid.uuid4()),
            task_description=delegation.taskDescription,
            assigned_to=delegation.assignedTo,
            assigned_to_email=delegation.assignedToEmail,
            assigned_to_phone=delegation.assignedToPhone,
            due_date=due_date_obj,
            follow_up_date=follow_up_date_obj,
            priority=delegation.priority,
            status=delegation.status,
            chilihead_progress=delegation.chiliheadProgress.dict(),
        )
        
        db.add(new_delegation)
        db.commit()
        db.refresh(new_delegation)
        
        return {
            "success": True,
            "delegation": delegation_to_dict(new_delegation)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.put("/delegations/{delegation_id}")
async def update_delegation(delegation_id: str, updates: DelegationUpdate, db: Session = Depends(get_db)):
    """Update an existing delegation"""
    try:
        delegation = db.query(DelegationModel).filter(DelegationModel.id == delegation_id).first()
        
        if not delegation:
            raise HTTPException(404, f"Delegation {delegation_id} not found")
        
        # Update fields
        if updates.taskDescription is not None:
            delegation.task_description = updates.taskDescription
        if updates.assignedTo is not None:
            delegation.assigned_to = updates.assignedTo
        if updates.assignedToEmail is not None:
            delegation.assigned_to_email = updates.assignedToEmail
        if updates.assignedToPhone is not None:
            delegation.assigned_to_phone = updates.assignedToPhone
        if updates.dueDate is not None:
            delegation.due_date = datetime.fromisoformat(updates.dueDate.replace('Z', '')).date()
        if updates.followUpDate is not None:
            delegation.follow_up_date = datetime.fromisoformat(updates.followUpDate.replace('Z', '')).date()
        if updates.priority is not None:
            delegation.priority = updates.priority
        if updates.status is not None:
            delegation.status = updates.status
        if updates.chiliheadProgress is not None:
            delegation.chilihead_progress = updates.chiliheadProgress.dict()
        
        delegation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(delegation)
        
        return {
            "success": True,
            "delegation": delegation_to_dict(delegation)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.delete("/delegations/{delegation_id}")
async def delete_delegation(delegation_id: str, db: Session = Depends(get_db)):
    """Delete a delegation"""
    try:
        delegation = db.query(DelegationModel).filter(DelegationModel.id == delegation_id).first()
        
        if not delegation:
            raise HTTPException(404, f"Delegation {delegation_id} not found")
        
        db.delete(delegation)
        db.commit()
        
        return {
            "success": True,
            "message": f"Delegation {delegation_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))
