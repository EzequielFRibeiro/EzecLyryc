"""
Integration tests for Celery task routing.
"""
import pytest
from app.celery_app import celery_app
from app.tasks import (
    process_transcription,
    process_sheet_music_scan,
    detect_key
)


class TestTaskRouting:
    """Test that tasks are properly registered and routed."""
    
    def test_transcription_task_registered(self):
        """Test that transcription task is registered."""
        task_name = "app.tasks.transcription.process_transcription"
        assert task_name in celery_app.tasks
    
    def test_transcription_priority_task_registered(self):
        """Test that priority transcription task is registered."""
        task_name = "app.tasks.transcription.process_transcription_priority"
        assert task_name in celery_app.tasks
    
    def test_ocr_task_registered(self):
        """Test that OCR task is registered."""
        task_name = "app.tasks.ocr.process_sheet_music_scan"
        assert task_name in celery_app.tasks
    
    def test_key_detection_task_registered(self):
        """Test that key detection task is registered."""
        task_name = "app.tasks.key_detection.detect_key"
        assert task_name in celery_app.tasks
    
    def test_transcription_task_route(self):
        """Test that transcription tasks route to transcription queue."""
        task_name = "app.tasks.transcription.process_transcription"
        routes = celery_app.conf.task_routes
        
        # Check if the pattern matches
        for pattern, config in routes.items():
            if "transcription" in pattern:
                assert config["queue"] == "transcription"
    
    def test_ocr_task_route(self):
        """Test that OCR tasks route to ocr queue."""
        task_name = "app.tasks.ocr.process_sheet_music_scan"
        routes = celery_app.conf.task_routes
        
        # Check if the pattern matches
        for pattern, config in routes.items():
            if "ocr" in pattern:
                assert config["queue"] == "ocr"
    
    def test_key_detection_task_route(self):
        """Test that key detection tasks route to key_detection queue."""
        task_name = "app.tasks.key_detection.detect_key"
        routes = celery_app.conf.task_routes
        
        # Check if the pattern matches
        for pattern, config in routes.items():
            if "key_detection" in pattern:
                assert config["queue"] == "key_detection"
    
    def test_task_includes_configured(self):
        """Test that all task modules are included in Celery config."""
        includes = celery_app.conf.include
        assert "app.tasks.transcription" in includes
        assert "app.tasks.ocr" in includes
        assert "app.tasks.key_detection" in includes
