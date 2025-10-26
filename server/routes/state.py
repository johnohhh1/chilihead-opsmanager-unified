from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from services.state_manager import state_manager
import json
import os
import httpx

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

@router.post("/tasks/{task_id}/sync-to-google-tasks")
async def sync_task_to_google_tasks(task_id: str):
    """Sync a task from state manager to Google Tasks"""
    try:
        from services.google_tasks import create_google_task

        # Get task from state manager
        task = state_manager.get_task(task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")

        # Check if already synced
        if task.get('google_task_id'):
            return {
                "success": False,
                "error": "Task is already synced to Google Tasks",
                "google_task_id": task['google_task_id']
            }

        # Prepare task data for Google Tasks
        description = task.get('description', '')
        if task.get('priority'):
            priority_text = f"Priority: {task['priority'].upper()}"
            description = f"{priority_text}\n\n{description}" if description else priority_text

        # Create Google Task
        result = create_google_task(
            title=task['action'],
            description=description,
            due_date=task.get('due_date'),
            priority=task.get('priority', 'normal')
        )

        if not result.get('success'):
            # Check if it needs re-authentication
            error_message = result.get('error', 'Failed to create Google Task')
            if result.get('needs_reauth') or 'permission' in error_message.lower() or 'authentication' in error_message.lower():
                raise HTTPException(401, error_message)
            raise HTTPException(500, error_message)

        # Update task in state manager with Google Task ID
        updated_task = state_manager.update_task(task_id, {'google_task_id': result['task_id']})

        return {
            "success": True,
            "task": updated_task,
            "google_task_id": result['task_id'],
            "message": "Task synced to Google Tasks successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        # Check if it's an authentication error
        error_str = str(e).lower()
        if "not authenticated" in error_str or "invalid credentials" in error_str:
            raise HTTPException(401, "Google authentication required. Please re-authenticate with Google to enable Tasks sync.")
        raise HTTPException(500, str(e))

@router.post("/tasks/{task_id}/push-to-team")
async def push_task_to_team_board(task_id: str):
    """Push a task from local system to the team board (Vercel)"""
    try:
        # Get task from state manager
        task = state_manager.get_task(task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")

        # Get team board configuration from environment
        team_board_url = os.getenv("TEAM_BOARD_URL")
        team_board_api_key = os.getenv("TEAM_BOARD_API_KEY")

        if not team_board_url or not team_board_api_key:
            raise HTTPException(500, "Team board not configured. Please set TEAM_BOARD_URL and TEAM_BOARD_API_KEY in .env")

        # Prepare task payload for team board
        payload = {
            "id": task_id,
            "title": task['action'],
            "description": task.get('description', ''),
            "priority": task.get('priority', 'normal'),
            "due_date": task.get('due_date'),
            "assigned_to": task.get('assigned_to', ''),
            "status": "todo",
            "pushed_by": "ChiliHead OpsManager"
        }

        # Push to team board
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.post(
                f"{team_board_url}/api/tasks",
                headers={
                    "x-api-key": team_board_api_key,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                raise HTTPException(
                    500,
                    f"Failed to push to team board: {error_data.get('error', response.text)}"
                )

            result = response.json()

        return {
            "success": True,
            "message": "Task pushed to team board successfully",
            "task": result.get('task')
        }

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            raise HTTPException(503, "Could not connect to team board. Make sure it's running.")
        raise HTTPException(500, str(e))

@router.post("/tasks/sync-from-team")
async def sync_status_from_team_board():
    """Sync task status updates from team board back to local system"""
    try:
        # Get team board configuration
        team_board_url = os.getenv("TEAM_BOARD_URL")
        team_board_api_key = os.getenv("TEAM_BOARD_API_KEY")

        if not team_board_url or not team_board_api_key:
            raise HTTPException(500, "Team board not configured. Please set TEAM_BOARD_URL and TEAM_BOARD_API_KEY in .env")

        # Fetch all tasks from team board
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(f"{team_board_url}/api/tasks")

            if response.status_code != 200:
                raise HTTPException(500, f"Failed to fetch from team board: {response.text}")

            team_data = response.json()
            team_tasks = team_data.get('tasks', [])

        # Get all local tasks
        local_tasks = state_manager.get_tasks()

        # Track updates
        updated_count = 0
        updated_tasks = []

        # Update local tasks with team board status
        for team_task in team_tasks:
            task_id = team_task.get('id')
            team_status = team_task.get('status')

            # Find matching local task
            local_task = next((t for t in local_tasks if t['id'] == task_id), None)

            if local_task and local_task.get('status') != team_status:
                # Map team board status to local status
                status_map = {
                    'todo': 'pending',
                    'in_progress': 'in_progress',
                    'completed': 'completed'
                }
                new_status = status_map.get(team_status, team_status)

                # Update the task
                local_task['status'] = new_status
                state_manager.update_task(task_id, local_task)

                updated_count += 1
                updated_tasks.append({
                    'id': task_id,
                    'title': local_task['action'],
                    'old_status': local_task.get('status'),
                    'new_status': new_status
                })

        return {
            "success": True,
            "message": f"Synced {updated_count} task status update(s) from team board",
            "updated_count": updated_count,
            "updated_tasks": updated_tasks
        }

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "connection" in error_str or "timeout" in error_str:
            raise HTTPException(503, "Could not connect to team board. Make sure it's running.")
        raise HTTPException(500, str(e))
