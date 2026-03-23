import pytest
from unittest.mock import patch, MagicMock
import io

from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app
from app.database import Base, engine, get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.services.auth import create_access_token
from app.api.upload import validate_file_format, validate_file_size, get_file_extension
from app.config import settings

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    db = next(get_db())
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user"""
    token = create_access_token({"sub": test_user.email, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}


def create_test_file(filename: str, content: bytes, content_type: str):
    """Helper to create test file upload"""
    return ("file", (filename, io.BytesIO(content), content_type))


class TestValidationFunctions:
    """Unit tests for validation helper functions"""
    
    def test_get_file_extension_with_valid_extension(self):
        """Test extracting file extension from filename"""
        assert get_file_extension("test.mp3") == "mp3"
        assert get_file_extension("audio.WAV") == "wav"
        assert get_file_extension("video.MP4") == "mp4"
        assert get_file_extension("file.name.with.dots.flac") == "flac"
    
    def test_get_file_extension_without_extension(self):
        """Test extracting extension from filename without extension"""
        assert get_file_extension("testfile") == ""
        assert get_file_extension("") == ""
    
    def test_get_file_extension_case_insensitive(self):
        """Test that file extension extraction is case-insensitive"""
        assert get_file_extension("TEST.MP3") == "mp3"
        assert get_file_extension("Audio.WaV") == "wav"
    
    def test_validate_file_format_supported_audio(self):
        """Test validation passes for supported audio formats"""
        # Should not raise exception
        validate_file_format("mp3")
        validate_file_format("wav")
        validate_file_format("flac")
        validate_file_format("ogg")
        validate_file_format("m4a")
        validate_file_format("aac")
    
    def test_validate_file_format_supported_video(self):
        """Test validation passes for supported video formats"""
        # Should not raise exception
        validate_file_format("mp4")
        validate_file_format("avi")
        validate_file_format("mov")
        validate_file_format("webm")
    
    def test_validate_file_format_unsupported(self):
        """Test validation fails for unsupported formats"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format("txt")
        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in exc_info.value.detail
        assert "Supported formats:" in exc_info.value.detail
    
    def test_validate_file_format_unsupported_shows_all_formats(self):
        """Test that error message lists all supported formats"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format("pdf")
        
        error_detail = exc_info.value.detail
        # Check that all audio formats are listed
        assert "mp3" in error_detail
        assert "wav" in error_detail
        assert "flac" in error_detail
        # Check that all video formats are listed
        assert "mp4" in error_detail
        assert "avi" in error_detail
    
    def test_validate_file_format_empty_extension(self):
        """Test validation fails for empty extension"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format("")
        assert exc_info.value.status_code == 400
    
    def test_validate_file_size_within_limit(self):
        """Test validation passes for files within size limit"""
        # Should not raise exception
        validate_file_size(1024)  # 1KB
        validate_file_size(50 * 1024 * 1024)  # 50MB
        validate_file_size(100 * 1024 * 1024)  # Exactly 100MB
    
    def test_validate_file_size_exceeds_limit(self):
        """Test validation fails for files exceeding size limit"""
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(max_size + 1)
        
        assert exc_info.value.status_code == 413
        assert "exceeds maximum limit" in exc_info.value.detail
        assert f"{settings.MAX_UPLOAD_SIZE_MB}MB" in exc_info.value.detail
    
    def test_validate_file_size_zero_bytes(self):
        """Test validation passes for zero-byte files"""
        # Should not raise exception - empty files are technically valid
        validate_file_size(0)
    
    def test_validate_file_size_boundary_conditions(self):
        """Test validation at exact boundary conditions"""
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        
        # Exactly at limit - should pass
        validate_file_size(max_size)
        
        # One byte over limit - should fail
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(max_size + 1)
        assert exc_info.value.status_code == 413
        
        # One byte under limit - should pass
        validate_file_size(max_size - 1)


