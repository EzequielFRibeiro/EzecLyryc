"""
Unit tests for WebSocket connection manager and endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.websocket_manager import ConnectionManager, manager
from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestConnectionManager:
    """Test ConnectionManager class."""
    
    @pytest.mark.asyncio
    async def test_connect_new_job(self, connection_manager, mock_websocket):
        """Test connecting a WebSocket to a new job."""
        job_id = "test-job-123"
        
        await connection_manager.connect(mock_websocket, job_id)
        
        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()
        
        # Verify connection was registered
        assert job_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[job_id]
        assert connection_manager.get_connection_count(job_id) == 1
    
    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_job(self, connection_manager):
        """Test multiple clients connecting to the same job."""
        job_id = "test-job-123"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws1.accept = AsyncMock()
        ws2.accept = AsyncMock()
        
        await connection_manager.connect(ws1, job_id)
        await connection_manager.connect(ws2, job_id)
        
        # Verify both connections are registered
        assert connection_manager.get_connection_count(job_id) == 2
        assert ws1 in connection_manager.active_connections[job_id]
        assert ws2 in connection_manager.active_connections[job_id]
    
    def test_disconnect(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        connection_manager.disconnect(mock_websocket, job_id)
        
        # Verify connection was removed
        assert job_id not in connection_manager.active_connections
    
    def test_disconnect_multiple_clients(self, connection_manager):
        """Test disconnecting one client when multiple are connected."""
        job_id = "test-job-123"
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        connection_manager.active_connections[job_id] = {ws1, ws2}
        
        connection_manager.disconnect(ws1, job_id)
        
        # Verify only one connection was removed
        assert job_id in connection_manager.active_connections
        assert ws1 not in connection_manager.active_connections[job_id]
        assert ws2 in connection_manager.active_connections[job_id]
        assert connection_manager.get_connection_count(job_id) == 1
    
    @pytest.mark.asyncio
    async def test_send_progress_update(self, connection_manager, mock_websocket):
        """Test sending progress update to connected clients."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        data = {"status": "processing", "percent": 50}
        await connection_manager.send_progress_update(job_id, data)
        
        # Verify message was sent
        mock_websocket.send_json.assert_called_once_with(data)
    
    @pytest.mark.asyncio
    async def test_send_progress_update_no_connections(self, connection_manager):
        """Test sending update when no connections exist."""
        job_id = "nonexistent-job"
        
        # Should not raise an error
        await connection_manager.send_progress_update(job_id, {"status": "processing"})
    
    @pytest.mark.asyncio
    async def test_send_status_update(self, connection_manager, mock_websocket):
        """Test sending status update."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        await connection_manager.send_status_update(
            job_id, "processing", "Processing audio", extra_field="value"
        )
        
        # Verify message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["job_id"] == job_id
        assert call_args["status"] == "processing"
        assert call_args["message"] == "Processing audio"
        assert call_args["extra_field"] == "value"
    
    @pytest.mark.asyncio
    async def test_send_progress(self, connection_manager, mock_websocket):
        """Test sending progress with percentage calculation."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        await connection_manager.send_progress(
            job_id, current=50, total=100, message="Halfway done"
        )
        
        # Verify message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["current"] == 50
        assert call_args["total"] == 100
        assert call_args["percent"] == 50
        assert call_args["message"] == "Halfway done"
    
    @pytest.mark.asyncio
    async def test_send_completion(self, connection_manager, mock_websocket):
        """Test sending completion notification."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        result = {"transcription_id": "trans-123", "duration": 30}
        await connection_manager.send_completion(job_id, result)
        
        # Verify message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "complete"
        assert call_args["status"] == "completed"
        assert call_args["result"] == result
    
    @pytest.mark.asyncio
    async def test_send_error(self, connection_manager, mock_websocket):
        """Test sending error notification."""
        job_id = "test-job-123"
        connection_manager.active_connections[job_id] = {mock_websocket}
        
        error_details = {"code": "AUDIO_QUALITY_LOW"}
        await connection_manager.send_error(
            job_id, "Audio quality too low", error_details
        )
        
        # Verify message structure
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["status"] == "failed"
        assert call_args["error"] == "Audio quality too low"
        assert call_args["details"] == error_details
    
    @pytest.mark.asyncio
    async def test_handle_disconnected_client(self, connection_manager):
        """Test handling a client that disconnects during send."""
        from fastapi import WebSocketDisconnect
        
        job_id = "test-job-123"
        ws_disconnected = AsyncMock()
        ws_disconnected.send_json = AsyncMock(side_effect=WebSocketDisconnect())
        ws_active = AsyncMock()
        
        connection_manager.active_connections[job_id] = {ws_disconnected, ws_active}
        
        await connection_manager.send_progress_update(job_id, {"status": "processing"})
        
        # Verify disconnected client was removed
        assert ws_disconnected not in connection_manager.active_connections[job_id]
        # Verify active client remains
        assert ws_active in connection_manager.active_connections[job_id]
    
    def test_get_connection_count_no_connections(self, connection_manager):
        """Test getting connection count for job with no connections."""
        assert connection_manager.get_connection_count("nonexistent-job") == 0


class TestWebSocketEndpoint:
    """Test WebSocket endpoint."""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is registered."""
        client = TestClient(app)
        
        # WebSocket endpoints are not directly testable with TestClient
        # but we can verify the route exists
        routes = [route.path for route in app.routes]
        assert "/ws/transcription/{job_id}" in routes
    
    @pytest.mark.asyncio
    async def test_websocket_connection_flow(self):
        """Test WebSocket connection and message flow."""
        # This is a basic structure test
        # Full WebSocket testing requires a more complex setup
        from app.api.websocket import websocket_transcription_endpoint
        
        # Verify the endpoint function exists and is callable
        assert callable(websocket_transcription_endpoint)


class TestTaskProgressIntegration:
    """Test TaskProgress integration with WebSocket manager."""
    
    @pytest.mark.asyncio
    async def test_task_progress_sends_websocket_updates(self):
        """Test that TaskProgress sends WebSocket updates."""
        from app.tasks.task_status import TaskProgress
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-123"
        mock_task.update_state = MagicMock()
        
        progress = TaskProgress(mock_task, total_steps=100)
        
        # Update progress
        with patch('app.tasks.task_status.asyncio.create_task') as mock_create_task:
            progress.update(50, "Processing audio")
            
            # Verify Celery state was updated
            mock_task.update_state.assert_called_once()
            
            # Verify WebSocket task was created
            mock_create_task.assert_called_once()
