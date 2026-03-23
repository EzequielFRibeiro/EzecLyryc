"""
Celery tasks for asynchronous processing.
"""
from app.tasks.transcription import process_transcription, process_transcription_priority
from app.tasks.ocr import process_sheet_music_scan
from app.tasks.key_detection import detect_key
from app.tasks.task_status import (
    TaskStatus,
    TaskProgress,
    get_task_status,
    get_estimated_wait_time
)

__all__ = [
    "process_transcription",
    "process_transcription_priority",
    "process_sheet_music_scan",
    "detect_key",
    "TaskStatus",
    "TaskProgress",
    "get_task_status",
    "get_estimated_wait_time",
]
