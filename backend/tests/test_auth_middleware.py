import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import os

# Set test environment variables before importing app
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_ACCESS_KEY": "test",
    "S3_SECRET_KEY": "test",
    "S3_BUCKET_NAME": "test",
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "SMTP_HOST": "smtp.test.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "test@test.com",
    "SMTP_PASSWORD": "test",
    "FROM_EMAIL": "noreply@test.com",
    "ENVIRONMENT": "test",
    "DEBUG": "True",
    "ALLOWED_ORIGINS": "http://localhost:5173",
    "FRONTEND_URL": "http://localhost:5173",
    "MAX_UPLOAD_SIZE_MB": "100",
    "ALLOWED_AUDIO_FORMATS": "mp3,wav,flac,ogg,m4a,aac",
    "ALLOWED_VIDEO_FORMATS": "mp4,avi,mov,webm",
    "FREE_TIER_MAX_DURATION_SECONDS": "30",
    "FREE_TIER_MAX_TRANSCRIPTIONS_PER_DAY": "3",
    "PRO_TIER_MAX_DURATION_SECONDS": "900",
    "YOUTUBE_MAX_DURATION_SECONDS": "900",
})

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.services.auth import create_access_token, create_refresh_token
from fastapi import Depends, APIRouter
from app.middleware.auth import get_current_user, get_current_active_user, get_optional_user

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test router to test middleware
test_router = APIRouter(prefix="/api/test", tags=["test"])


@test_router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    """Test endpoint that requires authentication."""
    return {"email": current_user.email, "id": current_user.id}


@test_router.get("/verified-only")
async def verified_only_route(current_user: User = Depends(get_current_active_user)):
    """Test endpoint that requires verified user."""
    return {"email": current_user.email, "verified": current_user.is_verified}


@test_router.get("/optional-auth")
async def optional_auth_route(current_user: User = Depends(get_optional_user)):
    """Test endpoint with optional authentication."""
    if current_user:
        return {"authenticated": True, "email": current_user.email}
    return {"authenticated": False}


app.include_router(test_router)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    from app.services.rate_limiter import rate_limit_storage
    rate_limit_storage.clear()
    yield
    Base.metadata.drop_all(bind=engine)
    rate_limit_storage.clear()


@pytest.fixture
def mock_email():
    """Mock email sending to avoid actual SMTP calls."""
    with patch('app.services.email.send_email', return_value=True):
        yield


@pytest.fixture
def test_user(mock_email):
    """Create a test user and return credentials."""
    # Register user
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    assert response.status_code == 201
    
    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test1234"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    return {
        "email": "test@example.com",
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"]
    }


class TestAuthenticationMiddleware:
    """Test JWT authentication middleware."""
    
    def test_protected_route_without_token(self):
        """Test accessing protected route without token."""
        response = client.get("/api/test/protected")
        assert response.status_code == 401  # HTTPBearer returns 401 when no credentials
    
    def test_protected_route_with_invalid_token(self):
        """Test accessing protected route with invalid token."""
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_protected_route_with_valid_token(self, test_user):
        """Test accessing protected route with valid token."""
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert "id" in data
    
    def test_verified_only_route_unverified_user(self, test_user):
        """Test accessing verified-only route with unverified user."""
        response = client.get(
            "/api/test/verified-only",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 403
        assert "Email not verified" in response.json()["detail"]
    
    def test_optional_auth_without_token(self):
        """Test optional auth route without token."""
        response = client.get("/api/test/optional-auth")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
    
    def test_optional_auth_with_token(self, test_user):
        """Test optional auth route with valid token."""
        response = client.get(
            "/api/test/optional-auth",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["email"] == test_user["email"]
    
    def test_optional_auth_with_invalid_token(self):
        """Test optional auth route with invalid token returns unauthenticated."""
        response = client.get(
            "/api/test/optional-auth",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False


class TestTokenRefresh:
    """Test token refresh mechanism."""
    
    def test_refresh_token_success(self, test_user):
        """Test successful token refresh."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": test_user["refresh_token"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        
        # Verify new access token works
        protected_response = client.get(
            "/api/test/protected",
            headers={"Authorization": f"Bearer {data['access_token']}"}
        )
        assert protected_response.status_code == 200
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]
    
    def test_refresh_token_wrong_type(self, test_user):
        """Test refresh with access token instead of refresh token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": test_user["access_token"]}
        )
        assert response.status_code == 401
        # Access tokens don't have type field, so they're invalid
    
    def test_login_returns_refresh_token(self, mock_email):
        """Test that login returns both access and refresh tokens."""
        # Register user
        client.post(
            "/api/auth/register",
            json={
                "email": "refresh_test@example.com",
                "password": "Test1234"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "refresh_test@example.com",
                "password": "Test1234"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestUserContextInjection:
    """Test that user context is properly injected into requests."""
    
    def test_user_context_contains_all_fields(self, test_user):
        """Test that injected user context contains all necessary fields."""
        response = client.get(
            "/api/test/protected",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify user data is accessible
        assert "email" in data
        assert "id" in data
        assert data["email"] == test_user["email"]
