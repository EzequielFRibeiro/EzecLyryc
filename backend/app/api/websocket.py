"""
WebSocket endpoints for real-time transcription updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from app.services.websocket_manager import manager
from app.tasks.task_status import get_task_status
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/transcription/{job_id}")
async def websocket_transcription_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for receiving real-time transcription progress updates.
    
    Clients connect to this endpoint with a job_id to receive:
    - Status updates (queued, processing, completed, failed)
    - Progress updates with percentage and messages
    - Completion notifications with results
    - Error notifications
    
    Args:
        websocket: WebSocket connection
        job_id: Transcription job ID (Celery task ID)
    """
    await manager.connect(websocket, job_id)
    
    try:
        # Send initial status
        initial_status = get_task_status(job_id)
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Connected to transcription updates",
            "initial_status": initial_status
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (e.g., ping/pong for keepalive)
                data = await websocket.receive_text()
                
                # Handle ping messages
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle status request
                elif data == "status":
                    current_status = get_task_status(job_id)
                    await websocket.send_json({
                        "type": "status_response",
                        "job_id": job_id,
                        **current_status
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        manager.disconnect(websocket, job_id)
