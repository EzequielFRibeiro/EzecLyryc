"""
WebSocket connection manager for real-time transcription progress updates.
"""
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Map of job_id to set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """
        Accept and register a new WebSocket connection for a job.
        
        Args:
            websocket: WebSocket connection instance
            job_id: Transcription job ID to subscribe to
        """
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection instance
            job_id: Transcription job ID
        """
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            # Clean up empty job entries
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            
            logger.info(f"WebSocket disconnected for job {job_id}")
    
    async def send_progress_update(self, job_id: str, data: dict):
        """
        Send progress update to all connections subscribed to a job.
        
        Args:
            job_id: Transcription job ID
            data: Progress data to send
        """
        if job_id not in self.active_connections:
            return
        
        # Create a copy of the set to avoid modification during iteration
        connections = self.active_connections[job_id].copy()
        disconnected = []
        
        for connection in connections:
            try:
                await connection.send_json(data)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, job_id)
    
    async def send_status_update(self, job_id: str, status: str, message: str, **kwargs):
        """
        Send a status update message.
        
        Args:
            job_id: Transcription job ID
            status: Status string (queued, processing, completed, failed)
            message: Human-readable message
            **kwargs: Additional data to include in the message
        """
        data = {
            "type": "status",
            "job_id": job_id,
            "status": status,
            "message": message,
            **kwargs
        }
        await self.send_progress_update(job_id, data)
    
    async def send_progress(self, job_id: str, current: int, total: int, message: str, **kwargs):
        """
        Send a progress update with percentage.
        
        Args:
            job_id: Transcription job ID
            current: Current step
            total: Total steps
            message: Progress message
            **kwargs: Additional metadata
        """
        percent = int((current / total) * 100) if total > 0 else 0
        data = {
            "type": "progress",
            "job_id": job_id,
            "status": "processing",
            "current": current,
            "total": total,
            "percent": percent,
            "message": message,
            **kwargs
        }
        await self.send_progress_update(job_id, data)
    
    async def send_completion(self, job_id: str, result: dict):
        """
        Send a completion notification.
        
        Args:
            job_id: Transcription job ID
            result: Result data
        """
        data = {
            "type": "complete",
            "job_id": job_id,
            "status": "completed",
            "message": "Transcription completed successfully",
            "result": result
        }
        await self.send_progress_update(job_id, data)
    
    async def send_error(self, job_id: str, error_message: str, error_details: dict = None):
        """
        Send an error notification.
        
        Args:
            job_id: Transcription job ID
            error_message: Error message
            error_details: Additional error details
        """
        data = {
            "type": "error",
            "job_id": job_id,
            "status": "failed",
            "message": error_message,
            "error": error_message
        }
        if error_details:
            data["details"] = error_details
        
        await self.send_progress_update(job_id, data)
    
    def get_connection_count(self, job_id: str) -> int:
        """
        Get the number of active connections for a job.
        
        Args:
            job_id: Transcription job ID
            
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(job_id, set()))


# Global connection manager instance
manager = ConnectionManager()
