from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from database import get_db
from models import Task as TaskModel
import uuid

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"  # low, medium, high, urgent
    source: str = "manual"  # manual, email, ai_suggested, delegated
    source_id: Optional[str] = None
    eisenhower_quadrant: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None  # todo, in_progress, completed, cancelled
    eisenhower_quadrant: Optional[str] = None

def task_to_dict(task: TaskModel):
    """Convert SQLAlchemy model to dict for API response"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "priority": task.priority,
        "status": task.status,
        "source": task.source,
        "source_id": task.source_id,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "gcal_event_id": task.gcal_event_id,
        "eisenhower_quadrant": task.eisenhower_quadrant,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }

@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tasks with optional filters"""
    try:
        query = db.query(TaskModel)
        
        if status:
            query = query.filter(TaskModel.status == status)
        if priority:
            query = query.filter(TaskModel.priority == priority)
        if source:
            query = query.filter(TaskModel.source == source)
        
        # Order by: incomplete first, then by due date, then by priority
        tasks = query.order_by(
            TaskModel.status != 'completed',
            TaskModel.due_date.asc().nullslast(),
            TaskModel.created_at.desc()
        ).all()
        
        return {
            "tasks": [task_to_dict(t) for t in tasks],
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tasks/{task_id}")
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        
        return task_to_dict(task)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tasks")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task"""
    try:
        # Parse due date if provided
        due_date_obj = None
        if task.due_date:
            try:
                due_date_obj = datetime.fromisoformat(task.due_date.replace('Z', '')).date()
            except:
                # Try parsing as date only
                due_date_obj = datetime.strptime(task.due_date, '%Y-%m-%d').date()
        
        # Create new task
        new_task = TaskModel(
            id=str(uuid.uuid4()),
            title=task.title,
            description=task.description,
            due_date=due_date_obj,
            priority=task.priority,
            status='todo',
            source=task.source,
            source_id=task.source_id,
            eisenhower_quadrant=task.eisenhower_quadrant,
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        return {
            "success": True,
            "task": task_to_dict(new_task)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate, db: Session = Depends(get_db)):
    """Update an existing task"""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        
        # Update fields
        if updates.title is not None:
            task.title = updates.title
        if updates.description is not None:
            task.description = updates.description
        if updates.due_date is not None:
            try:
                task.due_date = datetime.fromisoformat(updates.due_date.replace('Z', '')).date()
            except:
                task.due_date = datetime.strptime(updates.due_date, '%Y-%m-%d').date()
        if updates.priority is not None:
            task.priority = updates.priority
        if updates.status is not None:
            task.status = updates.status
            # Set completed_at if status changed to completed
            if updates.status == 'completed' and not task.completed_at:
                task.completed_at = datetime.utcnow()
        if updates.eisenhower_quadrant is not None:
            task.eisenhower_quadrant = updates.eisenhower_quadrant
        
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        return {
            "success": True,
            "task": task_to_dict(task)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, db: Session = Depends(get_db)):
    """Mark a task as completed"""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        
        task.status = 'completed'
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(task)
        
        return {
            "success": True,
            "task": task_to_dict(task)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """Delete a task"""
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        
        db.delete(task)
        db.commit()
        
        return {
            "success": True,
            "message": f"Task {task_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, str(e))

@router.get("/tasks/stats/summary")
async def get_task_stats(db: Session = Depends(get_db)):
    """Get summary statistics for tasks"""
    try:
        total = db.query(TaskModel).count()
        todo = db.query(TaskModel).filter(TaskModel.status == 'todo').count()
        in_progress = db.query(TaskModel).filter(TaskModel.status == 'in_progress').count()
        completed = db.query(TaskModel).filter(TaskModel.status == 'completed').count()
        
        # Count overdue tasks
        today = date.today()
        overdue = db.query(TaskModel).filter(
            TaskModel.status != 'completed',
            TaskModel.status != 'cancelled',
            TaskModel.due_date < today
        ).count()
        
        return {
            "total": total,
            "todo": todo,
            "in_progress": in_progress,
            "completed": completed,
            "overdue": overdue
        }
    except Exception as e:
        raise HTTPException(500, str(e))
