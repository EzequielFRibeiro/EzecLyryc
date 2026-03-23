from celery import Celery
from app.config import settings

celery_app = Celery(
    "cifrapartit",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.transcription",
        "app.tasks.ocr",
        "app.tasks.key_detection"
    ]
)

# Task routing configuration
celery_app.conf.task_routes = {
    "app.tasks.transcription.process_transcription": {"queue": "transcription"},
    "app.tasks.transcription.process_transcription_priority": {"queue": "transcription_priority"},
    "app.tasks.ocr.*": {"queue": "ocr"},
    "app.tasks.key_detection.*": {"queue": "key_detection"},
}

# Priority queue configuration for Pro users
celery_app.conf.task_default_priority = 5
celery_app.conf.broker_transport_options = {
    "priority_steps": [0, 3, 6, 9],  # 0=low, 3=normal, 6=high, 9=critical
    "queue_order_strategy": "priority",
}

# Queue priority levels
# transcription_priority queue: Pro users (priority 9)
# transcription queue: Free users (priority 3)
celery_app.conf.task_queue_max_priority = 10

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    result_expires=3600,  # Results expire after 1 hour
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_prefetch_multiplier=1,  # Fetch one task at a time for better priority handling
)
