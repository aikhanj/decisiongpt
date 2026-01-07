"""Celery tasks for chat message processing."""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from celery import Task
from sqlalchemy import select

from app.celery_app import celery_app
from app.database_sync import get_sync_db
from app.models.background_task import BackgroundTask, TaskStatus
from app.models.decision_node import DecisionNode


class ChatTask(Task):
    """Base task class with error handling."""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True


def run_async(coro):
    """Run an async coroutine in a sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_chat_message_async(
    node_id: str,
    user_message: str,
    api_key: str,
) -> dict:
    """Async implementation of chat message processing."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    from app.config import get_settings
    from app.services.chat_service import ChatService

    settings = get_settings()

    # Create async engine and session for this task
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # Get the node
        result = await db.execute(
            select(DecisionNode).where(DecisionNode.id == uuid.UUID(node_id))
        )
        node = result.scalar_one_or_none()

        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Process message
        chat_service = ChatService(db, api_key)
        response = await chat_service.send_message(node, user_message)

        # Convert response to dict for serialization
        return response.model_dump(mode="json")

    await engine.dispose()


@celery_app.task(
    bind=True,
    base=ChatTask,
    name="app.tasks.chat_tasks.process_chat_message",
    max_retries=3,
    default_retry_delay=30,
)
def process_chat_message_task(
    self,
    background_task_id: str,
    decision_id: str,
    node_id: str,
    user_message: str,
    api_key: str,
) -> dict[str, Any]:
    """Process a chat message in the background.

    Args:
        background_task_id: Our DB task ID for status tracking
        decision_id: The decision ID
        node_id: The node ID
        user_message: The user's message
        api_key: The OpenAI API key

    Returns:
        dict with the ChatResponse data
    """
    # Update task status to processing
    with get_sync_db() as db:
        task = db.query(BackgroundTask).filter(
            BackgroundTask.id == uuid.UUID(background_task_id)
        ).first()

        if task:
            task.status = TaskStatus.PROCESSING.value
            task.started_at = datetime.utcnow()
            task.celery_task_id = self.request.id
            db.commit()

    try:
        # Run the async chat processing
        result = run_async(
            _process_chat_message_async(node_id, user_message, api_key)
        )

        # Update task as completed
        with get_sync_db() as db:
            task = db.query(BackgroundTask).filter(
                BackgroundTask.id == uuid.UUID(background_task_id)
            ).first()

            if task:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.utcnow()
                task.result_data = result
                db.commit()

        return result

    except Exception as e:
        # Update task as failed
        with get_sync_db() as db:
            task = db.query(BackgroundTask).filter(
                BackgroundTask.id == uuid.UUID(background_task_id)
            ).first()

            if task:
                task.retry_count = (task.retry_count or 0) + 1

                # Check if we should retry
                if self.request.retries < self.max_retries:
                    task.status = TaskStatus.PENDING.value  # Will be retried
                    task.error_message = f"Retry {self.request.retries + 1}: {str(e)}"
                else:
                    task.status = TaskStatus.FAILED.value
                    task.completed_at = datetime.utcnow()
                    task.error_message = str(e)

                db.commit()

        # Re-raise to trigger Celery retry
        raise


@celery_app.task(
    bind=True,
    base=ChatTask,
    name="app.tasks.chat_tasks.process_start_decision",
    max_retries=3,
    default_retry_delay=30,
)
def process_start_decision_task(
    self,
    background_task_id: str,
    user_id: str,
    situation_text: str,
    api_key: str,
) -> dict[str, Any]:
    """Start a new decision in the background.

    This is for initial decision analysis (Phase 1).
    """
    # Update task status to processing
    with get_sync_db() as db:
        task = db.query(BackgroundTask).filter(
            BackgroundTask.id == uuid.UUID(background_task_id)
        ).first()

        if task:
            task.status = TaskStatus.PROCESSING.value
            task.started_at = datetime.utcnow()
            task.celery_task_id = self.request.id
            db.commit()

    try:
        # Run the async start decision
        result = run_async(
            _process_start_decision_async(user_id, situation_text, api_key)
        )

        # Update task as completed
        with get_sync_db() as db:
            task = db.query(BackgroundTask).filter(
                BackgroundTask.id == uuid.UUID(background_task_id)
            ).first()

            if task:
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.utcnow()
                task.result_data = result
                db.commit()

        return result

    except Exception as e:
        # Update task as failed
        with get_sync_db() as db:
            task = db.query(BackgroundTask).filter(
                BackgroundTask.id == uuid.UUID(background_task_id)
            ).first()

            if task:
                task.retry_count = (task.retry_count or 0) + 1

                if self.request.retries < self.max_retries:
                    task.status = TaskStatus.PENDING.value
                    task.error_message = f"Retry {self.request.retries + 1}: {str(e)}"
                else:
                    task.status = TaskStatus.FAILED.value
                    task.completed_at = datetime.utcnow()
                    task.error_message = str(e)

                db.commit()

        raise


async def _process_start_decision_async(
    user_id: str,
    situation_text: str,
    api_key: str,
) -> dict:
    """Async implementation of start decision."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

    from app.config import get_settings
    from app.services.chat_service import ChatService
    from app.schemas.decision import DecisionResponse, DecisionNodeResponse
    from app.schemas.canvas import ChatMessage, CanvasState

    settings = get_settings()

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        chat_service = ChatService(db, api_key)

        decision, node, phase1_response = await chat_service.start_decision(
            user_id=uuid.UUID(user_id),
            situation_text=situation_text,
        )

        # Get the assistant's initial message
        chat_messages = node.chat_messages_json or []
        assistant_msg = next(
            (m for m in reversed(chat_messages) if m.get("role") == "assistant"),
            {"id": "msg_0", "role": "assistant", "content": "Hello!", "timestamp": datetime.utcnow().isoformat()}
        )

        result = {
            "decision": DecisionResponse.model_validate(decision).model_dump(mode="json"),
            "node": DecisionNodeResponse.model_validate(node).model_dump(mode="json"),
            "initial_message": {
                "id": assistant_msg["id"],
                "role": "assistant",
                "content": assistant_msg["content"],
                "timestamp": assistant_msg["timestamp"],
            },
            "canvas_state": node.canvas_state_json or {},
            "questions": phase1_response.get("questions", []),
        }

    await engine.dispose()
    return result
