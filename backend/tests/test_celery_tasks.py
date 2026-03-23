"""
Unit tests for Celery task configuration and status tracking.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.celery_app import celery_app
from app.tasks.task_status import (
    TaskStatus,
    TaskProgress,
    get_task_status,
    get_estimated_wait_time
)


class TestCeleryConfiguration:
    """Test Celery app configuration."""
    
    def test_celery_broker_configured(self):
        """Test that Celery broker is configured with Redis."""
        assert celery_app.conf.broker_url is not None
        assert "redis://" in celery_app.conf.broker_url
    
    def test_celery_backend_configured(self):
        """Test that Celery result backend is configured."""
        assert celery_app.conf.result_backend is not None
        assert "redis://" in celery_app.conf.result_backend
    
    def test_task_routes_configured(self):
        """Test that task routes are configured for different queues."""
        routes = celery_app.conf.task_routes
        assert routes is not None
        assert "app.tasks.transcription.*" in routes
        assert "app.tasks.ocr.*" in routes
        assert "app.tasks.key_detection.*" in routes
        assert routes["app.tasks.transcription.*"]["queue"] == "transcription"
        assert routes["app.tasks.ocr.*"]["queue"] == "ocr"
        assert routes["app.tasks.key_detection.*"]["queue"] == "key_detection"
    
    def test_priority_queue_configured(self):
        """Test that priority queue settings are configured."""
        assert celery_app.conf.task_default_priority == 5
        assert celery_app.conf.broker_transport_options is not None
        assert "priority_steps" in celery_app.conf.broker_transport_options
        assert "queue_order_strategy" in celery_app.conf.broker_transport_options
    
    def test_task_serialization_configured(self):
        """Test that task serialization is configured."""
        assert celery_app.conf.task_serializer == "json"
        assert "json" in celery_app.conf.accept_content
        assert celery_app.conf.result_serializer == "json"
    
    def test_task_time_limits_configured(self):
        """Test that task time limits are configured."""
        assert celery_app.conf.task_time_limit == 30 * 60  # 30 minutes
        assert celery_app.conf.task_soft_time_limit == 25 * 60  # 25 minutes


class TestTaskStatus:
    """Test TaskStatus enumeration."""
    
    def test_task_status_values(self):
        """Test that TaskStatus has all required values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"


class TestTaskProgress:
    """Test TaskProgress helper class."""
    
    def test_task_progress_initialization(self):
        """Test TaskProgress initialization."""
        mock_task = Mock()
        progress = TaskProgress(mock_task, total_steps=100)
        
        assert progress.task == mock_task
        assert progress.total_steps == 100
        assert progress.current_step == 0
    
    def test_task_progress_update(self):
        """Test TaskProgress update method."""
        mock_task = Mock()
        progress = TaskProgress(mock_task, total_steps=100)
        
        progress.update(50, "Processing audio")
        
        mock_task.update_state.assert_called_once()
        call_args = mock_task.update_state.call_args
        assert call_args[1]["state"] == "PROGRESS"
        assert call_args[1]["meta"]["status"] == TaskStatus.PROCESSING
        assert call_args[1]["meta"]["current"] == 50
        assert call_args[1]["meta"]["total"] == 100
        assert call_args[1]["meta"]["percent"] == 50
        assert call_args[1]["meta"]["message"] == "Processing audio"
    
    def test_task_progress_update_with_metadata(self):
        """Test TaskProgress update with additional metadata."""
        mock_task = Mock()
        progress = TaskProgress(mock_task, total_steps=100)
        
        metadata = {"notes_detected": 42, "duration": 30.5}
        progress.update(75, "Generating notation", metadata=metadata)
        
        call_args = mock_task.update_state.call_args
        assert call_args[1]["meta"]["metadata"] == metadata
    
    def test_task_progress_complete(self):
        """Test TaskProgress complete method."""
        mock_task = Mock()
        progress = TaskProgress(mock_task)
        
        result = {"transcription_id": "123", "notes": []}
        progress.complete(result)
        
        assert result["status"] == TaskStatus.COMPLETED
    
    def test_task_progress_fail(self):
        """Test TaskProgress fail method."""
        mock_task = Mock()
        progress = TaskProgress(mock_task)
        
        progress.fail("Audio file not found")
        
        mock_task.update_state.assert_called_once()
        call_args = mock_task.update_state.call_args
        assert call_args[1]["state"] == "FAILURE"
        assert call_args[1]["meta"]["status"] == TaskStatus.FAILED
        assert call_args[1]["meta"]["error"] == "Audio file not found"
    
    def test_task_progress_fail_with_details(self):
        """Test TaskProgress fail with error details."""
        mock_task = Mock()
        progress = TaskProgress(mock_task)
        
        error_details = {"file_id": "abc123", "error_code": "NOT_FOUND"}
        progress.fail("Audio file not found", error_details=error_details)
        
        call_args = mock_task.update_state.call_args
        assert call_args[1]["meta"]["details"] == error_details


