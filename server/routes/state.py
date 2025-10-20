from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from services.state_manager import state_manager
import json

router = APIRouter()

class AcknowledgeEmailRequest(BaseModel):
    thread_id: str

class AddTaskRequest(BaseModel):
    action: str
    due_date: Optional[str] = None
    time_estimate: Optional[str] = None
    priority: Optional[str] = "normal"
    thread_id: Optional[str] = None

class AddTasksBulkRequest(BaseModel):
    tasks: List[dict]
    thread_id: Optional[str] = None

class ToggleTaskRequest(BaseModel):
    task_id: str

class UpdateTaskRequest(BaseModel):
    task_id: str
    updates: dict

class DeleteTaskRequest(BaseModel):
    task_id: str

@router.post("/acknowledge")
async def acknowledge_email(req: AcknowledgeEmailRequest):
    try:
        state = state_manager.acknowledge_email(req.thread_id)
        return {"success": True, "state": state}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/email/{thread_id}")
async def get_email_state(thread_id: str):
    try:
        state = state_manager.get_email_state(thread_id)
        return state
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/emails")
async def get_all_email_states():
    try:
        states = state_manager.get_all_email_states()
        return states
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tasks/add")
async def add_task(req: AddTaskRequest):
    try:
        task_dict = {
            'action': req.action,
            'due_date': req.due_date,
            'time_estimate': req.time_estimate,
            'priority': req.priority
        }
        task = state_manager.add_task(task_dict, req.thread_id)
        return {"success": True, "task": task}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tasks/add-bulk")
async def add_tasks_bulk(req: AddTasksBulkRequest):
    try:
        tasks = state_manager.add_tasks_bulk(req.tasks, req.thread_id)
        return {"success": True, "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tasks")
async def get_tasks(completed: Optional[bool] = None):
    try:
        tasks = state_manager.get_tasks(filter_completed=completed)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    try:
        task = state_manager.get_task(task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tasks/toggle")
async def toggle_task(request: Request):
    try:
        # Log the raw body for debugging
        body = await request.body()
        print(f"Toggle task - Raw body: {body.decode()}")
        
        try:
            data = json.loads(body)
            print(f"Toggle task - Parsed data: {data}")
        except:
            raise HTTPException(400, "Invalid JSON")
        
        req = ToggleTaskRequest(**data)
        task = state_manager.toggle_task(req.task_id)
        if not task:
            raise HTTPException(404, f"Task {req.task_id} not found")
        return {"success": True, "task": task}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Toggle task error: {str(e)}")
        raise HTTPException(500, str(e))

@router.post("/tasks/update")
async def update_task(req: UpdateTaskRequest):
    try:
        task = state_manager.update_task(req.task_id, req.updates)
        if not task:
            raise HTTPException(404, f"Task {req.task_id} not found")
        return {"success": True, "task": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/tasks/delete")
async def delete_task(request: Request):
    try:
        # Log the raw body for debugging
        body = await request.body()
        print(f"Delete task - Raw body: {body.decode()}")
        
        try:
            data = json.loads(body)
            print(f"Delete task - Parsed data: {data}")
        except:
            raise HTTPException(400, "Invalid JSON")
        
        req = DeleteTaskRequest(**data)
        success = state_manager.delete_task(req.task_id)
        if not success:
            raise HTTPException(404, f"Task {req.task_id} not found")
        return {"success": True, "message": f"Task {req.task_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete task error: {str(e)}")
        raise HTTPException(500, str(e))
