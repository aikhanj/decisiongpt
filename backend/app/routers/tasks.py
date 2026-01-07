"""Tasks router for background task management."""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_openai_api_key
from app.services.task_service import TaskService
from app.services.decision_service import DecisionService
from app.models.background_task import TaskStatus, TaskType
from app.schemas.tasks import (
    BackgroundTaskResponse,
    TaskStatusResponse,
    PendingTasksResponse,
)
from app.schemas.canvas import ChatRequest, ChatResponse, CanvasState, Option, CommitPlan, ChatMessage
from app.tasks.chat_tasks import process_chat_message_task


router = APIRouter(tags=["tasks"])


@router.post(
    "/decisions/{decision_id}/nodes/{node_id}/chat/async",
    response_model=BackgroundTaskResponse,
)
async def submit_async_chat(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_openai_api_key),
):
    """Submit a chat message for background processing.

    Returns immediately with a task ID that can be polled for status.
    """
    decision_service = DecisionService(db)
    task_service = TaskService(db)

    # Verify decision and node exist
    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Create background task record
    task = await task_service.create_task(
        task_type=TaskType.CHAT_MESSAGE,
        decision_id=decision_id,
        node_id=node_id,
        input_data={"message": request.message},
    )

    # Add user message to chat immediately (optimistic update)
    chat_messages = node.chat_messages_json or []
    user_msg = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    chat_messages.append(user_msg)
    node.chat_messages_json = chat_messages

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(node, "chat_messages_json")
    await db.commit()

    # Queue Celery task
    celery_task = process_chat_message_task.delay(
        background_task_id=str(task.id),
        decision_id=str(decision_id),
        node_id=str(node_id),
        user_message=request.message,
        api_key=api_key,
    )

    # Update task with Celery task ID
    await task_service.update_task_celery_id(task.id, celery_task.id)

    return BackgroundTaskResponse(
        id=task.id,
        task_type=TaskType.CHAT_MESSAGE,
        status=TaskStatus.PENDING,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )


@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a background task.

    Poll this endpoint to check if a task is complete.
    """
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Parse result if completed
    result = None
    if task.status == TaskStatus.COMPLETED.value and task.result_data:
        try:
            # Reconstruct ChatResponse from stored result
            result_data = task.result_data
            result = ChatResponse(
                message=ChatMessage(**result_data["message"]),
                canvas_state=CanvasState(**result_data.get("canvas_state", {})),
                phase=result_data.get("phase", "clarify"),
                questions=result_data.get("questions"),
                options=[Option(**o) for o in result_data.get("options", [])] if result_data.get("options") else None,
                commit_plan=CommitPlan(**result_data["commit_plan"]) if result_data.get("commit_plan") else None,
                advisor=result_data.get("advisor"),
            )
        except Exception:
            # If parsing fails, return raw data
            pass

    return TaskStatusResponse(
        id=task.id,
        status=TaskStatus(task.status),
        result=result,
        error=task.error_message,
        retry_count=task.retry_count,
    )


@router.get(
    "/decisions/{decision_id}/nodes/{node_id}/pending-tasks",
    response_model=PendingTasksResponse,
)
async def get_pending_tasks(
    decision_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all pending/processing tasks for a node.

    Used to restore polling state when user returns to a page.
    """
    decision_service = DecisionService(db)
    task_service = TaskService(db)

    # Verify decision and node exist
    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    node = await decision_service.get_node(node_id)
    if not node or node.decision_id != decision_id:
        raise HTTPException(status_code=404, detail="Node not found")

    # Get pending tasks
    tasks = await task_service.get_pending_tasks_for_node(node_id)

    return PendingTasksResponse(
        tasks=[
            BackgroundTaskResponse(
                id=t.id,
                task_type=TaskType(t.task_type),
                status=TaskStatus(t.status),
                created_at=t.created_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
            )
            for t in tasks
        ]
    )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending task.

    Only pending tasks can be cancelled. Processing tasks will complete.
    """
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.PENDING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status: {task.status}"
        )

    # Mark as failed (cancelled)
    await task_service.update_task_status(
        task_id=task_id,
        status=TaskStatus.FAILED,
        error_message="Cancelled by user",
    )

    # Revoke Celery task if it exists
    if task.celery_task_id:
        from app.celery_app import celery_app
        celery_app.control.revoke(task.celery_task_id, terminate=False)

    return {"status": "cancelled", "task_id": str(task_id)}