class TestFileUploadValidation:
    """Test file format and size validation"""
    
    def test_upload_valid_mp3_file(self, test_db):
        """Test uploading a valid MP3 file"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_duration.return_value = 180.5
            
            file_content = b"fake mp3 content"
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "mp3"
            assert data["file_size"] == len(file_content)
            assert data["duration"] == 180.5
            assert "file_key" in data
    
    def test_upload_valid_wav_file(self, test_db):
        """Test uploading a valid WAV file"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.wav"
            mock_duration.return_value = 120.0
            
            file_content = b"fake wav content"
            files = {"file": ("test.wav", io.BytesIO(file_content), "audio/wav")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "wav"
    
    def test_upload_unsupported_format(self, test_db):
        """Test uploading a file with unsupported format"""
        file_content = b"fake content"
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    def test_upload_file_without_extension(self, test_db):
        """Test uploading a file without extension"""
        file_content = b"fake content"
        files = {"file": ("testfile", io.BytesIO(file_content), "audio/mpeg")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 400
        assert "valid extension" in response.json()["detail"]
    
    def test_upload_file_exceeds_size_limit(self, test_db):
        """Test uploading a file that exceeds 100MB limit"""
        # Create a file larger than 100MB
        large_content = b"x" * (101 * 1024 * 1024)
        files = {"file": ("large.mp3", io.BytesIO(large_content), "audio/mpeg")}
        
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 413
        assert "exceeds maximum limit" in response.json()["detail"]


class TestAudioFormats:
    """Test all supported audio formats"""
    
    @pytest.mark.parametrize("extension,mime_type", [
        ("mp3", "audio/mpeg"),
        ("wav", "audio/wav"),
        ("flac", "audio/flac"),
        ("ogg", "audio/ogg"),
        ("m4a", "audio/mp4"),
        ("aac", "audio/aac"),
    ])
    def test_upload_audio_formats(self, test_db, extension, mime_type):
        """Test uploading all supported audio formats"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = f"uploads/anonymous/test-uuid.{extension}"
            mock_duration.return_value = 60.0
            
            file_content = b"fake audio content"
            files = {"file": (f"test.{extension}", io.BytesIO(file_content), mime_type)}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == extension


class TestVideoFormats:
    """Test video file upload with audio extraction"""
    
    @pytest.mark.parametrize("extension,mime_type", [
        ("mp4", "video/mp4"),
        ("avi", "video/x-msvideo"),
        ("mov", "video/quicktime"),
        ("webm", "video/webm"),
    ])
    def test_upload_video_formats(self, test_db, extension, mime_type):
        """Test uploading video files and extracting audio"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.extract_audio_from_video') as mock_extract, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_extract.return_value = "/tmp/extracted_audio.mp3"
            mock_duration.return_value = 240.0
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"extracted audio")
            
            file_content = b"fake video content"
            files = {"file": (f"test.{extension}", io.BytesIO(file_content), mime_type)}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "mp3"  # Video converted to MP3
            assert mock_extract.called
    
    def test_video_extraction_failure(self, test_db):
        """Test handling of video extraction failure"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_video') as mock_extract:
            mock_extract.side_effect = Exception("FFmpeg error")
            
            file_content = b"fake video content"
            files = {"file": ("test.mp4", io.BytesIO(file_content), "video/mp4")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 500
            assert "Failed to extract audio" in response.json()["detail"]


class TestAuthenticatedUpload:
    """Test file upload with authenticated users"""
    
    def test_upload_with_authenticated_user(self, test_db, test_user, auth_headers):
        """Test that authenticated users have files organized by user ID"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = f"uploads/user_{test_user.id}/test-uuid.mp3"
            mock_duration.return_value = 90.0
            
            file_content = b"fake mp3 content"
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files, headers=auth_headers)
            
            assert response.status_code == 200
            # Verify upload_file was called with user_id
            mock_upload.assert_called_once()
            call_kwargs = mock_upload.call_args[1]
            assert call_kwargs['user_id'] == test_user.id
    
    def test_upload_without_authentication(self, test_db):
        """Test that anonymous users can upload files"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_duration.return_value = 90.0
            
            file_content = b"fake mp3 content"
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            # Verify upload_file was called with user_id=None
            mock_upload.assert_called_once()
            call_kwargs = mock_upload.call_args[1]
            assert call_kwargs['user_id'] is None


class TestStorageIntegration:
    """Test storage service integration"""
    
    def test_storage_upload_failure(self, test_db):
        """Test handling of storage upload failure"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.side_effect = Exception("S3 connection error")
            mock_duration.return_value = 90.0
            
            file_content = b"fake mp3 content"
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 500
            assert "Failed to store uploaded file" in response.json()["detail"]


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_upload_file_at_size_limit(self, test_db):
        """Test uploading a file exactly at the 100MB limit"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_duration.return_value = 600.0
            
            # Exactly 100MB
            file_content = b"x" * (100 * 1024 * 1024)
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
    
    def test_upload_empty_file(self, test_db):
        """Test uploading an empty file"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_duration.return_value = 0.0
            
            file_content = b""
            files = {"file": ("test.mp3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
    
    def test_upload_case_insensitive_extension(self, test_db):
        """Test that file extensions are case-insensitive"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_duration.return_value = 60.0
            
            file_content = b"fake content"
            files = {"file": ("test.MP3", io.BytesIO(file_content), "audio/mpeg")}
            
            response = client.post("/api/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "mp3"


class TestBrowserRecordingUpload:
    """Test browser recording upload endpoint"""
    
    def test_upload_webm_recording(self, test_db):
        """Test uploading a WebM recording from browser"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.convert_audio_format') as mock_convert, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_convert.return_value = "/tmp/converted_audio.mp3"
            mock_duration.return_value = 45.5
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"converted audio")
            
            file_content = b"fake webm recording content"
            files = {"file": ("recording.webm", io.BytesIO(file_content), "audio/webm")}
            
            response = client.post("/api/upload/recording", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "mp3"  # WebM converted to MP3
            assert data["duration"] == 45.5
            assert data["message"] == "Recording uploaded successfully"
            assert mock_convert.called
    
    def test_upload_wav_recording(self, test_db):
        """Test uploading a WAV recording from browser"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.wav"
            mock_duration.return_value = 30.0
            
            file_content = b"fake wav recording content"
            files = {"file": ("recording.wav", io.BytesIO(file_content), "audio/wav")}
            
            response = client.post("/api/upload/recording", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "wav"  # WAV not converted
            assert data["duration"] == 30.0
    
    def test_upload_ogg_recording(self, test_db):
        """Test uploading an OGG recording from browser"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.return_value = "uploads/anonymous/test-uuid.ogg"
            mock_duration.return_value = 60.0
            
            file_content = b"fake ogg recording content"
            files = {"file": ("recording.ogg", io.BytesIO(file_content), "audio/ogg")}
            
            response = client.post("/api/upload/recording", files=files)
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "ogg"
    
    def test_upload_recording_unsupported_format(self, test_db):
        """Test uploading recording with unsupported format"""
        file_content = b"fake content"
        files = {"file": ("recording.mp3", io.BytesIO(file_content), "audio/mpeg")}
        
        response = client.post("/api/upload/recording", files=files)
        
        assert response.status_code == 400
        assert "Unsupported recording format" in response.json()["detail"]
    
    def test_upload_recording_without_extension(self, test_db):
        """Test uploading recording without extension"""
        file_content = b"fake content"
        files = {"file": ("recording", io.BytesIO(file_content), "audio/webm")}
        
        response = client.post("/api/upload/recording", files=files)
        
        assert response.status_code == 400
        assert "valid extension" in response.json()["detail"]
    
    def test_upload_recording_exceeds_size_limit(self, test_db):
        """Test uploading recording that exceeds 100MB limit"""
        large_content = b"x" * (101 * 1024 * 1024)
        files = {"file": ("recording.webm", io.BytesIO(large_content), "audio/webm")}
        
        response = client.post("/api/upload/recording", files=files)
        
        assert response.status_code == 413
        assert "exceeds maximum limit" in response.json()["detail"]
    
    def test_upload_recording_conversion_failure(self, test_db):
        """Test handling of WebM conversion failure"""
        with patch('app.services.audio_processor.audio_processor.convert_audio_format') as mock_convert:
            mock_convert.side_effect = Exception("FFmpeg conversion error")
            
            file_content = b"fake webm content"
            files = {"file": ("recording.webm", io.BytesIO(file_content), "audio/webm")}
            
            response = client.post("/api/upload/recording", files=files)
            
            assert response.status_code == 500
            assert "Failed to convert recording" in response.json()["detail"]
    
    def test_upload_recording_with_authenticated_user(self, test_db, test_user, auth_headers):
        """Test recording upload with authenticated user"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.convert_audio_format') as mock_convert, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_upload.return_value = f"uploads/user_{test_user.id}/test-uuid.mp3"
            mock_convert.return_value = "/tmp/converted_audio.mp3"
            mock_duration.return_value = 45.5
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"converted audio")
            
            file_content = b"fake webm recording"
            files = {"file": ("recording.webm", io.BytesIO(file_content), "audio/webm")}
            
            response = client.post("/api/upload/recording", files=files, headers=auth_headers)
            
            assert response.status_code == 200
            # Verify upload_file was called with user_id
            mock_upload.assert_called_once()
            call_kwargs = mock_upload.call_args[1]
            assert call_kwargs['user_id'] == test_user.id
    
    def test_upload_recording_storage_failure(self, test_db):
        """Test handling of storage upload failure for recording"""
        with patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('app.services.audio_processor.audio_processor.get_audio_duration') as mock_duration:
            
            mock_upload.side_effect = Exception("S3 connection error")
            mock_duration.return_value = 30.0
            
            file_content = b"fake wav recording"
            files = {"file": ("recording.wav", io.BytesIO(file_content), "audio/wav")}
            
            response = client.post("/api/upload/recording", files=files)
            
            assert response.status_code == 500
            assert "Failed to store uploaded recording" in response.json()["detail"]



class TestYouTubeUpload:
    """Test YouTube audio extraction endpoint"""
    
    def test_upload_youtube_valid_url(self, test_db):
        """Test uploading a valid YouTube URL"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 180.5)
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_getsize.return_value = 5 * 1024 * 1024  # 5MB
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["file_format"] == "mp3"
            assert data["duration"] == 180.5
            assert data["file_size"] == 5 * 1024 * 1024
            assert data["message"] == "YouTube audio extracted successfully"
            assert "file_key" in data
            assert mock_extract.called
    
    def test_upload_youtube_short_url(self, test_db):
        """Test uploading a YouTube short URL (youtu.be)"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 120.0)
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_getsize.return_value = 3 * 1024 * 1024
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://youtu.be/dQw4w9WgXcQ"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["duration"] == 120.0
    
    def test_upload_youtube_empty_url(self, test_db):
        """Test uploading with empty URL"""
        response = client.post(
            "/api/upload/youtube",
            json={"url": ""}
        )
        
        assert response.status_code == 400
        assert "YouTube URL is required" in response.json()["detail"]
    
    def test_upload_youtube_invalid_url(self, test_db):
        """Test uploading with non-YouTube URL"""
        response = client.post(
            "/api/upload/youtube",
            json={"url": "https://www.example.com/video"}
        )
        
        assert response.status_code == 400
        assert "Invalid YouTube URL" in response.json()["detail"]
    
    def test_upload_youtube_private_video(self, test_db):
        """Test uploading a private or unavailable YouTube video"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract:
            mock_extract.side_effect = ValueError("Video is private, unavailable, or restricted")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=private123"}
            )
            
            assert response.status_code == 400
            assert "private" in response.json()["detail"].lower() or "unavailable" in response.json()["detail"].lower()
    
    def test_upload_youtube_copyright_restricted(self, test_db):
        """Test uploading a copyright-restricted YouTube video"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract:
            mock_extract.side_effect = ValueError("Video is restricted due to copyright")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=copyright123"}
            )
            
            assert response.status_code == 400
            assert "copyright" in response.json()["detail"].lower() or "restricted" in response.json()["detail"].lower()
    
    def test_upload_youtube_extraction_failure(self, test_db):
        """Test handling of YouTube extraction failure"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract:
            mock_extract.side_effect = Exception("yt-dlp error")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=error123"}
            )
            
            assert response.status_code == 500
            assert "Failed to extract audio from YouTube" in response.json()["detail"]
    
    def test_upload_youtube_exceeds_size_limit(self, test_db):
        """Test YouTube extraction that results in file exceeding size limit"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('os.path.getsize') as mock_getsize:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 900.0)
            mock_getsize.return_value = 101 * 1024 * 1024  # 101MB
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=large123"}
            )
            
            assert response.status_code == 413
            assert "exceeds maximum size limit" in response.json()["detail"]
    
    def test_upload_youtube_storage_failure(self, test_db):
        """Test handling of storage upload failure for YouTube audio"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 180.0)
            mock_upload.side_effect = Exception("S3 connection error")
            mock_getsize.return_value = 5 * 1024 * 1024
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=storage123"}
            )
            
            assert response.status_code == 500
            assert "Failed to store extracted audio" in response.json()["detail"]
    
    def test_upload_youtube_with_authenticated_user(self, test_db, test_user, auth_headers):
        """Test YouTube upload with authenticated user"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 240.0)
            mock_upload.return_value = f"uploads/user_{test_user.id}/test-uuid.mp3"
            mock_getsize.return_value = 8 * 1024 * 1024
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=auth123"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            # Verify upload_file was called with user_id
            mock_upload.assert_called_once()
            call_kwargs = mock_upload.call_args[1]
            assert call_kwargs['user_id'] == test_user.id
    
    def test_upload_youtube_duration_limit(self, test_db):
        """Test that YouTube extraction respects 15-minute duration limit"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            # Return exactly 900 seconds (15 minutes)
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 900.0)
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_getsize.return_value = 20 * 1024 * 1024
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "https://www.youtube.com/watch?v=long123"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["duration"] == 900.0
            
            # Verify extract_audio_from_youtube was called with max_duration_seconds=900
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert call_args[1]['max_duration_seconds'] == 900
    
    def test_upload_youtube_url_with_whitespace(self, test_db):
        """Test YouTube URL with leading/trailing whitespace"""
        with patch('app.services.audio_processor.audio_processor.extract_audio_from_youtube') as mock_extract, \
             patch('app.services.storage.storage_service.upload_file') as mock_upload, \
             patch('os.path.getsize') as mock_getsize, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_extract.return_value = ("/tmp/youtube_audio.mp3", 150.0)
            mock_upload.return_value = "uploads/anonymous/test-uuid.mp3"
            mock_getsize.return_value = 4 * 1024 * 1024
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"youtube audio")
            
            response = client.post(
                "/api/upload/youtube",
                json={"url": "  https://www.youtube.com/watch?v=trim123  "}
            )
            
            assert response.status_code == 200
            # Verify URL was trimmed before passing to extract function
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert call_args[0][0] == "https://www.youtube.com/watch?v=trim123"