class TestGetTaskStatus:
    """Test get_task_status function."""
    
    @patch("app.tasks.task_status.AsyncResult")
    def test_get_task_status_pending(self, mock_async_result):
        """Test getting status of a pending task."""
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_async_result.return_value = mock_result
        
        status = get_task_status("task-123")
        
        assert status["task_id"] == "task-123"
        assert status["status"] == TaskStatus.QUEUED
        assert "message" in status
    
    @patch("app.tasks.task_status.AsyncResult")
    def test_get_task_status_progress(self, mock_async_result):
        """Test getting status of a task in progress."""
        mock_result = MagicMock()
        mock_result.state = "PROGRESS"
        mock_result.info = {
            "status": TaskStatus.PROCESSING,
            "current": 50,
            "total": 100,
            "percent": 50,
            "message": "Processing audio"
        }
        mock_async_result.return_value = mock_result
        
        status = get_task_status("task-123")
        
        assert status["task_id"] == "task-123"
        assert status["status"] == TaskStatus.PROCESSING
        assert status["current"] == 50
        assert status["percent"] == 50
    
    @patch("app.tasks.task_status.AsyncResult")
    def test_get_task_status_success(self, mock_async_result):
        """Test getting status of a completed task."""
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "transcription_id": "123",
            "notation_data": {}
        }
        mock_async_result.return_value = mock_result
        
        status = get_task_status("task-123")
        
        assert status["task_id"] == "task-123"
        assert status["status"] == TaskStatus.COMPLETED
        assert "result" in status
        assert status["result"]["transcription_id"] == "123"
    
    @patch("app.tasks.task_status.AsyncResult")
    def test_get_task_status_failure(self, mock_async_result):
        """Test getting status of a failed task."""
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = {
            "error": "Audio file not found",
            "details": {"file_id": "abc123"}
        }
        mock_async_result.return_value = mock_result
        
        status = get_task_status("task-123")
        
        assert status["task_id"] == "task-123"
        assert status["status"] == TaskStatus.FAILED
        assert status["error"] == "Audio file not found"
        assert "details" in status
    
    @patch("app.tasks.task_status.AsyncResult")
    def test_get_task_status_failure_with_exception(self, mock_async_result):
        """Test getting status of a failed task with exception."""
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = Exception("Something went wrong")
        mock_async_result.return_value = mock_result
        
        status = get_task_status("task-123")
        
        assert status["task_id"] == "task-123"
        assert status["status"] == TaskStatus.FAILED
        assert "error" in status


class TestGetEstimatedWaitTime:
    """Test get_estimated_wait_time function."""
    
    def test_get_estimated_wait_time_default(self):
        """Test getting estimated wait time returns a value."""
        wait_time = get_estimated_wait_time("transcription")
        
        assert wait_time is not None
        assert isinstance(wait_time, int)
        assert wait_time > 0
    
    def test_get_estimated_wait_time_different_queues(self):
        """Test getting estimated wait time for different queues."""
        transcription_time = get_estimated_wait_time("transcription")
        ocr_time = get_estimated_wait_time("ocr")
        
        assert transcription_time is not None
        assert ocr_time is not None
