"""
Gmail Add-on Backend API Integration
Provides endpoints for the enhanced Gmail Add-on to integrate with ChiliHead OpsManager
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import pytz
from sqlalchemy.orm import Session

from database import get_db
from services.email_service import EmailAnalysisService
from services.task_service import TaskManagementService
from services.memory_service import MemoryService
from services.delegation_service import DelegationTrackingService
from services.ai_service import AIService
from auth import verify_api_token

router = APIRouter(prefix="/api/backend/addon", tags=["gmail-addon"])

# ============= MODELS =============

class EmailAnalysisRequest(BaseModel):
    """Request model for email analysis"""
    email_id: str
    subject: str
    from_address: str
    to_address: str
    body: str
    html_body: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []
    thread_id: Optional[str] = None
    thread_length: Optional[int] = 1
    labels: Optional[List[str]] = []
    date: datetime
    include_memory: bool = True

class TaskCreateRequest(BaseModel):
    """Request model for task creation"""
    title: str
    description: Optional[str] = None
    category: str  # URGENT_IMPORTANT, NOT_URGENT_IMPORTANT, etc.
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    source: str = "gmail_addon"
    email_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

class DelegationRequest(BaseModel):
    """Request model for delegation tracking"""
    task: str
    assignee: str
    pillar: str  # Leadership, Operations, Guest Experience, etc.
    deadline: str
    context: Optional[str] = None
    expected_outcome: Optional[str] = None
    development_goal: Optional[str] = None
    notify: bool = True

class MemoryStoreRequest(BaseModel):
    """Request model for memory storage"""
    type: str  # email_context, task, delegation, metric, etc.
    key: Optional[str] = None
    data: Dict[str, Any]
    ttl: Optional[int] = 86400  # 24 hours default
    tags: Optional[List[str]] = []

class MemoryRetrieveRequest(BaseModel):
    """Request model for memory retrieval"""
    key: Optional[str] = None
    type: Optional[str] = None
    related_to: Optional[str] = None
    tags: Optional[List[str]] = []
    limit: Optional[int] = 10

class ChatRequest(BaseModel):
    """Request model for chat/instruction processing"""
    prompt: str
    context: Optional[str] = None
    include_memory: bool = True
    tools_enabled: bool = True

class MetricTrackRequest(BaseModel):
    """Request model for metric tracking"""
    metrics: Dict[str, Any]
    date: Optional[datetime] = None
    source: str = "gmail_addon"
    context: Optional[Dict[str, Any]] = {}

# ============= ENDPOINTS =============

@router.post("/analyze-email")
async def analyze_email(
    request: EmailAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Analyze email with AI and return structured insights
    """
    try:
        # Initialize services
        email_service = EmailAnalysisService(db)
        memory_service = MemoryService(db)
        ai_service = AIService()

        # Get memory context if requested
        context = {}
        if request.include_memory:
            context = memory_service.get_context(
                related_to=request.from_address,
                limit=5
            )

        # Analyze email with AI
        analysis = await email_service.analyze_email(
            email_data={
                "id": request.email_id,
                "subject": request.subject,
                "from": request.from_address,
                "to": request.to_address,
                "body": request.body,
                "html_body": request.html_body,
                "attachments": request.attachments,
                "thread_id": request.thread_id,
                "date": request.date.isoformat(),
                "labels": request.labels
            },
            context=context
        )

        # Extract metrics if found
        metrics = email_service.extract_metrics(analysis)
        if metrics:
            background_tasks.add_task(
                track_metrics_background,
                metrics=metrics,
                source=f"email_{request.email_id}",
                db=db
            )

        # Store in memory for context
        memory_service.store(
            type="email_analysis",
            key=f"email_{request.email_id}",
            data={
                "email": request.dict(),
                "analysis": analysis,
                "metrics": metrics
            },
            ttl=86400  # 24 hours
        )

        return {
            "success": True,
            "data": {
                "analysis": analysis,
                "metrics": metrics,
                "priority": email_service.calculate_priority(request.dict()),
                "suggested_tools": email_service.suggest_tools(analysis)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-task")
async def create_task(
    request: TaskCreateRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Create task with Eisenhower Matrix categorization
    """
    try:
        task_service = TaskManagementService(db)
        memory_service = MemoryService(db)

        # Create task
        task = task_service.create_task(
            title=request.title,
            description=request.description,
            category=request.category,
            assignee=request.assignee,
            due_date=request.due_date,
            source=request.source,
            context=request.context
        )

        # Store in memory
        memory_service.store(
            type="task_created",
            key=f"task_{task['id']}",
            data={
                "task": task,
                "source": request.source,
                "email_id": request.email_id
            }
        )

        # If assigned, create delegation record
        if request.assignee:
            delegation_service = DelegationTrackingService(db)
            delegation = delegation_service.track_delegation(
                task_id=task['id'],
                task_title=request.title,
                assignee=request.assignee,
                category="task_assignment"
            )

        return {
            "success": True,
            "data": task,
            "message": f"Task created in {request.category}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-delegation")
async def track_delegation(
    request: DelegationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Track delegation for team development
    """
    try:
        delegation_service = DelegationTrackingService(db)
        memory_service = MemoryService(db)

        # Create delegation record
        delegation = delegation_service.create_delegation(
            task=request.task,
            assignee=request.assignee,
            pillar=request.pillar,
            deadline=request.deadline,
            context=request.context,
            expected_outcome=request.expected_outcome,
            development_goal=request.development_goal
        )

        # Store in memory
        memory_service.store(
            type="delegation",
            key=f"delegation_{delegation['id']}",
            data=delegation,
            tags=[request.assignee, request.pillar]
        )

        # Send notification if requested
        if request.notify:
            background_tasks.add_task(
                send_delegation_notification,
                assignee=request.assignee,
                task=request.task,
                deadline=request.deadline,
                db=db
            )

        return {
            "success": True,
            "data": delegation,
            "message": f"Delegated to {request.assignee} - {request.pillar} development"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/store")
async def store_memory(
    request: MemoryStoreRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Store data in persistent memory
    """
    try:
        memory_service = MemoryService(db)

        result = memory_service.store(
            type=request.type,
            key=request.key,
            data=request.data,
            ttl=request.ttl,
            tags=request.tags
        )

        return {
            "success": True,
            "data": result,
            "message": "Memory stored successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/retrieve")
async def retrieve_memory(
    request: MemoryRetrieveRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Retrieve data from memory based on query
    """
    try:
        memory_service = MemoryService(db)

        # Retrieve by key if provided
        if request.key:
            result = memory_service.get(request.key)
            return {
                "success": True,
                "data": result if result else None
            }

        # Complex query
        results = memory_service.search(
            type=request.type,
            related_to=request.related_to,
            tags=request.tags,
            limit=request.limit
        )

        return {
            "success": True,
            "data": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def process_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Process chat/instruction with AI
    """
    try:
        ai_service = AIService()
        memory_service = MemoryService(db)

        # Get memory context if requested
        context = {}
        if request.include_memory:
            context = memory_service.get_recent_context(limit=10)

        # Process with AI
        response = await ai_service.process_instruction(
            prompt=request.prompt,
            context={
                "provided": request.context,
                "memory": context
            },
            tools_enabled=request.tools_enabled
        )

        # Execute tools if identified
        tool_results = []
        if request.tools_enabled and response.get("tools"):
            for tool in response["tools"]:
                result = await execute_tool(tool, db)
                tool_results.append(result)

        # Store conversation in memory
        memory_service.store(
            type="chat_interaction",
            data={
                "prompt": request.prompt,
                "response": response,
                "tool_results": tool_results,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "success": True,
            "data": {
                "response": response.get("text", ""),
                "tools_executed": tool_results,
                "structured_data": response.get("structured", {})
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-metrics")
async def track_metrics(
    request: MetricTrackRequest,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Track operational metrics
    """
    try:
        memory_service = MemoryService(db)

        # Store each metric
        stored_metrics = []
        for metric_name, value in request.metrics.items():
            result = memory_service.store(
                type="metric",
                key=f"metric_{metric_name}_{datetime.utcnow().strftime('%Y%m%d')}",
                data={
                    "metric": metric_name,
                    "value": value,
                    "date": request.date.isoformat() if request.date else datetime.utcnow().isoformat(),
                    "source": request.source,
                    "context": request.context
                },
                tags=["metric", metric_name]
            )
            stored_metrics.append(result)

        return {
            "success": True,
            "data": stored_metrics,
            "message": f"Tracked {len(stored_metrics)} metrics"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily-brief")
async def get_daily_brief(
    timezone: str = "America/New_York",
    include_metrics: bool = True,
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Generate comprehensive daily brief
    """
    try:
        memory_service = MemoryService(db)
        ai_service = AIService()

        # Get timezone
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Gather data for brief
        brief_data = {
            "date": now.strftime("%A, %B %d, %Y"),
            "time": now.strftime("%I:%M %p %Z"),
            "emails": memory_service.search(
                type="email_analysis",
                since=start_of_day - timedelta(days=1),
                limit=20
            ),
            "tasks": memory_service.search(
                type="task_created",
                since=start_of_day - timedelta(days=1),
                limit=20
            ),
            "delegations": memory_service.search(
                type="delegation",
                since=start_of_day - timedelta(days=1),
                limit=10
            )
        }

        # Include metrics if requested
        if include_metrics:
            brief_data["metrics"] = memory_service.search(
                type="metric",
                since=start_of_day - timedelta(days=1),
                limit=50
            )

        # Generate brief with AI
        brief_prompt = f"""Generate a concise operations brief for {brief_data['date']}.

Data:
- {len(brief_data['emails'])} emails analyzed
- {len(brief_data['tasks'])} tasks created
- {len(brief_data['delegations'])} delegations tracked
- {len(brief_data.get('metrics', []))} metrics recorded

Focus on:
1. Priority items requiring immediate attention
2. Key metrics and variances
3. Team development opportunities
4. Operational risks or concerns

Be direct and specific with names, numbers, and actions."""

        brief = await ai_service.generate_brief(brief_prompt, brief_data)

        return {
            "success": True,
            "data": {
                "brief": brief,
                "summary": {
                    "emails": len(brief_data['emails']),
                    "tasks": len(brief_data['tasks']),
                    "delegations": len(brief_data['delegations']),
                    "metrics": len(brief_data.get('metrics', []))
                },
                "generated_at": now.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= BACKGROUND TASKS =============

async def track_metrics_background(metrics: Dict, source: str, db: Session):
    """Background task to track metrics"""
    try:
        memory_service = MemoryService(db)
        for metric_name, value in metrics.items():
            memory_service.store(
                type="metric",
                key=f"metric_{metric_name}_{datetime.utcnow().strftime('%Y%m%d%H')}",
                data={
                    "metric": metric_name,
                    "value": value,
                    "source": source,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        print(f"Error tracking metrics: {e}")

async def send_delegation_notification(assignee: str, task: str, deadline: str, db: Session):
    """Background task to send delegation notifications"""
    try:
        # This would integrate with your notification service
        # For now, just log it
        print(f"Delegation notification: {assignee} assigned '{task}' due {deadline}")
    except Exception as e:
        print(f"Error sending notification: {e}")

async def execute_tool(tool: Dict, db: Session):
    """Execute a tool based on AI decision"""
    try:
        tool_name = tool.get("name")
        params = tool.get("params", {})

        if tool_name == "task_create":
            task_service = TaskManagementService(db)
            return task_service.create_task(**params)

        elif tool_name == "delegation_assign":
            delegation_service = DelegationTrackingService(db)
            return delegation_service.create_delegation(**params)

        elif tool_name == "memory_store":
            memory_service = MemoryService(db)
            return memory_service.store(**params)

        elif tool_name == "metric_track":
            memory_service = MemoryService(db)
            return memory_service.store(
                type="metric",
                data=params,
                tags=["metric"]
            )

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}

# ============= ERROR REPORTING =============

@router.post("/error-report")
async def report_error(
    error: str,
    context: Optional[str] = None,
    source: str = "gmail_addon",
    db: Session = Depends(get_db),
    token: str = Depends(verify_api_token)
):
    """
    Log errors from Gmail Add-on
    """
    try:
        memory_service = MemoryService(db)

        error_record = memory_service.store(
            type="error_report",
            data={
                "error": error,
                "context": context,
                "source": source,
                "timestamp": datetime.utcnow().isoformat()
            },
            tags=["error", source]
        )

        # You could also send notifications here
        print(f"Error reported from {source}: {error}")

        return {
            "success": True,
            "message": "Error logged successfully",
            "id": error_record.get("id")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))