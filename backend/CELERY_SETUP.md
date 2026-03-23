# Celery Task Queue Setup

This document describes the Celery task queue configuration for the CifraPartit platform.

## Overview

The platform uses Celery with Redis as the message broker for asynchronous task processing. This enables long-running operations like audio transcription, OCR scanning, and key detection to run in the background without blocking API requests.

## Architecture

### Task Queues

The system uses three separate queues for different types of tasks:

1. **transcription** - Audio transcription tasks
2. **ocr** - Sheet music OCR scanning tasks
3. **key_detection** - Musical key detection tasks

### Priority System

Tasks support priority levels for Pro users:
- **0** - Low priority
- **3** - Normal priority (default)
- **6** - High priority (Pro users)
- **9** - Critical priority

Pro users' transcription tasks are automatically routed with higher priority to ensure faster processing.

## Configuration

### Celery App Configuration

The Celery app is configured in `backend/app/celery_app.py`:

```python
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
```

### Task Routing

Tasks are automatically routed to their respective queues based on module name:

```python
celery_app.conf.task_routes = {
    "app.tasks.transcription.*": {"queue": "transcription"},
    "app.tasks.ocr.*": {"queue": "ocr"},
    "app.tasks.key_detection.*": {"queue": "key_detection"},
}
```

### Time Limits

- **Hard time limit**: 30 minutes
- **Soft time limit**: 25 minutes

Tasks exceeding these limits will be terminated to prevent resource exhaustion.

## Available Tasks

### Transcription Tasks

#### `process_transcription`
Process audio transcription for free and Pro users.

**Parameters:**
- `audio_file_id` (str): ID of the audio file in storage
- `instrument_type` (str): Type of instrument (piano, guitar, bass, etc.)
- `user_id` (int): ID of the user requesting transcription
- `options` (dict, optional): Additional transcription options

**Returns:** Dictionary containing transcription results

#### `process_transcription_priority`
Process audio transcription with high priority for Pro users.

Same parameters and return value as `process_transcription`.

### OCR Tasks

#### `process_sheet_music_scan`
Process sheet music image using OCR.

**Parameters:**
- `image_file_id` (str): ID of the image file in storage
- `user_id` (int): ID of the user requesting OCR
- `options` (dict, optional): Additional OCR options

**Returns:** Dictionary containing OCR results and transcription data

### Key Detection Tasks

#### `detect_key`
Detect the musical key of an audio file.

**Parameters:**
- `audio_file_id` (str): ID of the audio file in storage
- `user_id` (int): ID of the user requesting key detection

**Returns:** Dictionary containing detected key information

## Task Status Tracking

### TaskStatus Enum

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### TaskProgress Helper

The `TaskProgress` class provides a convenient way to track and update task progress:

```python
from app.tasks.task_status import TaskProgress

@celery_app.task(bind=True)
def my_task(self):
    progress = TaskProgress(self, total_steps=100)
    
    # Update progress
    progress.update(25, "Loading data")
    progress.update(50, "Processing", metadata={"items": 42})
    
    # Mark as complete
    result = {"status": "success"}
    progress.complete(result)
    return result
```

### Getting Task Status

```python
from app.tasks import get_task_status

status = get_task_status(task_id)
# Returns:
# {
#     "task_id": "abc123",
#     "status": "processing",
#     "current": 50,
#     "total": 100,
#     "percent": 50,
#     "message": "Processing audio"
# }
```

## Running Workers

### Start All Workers

To start workers for all queues:

```bash
# Linux/Mac
./backend/start_worker.sh

# Windows
backend\start_worker.bat
```

### Start Specific Queue Workers

To start workers for specific queues:

```bash
# Transcription queue only
celery -A app.celery_app worker --loglevel=info -Q transcription

# OCR queue only
celery -A app.celery_app worker --loglevel=info -Q ocr

# Key detection queue only
celery -A app.celery_app worker --loglevel=info -Q key_detection

# Multiple queues
celery -A app.celery_app worker --loglevel=info -Q transcription,ocr
```

### Worker Options

- `--concurrency=N` - Number of worker processes (default: number of CPUs)
- `--loglevel=info` - Log level (debug, info, warning, error, critical)
- `--autoscale=MAX,MIN` - Auto-scale workers between MIN and MAX

Example:
```bash
celery -A app.celery_app worker --loglevel=info -Q transcription --autoscale=10,3
```

## Monitoring

### Flower (Web-based monitoring)

Install Flower:
```bash
pip install flower
```

Start Flower:
```bash
celery -A app.celery_app flower
```

Access at: http://localhost:5555

### Command-line Monitoring

```bash
# List active tasks
celery -A app.celery_app inspect active

# List registered tasks
celery -A app.celery_app inspect registered

# List worker stats
celery -A app.celery_app inspect stats

# Purge all tasks from queue
celery -A app.celery_app purge
```

## Testing

Run Celery-related tests:

```bash
# All Celery tests
pytest backend/tests/test_celery_tasks.py -v

# Task routing tests
pytest backend/tests/test_task_routing.py -v
```

## Requirements

The following requirements are satisfied by this implementation:

- **Requirement 4.6**: Transcription engine processes audio asynchronously using the Processing_Queue
- **Requirement 4.7**: When transcription is queued, the platform provides the user with a unique tracking identifier
- **Requirement 21.3**: The Processing_Queue handles at least 10 concurrent transcription jobs

## Future Enhancements

The following features will be implemented in future tasks:

- **Task 6.2**: WebSocket connection manager for real-time progress updates
- **Task 7.3**: Complete transcription task implementation with AI engine
- **Task 9.1**: Complete key detection implementation
- **Task 10.2**: Complete OCR task implementation
- **Task 14.2**: Pro user priority queue implementation in API endpoints

## Troubleshooting

### Redis Connection Issues

If workers can't connect to Redis:
1. Ensure Redis is running: `docker-compose up redis`
2. Check Redis URL in `.env` file
3. Test connection: `redis-cli ping`

### Tasks Not Being Processed

1. Check if workers are running: `celery -A app.celery_app inspect active`
2. Check queue names match configuration
3. Check worker logs for errors

### Task Timeouts

If tasks are timing out:
1. Increase time limits in `celery_app.py`
2. Optimize task implementation
3. Consider breaking large tasks into smaller subtasks
