"""
Pytest configuration and fixtures for tests.
This file is loaded before any test modules, allowing us to mock services
that initialize on import.
"""
import os
from unittest.mock import patch, MagicMock

# Set environment variables before any imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY", "minioadmin")
os.environ.setdefault("S3_SECRET_KEY", "minioadmin")
os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SMTP_HOST", "smtp.test.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@test.com")
os.environ.setdefault("SMTP_PASSWORD", "test-password")
os.environ.setdefault("FROM_EMAIL", "noreply@test.com")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ALLOWED_AUDIO_FORMATS", "mp3,wav,flac,ogg,m4a,aac")
os.environ.setdefault("ALLOWED_VIDEO_FORMATS", "mp4,avi,mov,webm")

# Mock S3 storage service initialization to avoid connection errors
_storage_mock = patch('boto3.client')
_storage_mock.start()
