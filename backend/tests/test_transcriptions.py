import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.transcription import Transcription, TranscriptionStatus, InstrumentType
from app.services.auth import get_password_hash, create_access_token
from app.config import settings
from datetime import datetime, timedelta
import json

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_transcriptions.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        is_verified=True,
        subscription_tier="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def pro_user():
    """Create a pro user"""
    db = TestingSessionLocal()
    user = User(
        email="pro@example.com",
        hashed_password=get_password_hash("TestPassword123"),
        is_verified=True,
        subscription_tier="pro"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Generate auth headers for test user"""
    token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(pro_user):
    """Generate auth headers for pro user"""
    token = create_access_token(data={"sub": pro_user.email, "user_id": pro_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_transcription(test_user):
    """Create a sample transcription"""
    db = TestingSessionLocal()
    transcription = Transcription(
        user_id=test_user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="uploads/test/sample.mp3",
        status=TranscriptionStatus.COMPLETED,
        duration=45.5,
        notation_data=json.dumps({
            "notes": [{"pitch": "C4", "duration": 0.5}],
            "tempo": 120,
            "key": "C major"
        })
    )
    db.add(transcription)
    db.commit()
    db.refresh(transcription)
    db.close()
    return transcription


class TestCreateTranscription:
    """Tests for POST /api/transcriptions endpoint"""
    
    def test_create_transcription_success(self, test_user, auth_headers, monkeypatch):
        """Test successful transcription creation"""
        # Mock storage service to avoid actual file operations
        def mock_get_file(file_key):
            return b"fake audio data"
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        
        # Mock Celery task
        class MockTask:
            id = "test-job-id-123"
        
        def mock_apply_async(*args, **kwargs):
            return MockTask()
        
        from app.tasks import transcription
        monkeypatch.setattr(transcription.process_transcription, "apply_async", mock_apply_async)
        
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio.mp3",
                "instrument_type": "guitar",
                "title": "My Song",
                "melody_only": False,
                "polyphonic": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "transcription_id" in data
        assert data["job_id"] == "test-job-id-123"
        assert data["status"] == "queued"
        assert "30s" in data["message"]  # Free tier limit
    
    def test_create_transcription_pro_user(self, pro_user, pro_auth_headers, monkeypatch):
        """Test transcription creation for pro user"""
        # Mock storage service
        def mock_get_file(file_key):
            return b"fake audio data"
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        
        # Mock Celery task
        class MockTask:
            id = "pro-job-id-456"
        
        def mock_apply_async(*args, **kwargs):
            return MockTask()
        
        from app.tasks import transcription
        monkeypatch.setattr(transcription.process_transcription_priority, "apply_async", mock_apply_async)
        
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio.mp3",
                "instrument_type": "piano",
                "title": "Pro Song",
                "melody_only": True,
                "polyphonic": True
            },
            headers=pro_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == "pro-job-id-456"
        assert "900s" in data["message"]  # Pro tier limit
    
    def test_create_transcription_invalid_instrument(self, auth_headers, monkeypatch):
        """Test transcription creation with invalid instrument type"""
        # Mock storage service
        def mock_get_file(file_key):
            return b"fake audio data"
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio.mp3",
                "instrument_type": "invalid_instrument",
                "title": "Test Song"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Invalid instrument type" in response.json()["detail"]
    
    def test_create_transcription_file_not_found(self, auth_headers, monkeypatch):
        """Test transcription creation with non-existent audio file"""
        # Mock storage service to raise exception
        def mock_get_file(file_key):
            raise Exception("File not found")
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/nonexistent.mp3",
                "instrument_type": "guitar",
                "title": "Test Song"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Audio file not found" in response.json()["detail"]
    
    def test_create_transcription_daily_limit_exceeded(self, test_user, auth_headers, monkeypatch):
        """Test daily transcription limit for free users"""
        # Mock storage service
        def mock_get_file(file_key):
            return b"fake audio data"
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        
        # Mock Celery task
        class MockTask:
            id = "test-job-id"
        
        def mock_apply_async(*args, **kwargs):
            return MockTask()
        
        from app.tasks import transcription
        monkeypatch.setattr(transcription.process_transcription, "apply_async", mock_apply_async)
        
        # Create 3 transcriptions (free tier limit)
        db = TestingSessionLocal()
        for i in range(3):
            t = Transcription(
                user_id=test_user.id,
                title=f"Song {i}",
                instrument_type=InstrumentType.GUITAR,
                audio_url=f"uploads/test/audio{i}.mp3",
                status=TranscriptionStatus.COMPLETED
            )
            db.add(t)
        db.commit()
        db.close()
        
        # Try to create 4th transcription
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio.mp3",
                "instrument_type": "guitar",
                "title": "Fourth Song"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 429
        assert "Daily transcription limit reached" in response.json()["detail"]
    
    def test_create_transcription_unauthorized(self):
        """Test transcription creation without authentication"""
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio.mp3",
                "instrument_type": "guitar",
                "title": "Test Song"
            }
        )
        
        assert response.status_code == 401


class TestGetTranscription:
    """Tests for GET /api/transcriptions/{id} endpoint"""
    
    def test_get_transcription_success(self, sample_transcription, auth_headers):
        """Test successful transcription retrieval"""
        response = client.get(
            f"/api/transcriptions/{sample_transcription.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_transcription.id
        assert data["title"] == "Test Song"
        assert data["instrument_type"] == "guitar"
        assert data["status"] == "completed"
        assert data["duration"] == 45.5
        assert data["notation_data"] is not None
        assert data["notation_data"]["tempo"] == 120
    
    def test_get_transcription_not_found(self, auth_headers):
        """Test retrieval of non-existent transcription"""
        response = client.get(
            "/api/transcriptions/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_transcription_access_denied(self, sample_transcription, pro_auth_headers):
        """Test access to another user's transcription"""
        response = client.get(
            f"/api/transcriptions/{sample_transcription.id}",
            headers=pro_auth_headers
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_get_transcription_unauthorized(self, sample_transcription):
        """Test transcription retrieval without authentication"""
        response = client.get(f"/api/transcriptions/{sample_transcription.id}")
        
        assert response.status_code == 401


class TestListTranscriptions:
    """Tests for GET /api/transcriptions endpoint"""
    
    def test_list_transcriptions_success(self, test_user, auth_headers):
        """Test successful transcription listing"""
        # Create multiple transcriptions
        db = TestingSessionLocal()
        for i in range(5):
            t = Transcription(
                user_id=test_user.id,
                title=f"Song {i}",
                instrument_type=InstrumentType.GUITAR if i % 2 == 0 else InstrumentType.PIANO,
                audio_url=f"uploads/test/audio{i}.mp3",
                status=TranscriptionStatus.COMPLETED,
                duration=30.0 + i
            )
            db.add(t)
        db.commit()
        db.close()
        
        response = client.get("/api/transcriptions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["transcriptions"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1
    
    def test_list_transcriptions_pagination(self, test_user, auth_headers):
        """Test transcription listing with pagination"""
        # Create 25 transcriptions
        db = TestingSessionLocal()
        for i in range(25):
            t = Transcription(
                user_id=test_user.id,
                title=f"Song {i}",
                instrument_type=InstrumentType.GUITAR,
                audio_url=f"uploads/test/audio{i}.mp3",
                status=TranscriptionStatus.COMPLETED
            )
            db.add(t)
        db.commit()
        db.close()
        
        # Get first page
        response = client.get("/api/transcriptions?page=1&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["transcriptions"]) == 10
        assert data["page"] == 1
        assert data["total_pages"] == 3
        
        # Get second page
        response = client.get("/api/transcriptions?page=2&page_size=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["transcriptions"]) == 10
        assert data["page"] == 2
    
    def test_list_transcriptions_filter_by_instrument(self, test_user, auth_headers):
        """Test transcription listing with instrument filter"""
        # Create transcriptions with different instruments
        db = TestingSessionLocal()
        for i in range(3):
            t = Transcription(
                user_id=test_user.id,
                title=f"Guitar Song {i}",
                instrument_type=InstrumentType.GUITAR,
                audio_url=f"uploads/test/guitar{i}.mp3",
                status=TranscriptionStatus.COMPLETED
            )
            db.add(t)
        for i in range(2):
            t = Transcription(
                user_id=test_user.id,
                title=f"Piano Song {i}",
                instrument_type=InstrumentType.PIANO,
                audio_url=f"uploads/test/piano{i}.mp3",
                status=TranscriptionStatus.COMPLETED
            )
            db.add(t)
        db.commit()
        db.close()
        
        # Filter by guitar
        response = client.get("/api/transcriptions?instrument_type=guitar", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(t["instrument_type"] == "guitar" for t in data["transcriptions"])
        
        # Filter by piano
        response = client.get("/api/transcriptions?instrument_type=piano", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(t["instrument_type"] == "piano" for t in data["transcriptions"])
    
    def test_list_transcriptions_search_by_title(self, test_user, auth_headers):
        """Test transcription listing with title search"""
        # Create transcriptions with different titles
        db = TestingSessionLocal()
        titles = ["Stairway to Heaven", "Hotel California", "Bohemian Rhapsody", "Sweet Child O' Mine"]
        for title in titles:
            t = Transcription(
                user_id=test_user.id,
                title=title,
                instrument_type=InstrumentType.GUITAR,
                audio_url=f"uploads/test/{title}.mp3",
                status=TranscriptionStatus.COMPLETED
            )
            db.add(t)
        db.commit()
        db.close()
        
        # Search for "heaven"
        response = client.get("/api/transcriptions?search=heaven", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Heaven" in data["transcriptions"][0]["title"]
        
        # Search for "child"
        response = client.get("/api/transcriptions?search=child", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Child" in data["transcriptions"][0]["title"]
    
    def test_list_transcriptions_empty(self, auth_headers):
        """Test transcription listing with no transcriptions"""
        response = client.get("/api/transcriptions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["transcriptions"]) == 0
    
    def test_list_transcriptions_unauthorized(self):
        """Test transcription listing without authentication"""
        response = client.get("/api/transcriptions")
        
        assert response.status_code == 401


class TestDeleteTranscription:
    """Tests for DELETE /api/transcriptions/{id} endpoint"""
    
    def test_delete_transcription_success(self, sample_transcription, auth_headers, monkeypatch):
        """Test successful transcription deletion"""
        # Mock storage service
        deleted_files = []
        
        def mock_delete_file(file_key):
            deleted_files.append(file_key)
            return True
        
        from app.services import storage
        monkeypatch.setattr(storage.storage_service, "delete_file", mock_delete_file)
        
        import json
        response = client.request(
            "DELETE",
            f"/api/transcriptions/{sample_transcription.id}",
            content=json.dumps({"confirmation_token": str(sample_transcription.id)}),
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
        assert sample_transcription.audio_url in deleted_files
        
        # Verify transcription is deleted from database
        db = TestingSessionLocal()
        t = db.query(Transcription).filter(Transcription.id == sample_transcription.id).first()
        assert t is None
        db.close()
    
    def test_delete_transcription_invalid_token(self, sample_transcription, auth_headers):
        """Test transcription deletion with invalid confirmation token"""
        import json
        response = client.request(
            "DELETE",
            f"/api/transcriptions/{sample_transcription.id}",
            content=json.dumps({"confirmation_token": "wrong_token"}),
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        assert "Invalid confirmation token" in response.json()["detail"]
    
    def test_delete_transcription_not_found(self, auth_headers):
        """Test deletion of non-existent transcription"""
        import json
        response = client.request(
            "DELETE",
            "/api/transcriptions/99999",
            content=json.dumps({"confirmation_token": "99999"}),
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_transcription_access_denied(self, sample_transcription, pro_auth_headers):
        """Test deletion of another user's transcription"""
        import json
        response = client.request(
            "DELETE",
            f"/api/transcriptions/{sample_transcription.id}",
            content=json.dumps({"confirmation_token": str(sample_transcription.id)}),
            headers={**pro_auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_delete_transcription_unauthorized(self, sample_transcription):
        """Test transcription deletion without authentication"""
        import json
        response = client.request(
            "DELETE",
            f"/api/transcriptions/{sample_transcription.id}",
            content=json.dumps({"confirmation_token": str(sample_transcription.id)}),
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 401


class TestAuthorizationAndTierLimits:
    """Integration tests for authorization and tier limits"""
    
    def test_free_user_cannot_exceed_daily_limit(self, test_user, auth_headers, monkeypatch):
        """Test that free users are limited to 3 transcriptions per day"""
        # Mock storage and celery
        def mock_get_file(file_key):
            return b"fake audio data"
        
        class MockTask:
            id = "test-job-id"
        
        def mock_apply_async(*args, **kwargs):
            return MockTask()
        
        from app.services import storage
        from app.tasks import transcription
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        monkeypatch.setattr(transcription.process_transcription, "apply_async", mock_apply_async)
        
        # Create 3 transcriptions successfully
        for i in range(3):
            response = client.post(
                "/api/transcriptions",
                json={
                    "audio_file_key": f"uploads/test/audio{i}.mp3",
                    "instrument_type": "guitar",
                    "title": f"Song {i}"
                },
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # 4th attempt should fail
        response = client.post(
            "/api/transcriptions",
            json={
                "audio_file_key": "uploads/test/audio3.mp3",
                "instrument_type": "guitar",
                "title": "Song 3"
            },
            headers=auth_headers
        )
        assert response.status_code == 429
    
    def test_pro_user_unlimited_transcriptions(self, pro_user, pro_auth_headers, monkeypatch):
        """Test that pro users have unlimited transcriptions"""
        # Mock storage and celery
        def mock_get_file(file_key):
            return b"fake audio data"
        
        class MockTask:
            id = "test-job-id"
        
        def mock_apply_async(*args, **kwargs):
            return MockTask()
        
        from app.services import storage
        from app.tasks import transcription
        monkeypatch.setattr(storage.storage_service, "get_file", mock_get_file)
        monkeypatch.setattr(transcription.process_transcription_priority, "apply_async", mock_apply_async)
        
        # Create 10 transcriptions (more than free tier limit)
        for i in range(10):
            response = client.post(
                "/api/transcriptions",
                json={
                    "audio_file_key": f"uploads/test/audio{i}.mp3",
                    "instrument_type": "piano",
                    "title": f"Pro Song {i}"
                },
                headers=pro_auth_headers
            )
            assert response.status_code == 201
    
    def test_user_can_only_access_own_transcriptions(self, test_user, pro_user, auth_headers, pro_auth_headers):
        """Test that users can only access their own transcriptions"""
        # Create transcription for test_user
        db = TestingSessionLocal()
        t1 = Transcription(
            user_id=test_user.id,
            title="User 1 Song",
            instrument_type=InstrumentType.GUITAR,
            audio_url="uploads/test/user1.mp3",
            status=TranscriptionStatus.COMPLETED
        )
        db.add(t1)
        db.commit()
        db.refresh(t1)
        t1_id = t1.id
        
        # Create transcription for pro_user
        t2 = Transcription(
            user_id=pro_user.id,
            title="User 2 Song",
            instrument_type=InstrumentType.PIANO,
            audio_url="uploads/test/user2.mp3",
            status=TranscriptionStatus.COMPLETED
        )
        db.add(t2)
        db.commit()
        db.refresh(t2)
        t2_id = t2.id
        db.close()
        
        # test_user can access their own
        response = client.get(f"/api/transcriptions/{t1_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # test_user cannot access pro_user's
        response = client.get(f"/api/transcriptions/{t2_id}", headers=auth_headers)
        assert response.status_code == 403
        
        # pro_user can access their own
        response = client.get(f"/api/transcriptions/{t2_id}", headers=pro_auth_headers)
        assert response.status_code == 200
        
        # pro_user cannot access test_user's
        response = client.get(f"/api/transcriptions/{t1_id}", headers=pro_auth_headers)
        assert response.status_code == 403
