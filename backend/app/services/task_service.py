"""Service for managing background tasks."""

import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_task import BackgroundTask, TaskStatus, TaskType


class TaskService:
    """Service for managing background tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        task_type: TaskType,
        decision_id: uuid.UUID,
        node_id: uuid.UUID,
        input_data: dict | None = None,
    ) -> BackgroundTask:
        """Create a new background task."""
        task = BackgroundTask(
            task_type=task_type.value,
            decision_id=decision_id,
            node_id=node_id,
            input_data=input_data or {},
            status=TaskStatus.PENDING.value,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: uuid.UUID) -> BackgroundTask | None:
        """Get a task by ID."""
        result = await self.db.execute(
            select(BackgroundTask).where(BackgroundTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_task_by_celery_id(self, celery_task_id: str) -> BackgroundTask | None:
        """Get a task by Celery task ID."""
        result = await self.db.execute(
            select(BackgroundTask).where(BackgroundTask.celery_task_id == celery_task_id)
        )
        return result.scalar_one_or_none()

    async def update_task_celery_id(
        self, task_id: uuid.UUID, celery_task_id: str
    ) -> BackgroundTask | None:
        """Update task with Celery task ID."""
        task = await self.get_task(task_id)
        if task:
            task.celery_task_id = celery_task_id
            await self.db.commit()
            await self.db.refresh(task)
        return task

    async def update_task_status(
        self,
        task_id: uuid.UUID,
        status: TaskStatus,
        result_data: dict | None = None,
        error_message: str | None = None,
    ) -> BackgroundTask | None:
        """Update task status and optionally result/error."""
        task = await self.get_task(task_id)
        if not task:
            return None

        task.status = status.value

        if status == TaskStatus.PROCESSING:
            task.started_at = datetime.utcnow()
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = datetime.utcnow()

        if result_data is not None:
            task.result_data = result_data
        if error_message is not None:
            task.error_message = error_message

        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def increment_retry_count(self, task_id: uuid.UUID) -> BackgroundTask | None:
        """Increment retry count for a task."""
        task = await self.get_task(task_id)
        if task:
            task.retry_count += 1
            await self.db.commit()
            await self.db.refresh(task)
        return task

    async def get_pending_tasks_for_node(
        self, node_id: uuid.UUID
    ) -> list[BackgroundTask]:
        """Get all pending/processing tasks for a node."""
        result = await self.db.execute(
            select(BackgroundTask)
            .where(BackgroundTask.node_id == node_id)
            .where(
                BackgroundTask.status.in_([
                    TaskStatus.PENDING.value,
                    TaskStatus.PROCESSING.value,
                ])
            )
            .order_by(BackgroundTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_recent_tasks_for_node(
        self, node_id: uuid.UUID, limit: int = 10
    ) -> list[BackgroundTask]:
        """Get recent tasks for a node (all statuses)."""
        result = await self.db.execute(
            select(BackgroundTask)
            .where(BackgroundTask.node_id == node_id)
            .order_by(BackgroundTask.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cleanup_stale_tasks(
        self, older_than_minutes: int = 30
    ) -> int:
        """Mark stuck processing tasks as failed."""
        from sqlalchemy import update as sql_update

        cutoff = datetime.utcnow()
        from datetime import timedelta
        cutoff = cutoff - timedelta(minutes=older_than_minutes)

        result = await self.db.execute(
            sql_update(BackgroundTask)
            .where(BackgroundTask.status == TaskStatus.PROCESSING.value)
            .where(BackgroundTask.started_at < cutoff)
            .values(
                status=TaskStatus.FAILED.value,
                error_message="Task timed out",
                completed_at=datetime.utcnow(),
            )
        )
        await self.db.commit()
        return result.rowcount
