"""
Task status tracking and progress update utilities for Celery tasks.
"""
from enum import Enum
from typing import Optional, Dict, Any
from celery import Task
from celery.result import AsyncResult
import asyncio


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskProgress:
    """Helper class for tracking and updating task progress."""
    
    def __init__(self, task: Task, total_steps: int = 100):
        """
        Initialize task progress tracker.
        
        Args:
            task: Celery task instance
            total_steps: Total number of steps (default 100 for percentage)
        """
        self.task = task
        self.total_steps = total_steps
        self.current_step = 0
    
    def update(
        self,
        step: int,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update task progress and send WebSocket notification.
        
        Args:
            step: Current step number
            message: Progress message
            metadata: Additional metadata to include
        """
        self.current_step = step
        progress_data = {
            "status": TaskStatus.PROCESSING,
            "current": step,
            "total": self.total_steps,
            "percent": int((step / self.total_steps) * 100),
            "message": message,
        }
        
        if metadata:
            progress_data["metadata"] = metadata
        
        # Update Celery task state
        self.task.update_state(
            state="PROGRESS",
            meta=progress_data
        )
        
        # Send WebSocket notification
        self._send_websocket_update(progress_data)
    
    def complete(self, result: Dict[str, Any]) -> None:
        """
        Mark task as completed and send WebSocket notification.
        
        Args:
            result: Final result data
        """
        result["status"] = TaskStatus.COMPLETED
        
        # Send WebSocket notification
        self._send_websocket_completion(result)
    
    def fail(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark task as failed and send WebSocket notification.
        
        Args:
            error_message: Error message
            error_details: Additional error details
        """
        error_data = {
            "status": TaskStatus.FAILED,
            "error": error_message,
        }
        
        if error_details:
            error_data["details"] = error_details
        
        # Update Celery task state
        self.task.update_state(
            state="FAILURE",
            meta=error_data
        )
        
        # Send WebSocket notification
        self._send_websocket_error(error_message, error_details)
    
    def _send_websocket_update(self, progress_data: Dict[str, Any]) -> None:
        """Send progress update via WebSocket."""
        try:
            from app.services.websocket_manager import manager
            job_id = self.task.request.id
            
            # Run async function in sync context
            asyncio.create_task(
                manager.send_progress(
                    job_id=job_id,
                    current=progress_data["current"],
                    total=progress_data["total"],
                    message=progress_data["message"],
                    metadata=progress_data.get("metadata")
                )
            )
        except Exception as e:
            # Don't fail the task if WebSocket notification fails
            import logging
            logging.error(f"Failed to send WebSocket update: {e}")
    
    def _send_websocket_completion(self, result: Dict[str, Any]) -> None:
        """Send completion notification via WebSocket."""
        try:
            from app.services.websocket_manager import manager
            job_id = self.task.request.id
            
            asyncio.create_task(
                manager.send_completion(job_id=job_id, result=result)
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send WebSocket completion: {e}")
    
    def _send_websocket_error(self, error_message: str, error_details: Optional[Dict[str, Any]]) -> None:
        """Send error notification via WebSocket."""
        try:
            from app.services.websocket_manager import manager
            job_id = self.task.request.id
            
            asyncio.create_task(
                manager.send_error(
                    job_id=job_id,
                    error_message=error_message,
                    error_details=error_details
                )
            )
        except Exception as e:
            import logging
            logging.error(f"Failed to send WebSocket error: {e}")


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the current status of a task.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dictionary containing task status information
    """
    result = AsyncResult(task_id)
    
    if result.state == "PENDING":
        return {
            "task_id": task_id,
            "status": TaskStatus.QUEUED,
            "message": "Task is queued and waiting to be processed"
        }
    elif result.state == "PROGRESS":
        return {
            "task_id": task_id,
            **result.info
        }
    elif result.state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": TaskStatus.COMPLETED,
            "result": result.result
        }
    elif result.state == "FAILURE":
        error_info = result.info if isinstance(result.info, dict) else {"error": str(result.info)}
        return {
            "task_id": task_id,
            "status": TaskStatus.FAILED,
            **error_info
        }
    else:
        return {
            "task_id": task_id,
            "status": result.state.lower(),
            "message": f"Task is in {result.state} state"
        }


def get_estimated_wait_time(queue_name: str = "transcription") -> Optional[int]:
    """
    Get estimated wait time for a queue.
    
    Args:
        queue_name: Name of the queue
        
    Returns:
        Estimated wait time in seconds, or None if unavailable
    """
    # This is a placeholder implementation
    # In production, you would inspect the queue length and calculate based on average processing time
    # For now, return a default estimate
    return 120  # 2 minutes default estimate
