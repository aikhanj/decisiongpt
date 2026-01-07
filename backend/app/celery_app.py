"""Celery application configuration for background task processing."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Create Celery application
celery_app = Celery(
    "decisiongpt",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.chat_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task acknowledgment - acks_late for reliability (task requeued if worker dies)
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Track task state
    task_track_started=True,

    # Result expiration (24 hours)
    result_expires=86400,

    # Task time limits
    task_soft_time_limit=settings.task_timeout_seconds - 30,  # Soft limit 30s before hard
    task_time_limit=settings.task_timeout_seconds,

    # Worker configuration
    worker_prefetch_multiplier=1,  # One task at a time for predictable load
    worker_concurrency=4,  # Number of worker processes

    # Retry configuration
    task_default_retry_delay=30,  # 30 seconds between retries
    task_max_retries=3,
)
