"""
Integration tests for authentication flow.
Tests the complete user journey from registration to password reset.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
import os

# Set test environment variables before importing app
os.environ.update({
    "DATABASE_URL": "sqlite:///./test_integration.db",
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_ACCESS_KEY": "test",
    "S3_SECRET_KEY": "test",
    "S3_BUCKET_NAME": "test",
    "SECRET_KEY": "test-secret-key-for-integration-testing",
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
from app.database import Base, get_db, engine as app_engine
from app.models.user import User

# Use the same engine that the app is using
engine = app_engine
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    # Clear rate limiter storage between tests
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


def test_complete_authentication_flow(mock_email):
    """Test the complete authentication flow from registration to login."""
    
    # Step 1: Register a new user
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "integration@test.com",
            "password": "TestPass123"
        }
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == "integration@test.com"
    assert user_data["is_verified"] is False
    
    # Step 2: Verify email
    from app.services.auth import create_verification_token
    verification_token = create_verification_token("integration@test.com")
    
    verify_response = client.post(
        "/api/auth/verify-email",
        json={"token": verification_token}
    )
    assert verify_response.status_code == 200
    assert "verified successfully" in verify_response.json()["message"]
    
    # Step 3: Login with verified account
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "integration@test.com",
            "password": "TestPass123"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Step 4: Request password reset
    reset_request_response = client.post(
        "/api/auth/request-password-reset",
        json={"email": "integration@test.com"}
    )
    assert reset_request_response.status_code == 200
    
    # Step 5: Reset password
    from app.services.auth import create_password_reset_token
    reset_token = create_password_reset_token("integration@test.com")
    
    reset_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": reset_token,
            "new_password": "NewTestPass456"
        }
    )
    assert reset_response.status_code == 200
    assert "reset successfully" in reset_response.json()["message"]
    
    # Step 6: Login with new password
    new_login_response = client.post(
        "/api/auth/login",
        json={
            "email": "integration@test.com",
            "password": "NewTestPass456"
        }
    )
    assert new_login_response.status_code == 200
    new_token_data = new_login_response.json()
    assert "access_token" in new_token_data
    
    # Step 7: Verify old password no longer works
    old_login_response = client.post(
        "/api/auth/login",
        json={
            "email": "integration@test.com",
            "password": "TestPass123"
        }
    )
    assert old_login_response.status_code == 401


def test_rate_limiting_across_endpoints(mock_email):
    """Test that rate limiting works across different authentication endpoints."""
    
    # Register a user first (this counts as 1 attempt)
    client.post(
        "/api/auth/register",
        json={
            "email": "ratelimit@test.com",
            "password": "TestPass123"
        }
    )
    
    # Make 4 more failed login attempts (total 5 with registration)
    for i in range(4):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "ratelimit@test.com",
                "password": "WrongPassword1"
            }
        )
        # All attempts should return 401 (invalid credentials)
        assert response.status_code == 401
    
    # 6th attempt should be rate limited
    response = client.post(
        "/api/auth/login",
        json={
            "email": "ratelimit@test.com",
            "password": "WrongPassword1"
        }
    )
    assert response.status_code == 429
    assert "Too many attempts" in response.json()["detail"]


def test_security_no_user_enumeration(mock_email):
    """Test that the API doesn't reveal whether users exist."""
    
    # Register a user
    client.post(
        "/api/auth/register",
        json={
            "email": "exists@test.com",
            "password": "TestPass123"
        }
    )
    
    # Try to login with non-existent user
    response1 = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "TestPass123"
        }
    )
    
    # Try to login with existing user but wrong password
    response2 = client.post(
        "/api/auth/login",
        json={
            "email": "exists@test.com",
            "password": "WrongPassword1"
        }
    )
    
    # Both should return the same generic error
    assert response1.status_code == 401
    assert response2.status_code == 401
    assert response1.json()["detail"] == response2.json()["detail"]
    assert response1.json()["detail"] == "Invalid credentials"
    
    # Password reset should also not reveal user existence
    reset1 = client.post(
        "/api/auth/request-password-reset",
        json={"email": "exists@test.com"}
    )
    reset2 = client.post(
        "/api/auth/request-password-reset",
        json={"email": "nonexistent@test.com"}
    )
    
    # Both should return success
    assert reset1.status_code == 200
    assert reset2.status_code == 200
    assert reset1.json()["message"] == reset2.json()["message"]
