"""
Unit tests for subscription management.

Tests subscription status, upgrades, webhooks, and priority queue routing.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.database import Base, get_db
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription, PaymentStatus
from app.services.auth import get_password_hash
import json

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_subscriptions.db"
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
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        subscription_tier=SubscriptionTier.FREE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_pro_user():
    """Create a test Pro user"""
    db = TestingSessionLocal()
    user = User(
        email="pro@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_verified=True,
        subscription_tier=SubscriptionTier.PRO
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id  # Store ID before closing session
    
    # Create subscription
    subscription = Subscription(
        user_id=user_id,
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(subscription)
    db.commit()
    db.close()
    
    # Return a dict instead of the detached object
    return {"id": user_id, "email": "pro@example.com"}


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(test_pro_user):
    """Get authentication headers for Pro user"""
    response = client.post(
        "/api/auth/login",
        json={"email": "pro@example.com", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSubscriptionStatus:
    """Test subscription status endpoint"""
    
    def test_get_subscription_status_free_user(self, test_user, auth_headers):
        """Free user can get subscription status"""
        response = client.get("/api/subscriptions/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        assert data["payment_status"] == "active"
        assert data["is_active"] is True
        assert data["days_remaining"] is None
    
    def test_get_subscription_status_pro_user(self, test_pro_user, pro_auth_headers):
        """Pro user can get subscription status"""
        response = client.get("/api/subscriptions/status", headers=pro_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["payment_status"] == "active"
        assert data["is_active"] is True
        assert data["days_remaining"] is not None
        assert data["days_remaining"] > 0
    
    def test_get_subscription_status_unauthenticated(self):
        """Unauthenticated user cannot get subscription status"""
        response = client.get("/api/subscriptions/status")
        assert response.status_code == 401
    
    def test_get_subscription_status_creates_default(self, test_user, auth_headers):
        """Status endpoint creates default subscription if none exists"""
        # Delete any existing subscription
        db = TestingSessionLocal()
        db.query(Subscription).filter(Subscription.user_id == test_user.id).delete()
        db.commit()
        db.close()
        
        response = client.get("/api/subscriptions/status", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "free"
        
        # Verify subscription was created
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.user_id == test_user.id).first()
        assert subscription is not None
        assert subscription.tier == SubscriptionTier.FREE
        db.close()


class TestSubscriptionUpgrade:
    """Test subscription upgrade endpoint"""
    
    def test_upgrade_to_pro_success(self, test_user, auth_headers):
        """User can upgrade to Pro subscription"""
        response = client.post(
            "/api/subscriptions/upgrade",
            headers=auth_headers,
            json={"payment_method_id": "pm_test_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"
        assert data["payment_status"] == "active"
        assert "expires_at" in data
        assert "Successfully upgraded" in data["message"]
        
        # Verify database was updated
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == test_user.id).first()
        assert user.subscription_tier == SubscriptionTier.PRO
        
        subscription = db.query(Subscription).filter(Subscription.user_id == test_user.id).first()
        assert subscription.tier == SubscriptionTier.PRO
        assert subscription.payment_status == PaymentStatus.ACTIVE
        assert subscription.expires_at is not None
        db.close()
    
    def test_upgrade_already_pro(self, test_pro_user, pro_auth_headers):
        """Already Pro user cannot upgrade again"""
        response = client.post(
            "/api/subscriptions/upgrade",
            headers=pro_auth_headers,
            json={"payment_method_id": "pm_test_123"}
        )
        
        assert response.status_code == 400
        assert "already has an active Pro subscription" in response.json()["detail"]
    
    def test_upgrade_unauthenticated(self):
        """Unauthenticated user cannot upgrade"""
        response = client.post(
            "/api/subscriptions/upgrade",
            json={"payment_method_id": "pm_test_123"}
        )
        assert response.status_code == 401
    
    def test_upgrade_with_billing_email(self, test_user, auth_headers):
        """User can upgrade with custom billing email"""
        response = client.post(
            "/api/subscriptions/upgrade",
            headers=auth_headers,
            json={
                "payment_method_id": "pm_test_123",
                "billing_email": "billing@example.com"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "pro"


class TestPaymentWebhook:
    """Test payment webhook endpoint"""
    
    def test_webhook_payment_success(self, test_pro_user):
        """Webhook processes payment success event"""
        user_id = test_pro_user["id"]
        
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        subscription_id = subscription.id
        
        # Set expiration to past
        subscription.expires_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        db.close()
        
        webhook_data = {
            "event_type": "payment.success",
            "user_id": user_id,
            "subscription_id": subscription_id,
            "payment_id": "pay_123",
            "amount": 29.99,
            "currency": "USD",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = client.post(
            "/api/subscriptions/webhook",
            json=webhook_data,
            headers={"X-Webhook-Signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was extended
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        assert subscription.payment_status == PaymentStatus.ACTIVE
        assert subscription.expires_at > datetime.utcnow()
        db.close()
    
    def test_webhook_payment_failed(self, test_pro_user):
        """Webhook processes payment failed event"""
        user_id = test_pro_user["id"]
        
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        subscription_id = subscription.id
        db.close()
        
        webhook_data = {
            "event_type": "payment.failed",
            "user_id": user_id,
            "subscription_id": subscription_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = client.post(
            "/api/subscriptions/webhook",
            json=webhook_data,
            headers={"X-Webhook-Signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription status changed
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        assert subscription.payment_status == PaymentStatus.PENDING
        db.close()
    
    def test_webhook_subscription_cancelled(self, test_pro_user):
        """Webhook processes subscription cancelled event"""
        user_id = test_pro_user["id"]
        
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        subscription_id = subscription.id
        db.close()
        
        webhook_data = {
            "event_type": "subscription.cancelled",
            "user_id": user_id,
            "subscription_id": subscription_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = client.post(
            "/api/subscriptions/webhook",
            json=webhook_data,
            headers={"X-Webhook-Signature": "test_signature"}
        )
        
        assert response.status_code == 200
        
        # Verify subscription was cancelled
        db = TestingSessionLocal()
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        assert subscription.payment_status == PaymentStatus.CANCELLED
        assert subscription.tier == SubscriptionTier.FREE
        
        # Verify user tier was downgraded
        user = db.query(User).filter(User.id == user_id).first()
        assert user.subscription_tier == SubscriptionTier.FREE
        db.close()
    
    def test_webhook_subscription_not_found(self):
        """Webhook returns 404 for non-existent subscription"""
        webhook_data = {
            "event_type": "payment.success",
            "user_id": 999,
            "subscription_id": 999,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = client.post(
            "/api/subscriptions/webhook",
            json=webhook_data,
            headers={"X-Webhook-Signature": "test_signature"}
        )
        
        assert response.status_code == 404
    
    def test_webhook_invalid_data(self):
        """Webhook returns 400 for invalid data"""
        response = client.post(
            "/api/subscriptions/webhook",
            json={"invalid": "data"},
            headers={"X-Webhook-Signature": "test_signature"}
        )
        
        assert response.status_code == 400


class TestSubscriptionTierEnforcement:
    """Test subscription tier enforcement in other endpoints"""
    
    def test_export_format_restriction_free_user(self, test_user, auth_headers):
        """Free users cannot export in Pro formats"""
        from app.services.export_service import export_service
        
        # Test MusicXML (Pro only)
        is_valid, error = export_service.validate_format("musicxml", "free")
        assert is_valid is False
        assert "Pro users" in error
        
        # Test MIDI (Pro only)
        is_valid, error = export_service.validate_format("midi", "free")
        assert is_valid is False
        
        # Test PDF (free tier)
        is_valid, error = export_service.validate_format("pdf", "free")
        assert is_valid is True
    
    def test_export_format_access_pro_user(self, test_pro_user):
        """Pro users can export in all formats"""
        from app.services.export_service import export_service
        
        formats = ["pdf", "musicxml", "midi", "gpx", "gp5"]
        for fmt in formats:
            is_valid, error = export_service.validate_format(fmt, "pro")
            assert is_valid is True, f"Pro user should access {fmt} format"


class TestPriorityQueue:
    """Test priority queue routing for Pro users"""
    
    def test_pro_user_uses_priority_queue(self):
        """Pro users should use priority transcription task"""
        from app.tasks.transcription import process_transcription_priority
        
        # Verify priority task exists
        assert process_transcription_priority is not None
        assert process_transcription_priority.name == "app.tasks.transcription.process_transcription_priority"
    
    def test_celery_routing_configuration(self):
        """Verify Celery routing configuration for priority queue"""
        from app.celery_app import celery_app
        
        # Check task routes
        routes = celery_app.conf.task_routes
        assert "app.tasks.transcription.process_transcription" in routes
        assert "app.tasks.transcription.process_transcription_priority" in routes
        
        # Verify priority queue exists
        priority_route = routes["app.tasks.transcription.process_transcription_priority"]
        assert priority_route["queue"] == "transcription_priority"
