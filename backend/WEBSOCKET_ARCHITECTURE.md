# WebSocket Architecture for Real-Time Updates

## System Architecture

```
┌─────────────────┐
│   Web Client    │
│  (Browser/App)  │
└────────┬────────┘
         │
         │ 1. Submit transcription job
         ▼
┌─────────────────────────────────┐
│      FastAPI REST API           │
│   POST /api/transcriptions      │
└────────┬────────────────────────┘
         │
         │ 2. Queue Celery task
         │    Return job_id
         ▼
┌─────────────────────────────────┐
│      Redis (Broker)             │
│   Task Queue + Results          │
└────────┬────────────────────────┘
         │
         │ 3. Task picked up
         ▼
┌─────────────────────────────────┐
│     Celery Worker               │
│  process_transcription()        │
│                                 │
│  ┌──────────────────────────┐  │
│  │   TaskProgress           │  │
│  │   - update(step, msg)    │──┼──┐
│  │   - complete(result)     │  │  │
│  │   - fail(error)          │  │  │
│  └──────────────────────────┘  │  │
└─────────────────────────────────┘  │
                                     │
         ┌───────────────────────────┘
         │ 4. Send WebSocket updates
         ▼
┌─────────────────────────────────┐
│   WebSocket Manager             │
│   (ConnectionManager)           │
│                                 │
│  Active Connections:            │
│  {                              │
│    "job-123": {ws1, ws2, ws3}   │
│    "job-456": {ws4}             │
│  }                              │
└────────┬────────────────────────┘
         │
         │ 5. Broadcast to subscribers
         ▼
┌─────────────────────────────────┐
│   WebSocket Connections         │
│   ws://api/ws/transcription/... │
└────────┬────────────────────────┘
         │
         │ 6. Real-time updates
         ▼
┌─────────────────┐
│   Web Client    │
│  Update UI      │
└─────────────────┘
```

## Component Interaction Flow

### 1. Job Submission
```
Client → REST API → Celery Queue
                 ↓
            Returns job_id
```

### 2. WebSocket Connection
```
Client connects to: ws://api/ws/transcription/{job_id}
                 ↓
    ConnectionManager.connect()
                 ↓
    Sends initial status
```

### 3. Task Processing
```
Celery Worker starts task
         ↓
TaskProgress.update(10, "Loading audio")
         ↓
ConnectionManager.send_progress()
         ↓
All connected clients receive update
```

### 4. Progress Updates
```
Task: 0% ──→ 25% ──→ 50% ──→ 75% ──→ 100%
  │          │        │        │        │
  ↓          ↓        ↓        ↓        ↓
WebSocket: progress → progress → progress → complete
  │          │        │        │        │
  ↓          ↓        ↓        ↓        ↓
Client UI updates in real-time
```

### 5. Multiple Clients
```
Job "abc123"
    ├── Client 1 (ws1) ──→ Receives updates
    ├── Client 2 (ws2) ──→ Receives updates
    └── Client 3 (ws3) ──→ Receives updates

All clients receive the same updates simultaneously
```

## Message Flow Sequence

```
Client                  WebSocket API           ConnectionManager        Celery Worker
  │                          │                         │                      │
  │─────connect()───────────→│                         │                      │
  │                          │────register()──────────→│                      │
  │←────connected msg────────│                         │                      │
  │                          │                         │                      │
  │                          │                         │←──update(10, msg)────│
  │                          │←────send_progress()─────│                      │
  │←────progress 10%─────────│                         │                      │
  │                          │                         │                      │
  │                          │                         │←──update(50, msg)────│
  │                          │←────send_progress()─────│                      │
  │←────progress 50%─────────│                         │                      │
  │                          │                         │                      │
  │                          │                         │←──complete(result)───│
  │                          │←────send_completion()───│                      │
  │←────complete msg─────────│                         │                      │
  │                          │                         │                      │
  │─────disconnect()────────→│                         │                      │
  │                          │────unregister()────────→│                      │
```

## Data Structures

### ConnectionManager State
```python
{
    "job-abc123": {
        <WebSocket object 1>,
        <WebSocket object 2>,
        <WebSocket object 3>
    },
    "job-def456": {
        <WebSocket object 4>
    }
}
```

### Progress Message
```json
{
    "type": "progress",
    "job_id": "abc123",
    "status": "processing",
    "current": 50,
    "total": 100,
    "percent": 50,
    "message": "Detecting notes and rhythm",
    "metadata": {
        "notes_detected": 120,
        "current_section": "verse"
    }
}
```

## Error Handling

### Client Disconnection
```
Client disconnects unexpectedly
         ↓
WebSocket.send() raises WebSocketDisconnect
         ↓
ConnectionManager catches exception
         ↓
Removes connection from active_connections
         ↓
Continues sending to other clients
```

### WebSocket Send Failure
```
TaskProgress.update() called
         ↓
Tries to send WebSocket update
         ↓
WebSocket send fails
         ↓
Logs error but doesn't fail task
         ↓
Task continues processing normally
```

## Scalability Considerations

### Single Server
- ConnectionManager is in-memory
- All connections on same server
- Works for small to medium deployments

### Multiple Servers (Future)
- Need shared state (Redis Pub/Sub)
- Broadcast updates to all servers
- Each server manages its own connections
- Clients connect to any server

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Server 1 │     │ Server 2 │     │ Server 3 │
│  ws1,ws2 │     │  ws3,ws4 │     │  ws5,ws6 │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      │
              ┌───────▼────────┐
              │  Redis Pub/Sub │
              │   (Broadcast)  │
              └────────────────┘
                      ▲
                      │
              ┌───────┴────────┐
              │  Celery Worker │
              │  (Publisher)   │
              └────────────────┘
```

## Performance Metrics

### Connection Overhead
- Each WebSocket: ~4KB memory
- 1000 connections: ~4MB memory
- Minimal CPU usage when idle

### Message Latency
- In-memory: <1ms
- Network: 10-50ms typical
- Total: <100ms end-to-end

### Throughput
- Single server: 10,000+ concurrent connections
- Message rate: 1000+ messages/second
- Limited by network bandwidth, not CPU

## Security Considerations

### Authentication (Future Enhancement)
```python
@router.websocket("/transcription/{job_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(...)  # JWT token
):
    # Verify token
    user = verify_token(token)
    
    # Verify user owns job
    if not user_owns_job(user, job_id):
        await websocket.close(code=403)
        return
    
    # Continue with connection
    await manager.connect(websocket, job_id)
```

### Rate Limiting
- Limit connections per IP
- Limit connections per user
- Prevent connection flooding

### Message Validation
- Validate all incoming messages
- Sanitize user input
- Prevent injection attacks

## Monitoring and Debugging

### Metrics to Track
- Active connections count
- Messages sent per second
- Connection duration
- Disconnection reasons
- Error rates

### Logging
```python
logger.info(f"WebSocket connected: job={job_id}, total={count}")
logger.info(f"WebSocket disconnected: job={job_id}")
logger.error(f"WebSocket send failed: job={job_id}, error={e}")
```

### Health Check
```python
@app.get("/ws/health")
async def websocket_health():
    return {
        "active_jobs": len(manager.active_connections),
        "total_connections": sum(
            len(conns) for conns in manager.active_connections.values()
        )
    }
```
