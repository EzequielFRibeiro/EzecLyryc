# WebSocket Real-Time Updates

## Overview

The WebSocket connection manager provides real-time progress updates for transcription jobs. Clients can connect to a WebSocket endpoint and receive live updates as their transcription is processed.

## WebSocket Endpoint

```
ws://localhost:8000/ws/transcription/{job_id}
```

Replace `{job_id}` with the Celery task ID returned when submitting a transcription job.

## Connection Flow

1. Client submits a transcription job via REST API
2. Server returns a `job_id` (Celery task ID)
3. Client connects to WebSocket endpoint with the `job_id`
4. Server sends initial status message
5. Server sends progress updates as transcription processes
6. Server sends completion or error message when done
7. Client can disconnect or keep connection open

## Message Types

### Connected Message
Sent immediately after connection is established:
```json
{
  "type": "connected",
  "job_id": "abc123",
  "message": "Connected to transcription updates",
  "initial_status": {
    "task_id": "abc123",
    "status": "queued",
    "message": "Task is queued and waiting to be processed"
  }
}
```

### Progress Update
Sent during processing:
```json
{
  "type": "progress",
  "job_id": "abc123",
  "status": "processing",
  "current": 50,
  "total": 100,
  "percent": 50,
  "message": "Detecting notes and rhythm"
}
```

### Status Update
Sent when status changes:
```json
{
  "type": "status",
  "job_id": "abc123",
  "status": "processing",
  "message": "Processing audio file"
}
```

### Completion Message
Sent when transcription completes successfully:
```json
{
  "type": "complete",
  "job_id": "abc123",
  "status": "completed",
  "message": "Transcription completed successfully",
  "result": {
    "transcription_id": "trans-456",
    "duration": 30,
    "notes_detected": 150
  }
}
```

### Error Message
Sent when transcription fails:
```json
{
  "type": "error",
  "job_id": "abc123",
  "status": "failed",
  "message": "Audio quality too low",
  "error": "Audio quality too low",
  "details": {
    "code": "AUDIO_QUALITY_LOW",
    "suggestion": "Try recording in a quieter environment"
  }
}
```

## Client Commands

Clients can send messages to the server:

### Ping
Keep connection alive:
```
ping
```

Server responds with:
```json
{
  "type": "pong"
}
```

### Status Request
Request current status:
```
status
```

Server responds with:
```json
{
  "type": "status_response",
  "job_id": "abc123",
  "task_id": "abc123",
  "status": "processing",
  "current": 50,
  "total": 100,
  "percent": 50,
  "message": "Detecting notes and rhythm"
}
```

## JavaScript Client Example

```javascript
// Connect to WebSocket
const jobId = 'abc123'; // From transcription submission
const ws = new WebSocket(`ws://localhost:8000/ws/transcription/${jobId}`);

// Handle connection open
ws.onopen = () => {
  console.log('Connected to transcription updates');
};

// Handle incoming messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'connected':
      console.log('Initial status:', data.initial_status);
      break;
      
    case 'progress':
      console.log(`Progress: ${data.percent}% - ${data.message}`);
      updateProgressBar(data.percent);
      break;
      
    case 'complete':
      console.log('Transcription completed!', data.result);
      showTranscription(data.result);
      ws.close();
      break;
      
    case 'error':
      console.error('Transcription failed:', data.error);
      showError(data.message, data.details);
      ws.close();
      break;
      
    case 'pong':
      console.log('Pong received');
      break;
  }
};

// Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

// Handle connection close
ws.onclose = () => {
  console.log('WebSocket connection closed');
};

// Send ping every 30 seconds to keep connection alive
const pingInterval = setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('ping');
  } else {
    clearInterval(pingInterval);
  }
}, 30000);

// Request status manually
function requestStatus() {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send('status');
  }
}
```

## React Hook Example

```typescript
import { useEffect, useState } from 'react';

interface TranscriptionProgress {
  status: string;
  percent: number;
  message: string;
  result?: any;
  error?: string;
}

export function useTranscriptionProgress(jobId: string) {
  const [progress, setProgress] = useState<TranscriptionProgress>({
    status: 'connecting',
    percent: 0,
    message: 'Connecting...'
  });

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/transcription/${jobId}`);

    ws.onopen = () => {
      setProgress(prev => ({ ...prev, status: 'connected', message: 'Connected' }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'progress':
          setProgress({
            status: data.status,
            percent: data.percent,
            message: data.message
          });
          break;

        case 'complete':
          setProgress({
            status: 'completed',
            percent: 100,
            message: 'Completed',
            result: data.result
          });
          ws.close();
          break;

        case 'error':
          setProgress({
            status: 'failed',
            percent: 0,
            message: data.message,
            error: data.error
          });
          ws.close();
          break;
      }
    };

    ws.onerror = () => {
      setProgress({
        status: 'error',
        percent: 0,
        message: 'Connection error',
        error: 'Failed to connect to server'
      });
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [jobId]);

  return progress;
}
```

## Integration with Celery Tasks

To send WebSocket updates from Celery tasks, use the `TaskProgress` helper:

```python
from app.tasks.task_status import TaskProgress
from celery import shared_task

@shared_task(bind=True)
def process_transcription(self, audio_file_path: str):
    # Initialize progress tracker
    progress = TaskProgress(self, total_steps=100)
    
    # Update progress at various stages
    progress.update(10, "Loading audio file")
    audio = load_audio(audio_file_path)
    
    progress.update(30, "Detecting notes")
    notes = detect_notes(audio)
    
    progress.update(60, "Analyzing rhythm")
    rhythm = analyze_rhythm(audio)
    
    progress.update(90, "Generating notation")
    notation = generate_notation(notes, rhythm)
    
    # Mark as complete
    result = {
        "transcription_id": "trans-123",
        "notes_count": len(notes)
    }
    progress.complete(result)
    
    return result
```

## Connection Lifecycle

1. **Connection**: Client connects, server accepts and registers connection
2. **Initial Status**: Server sends current task status
3. **Updates**: Server sends progress updates as task processes
4. **Completion**: Server sends final result or error
5. **Disconnection**: Client or server closes connection
6. **Cleanup**: Server removes connection from active connections

## Error Handling

- If a client disconnects during processing, the server automatically removes the connection
- If sending a message fails, the server logs the error but doesn't fail the task
- Multiple clients can connect to the same job_id simultaneously
- Reconnection is supported - clients can reconnect at any time to get current status

## Performance Considerations

- WebSocket connections are lightweight and can handle many concurrent connections
- Progress updates are sent only to clients subscribed to specific job_ids
- Disconnected clients are automatically cleaned up
- No polling required - updates are pushed in real-time
