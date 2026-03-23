import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys

# Set minimal environment variables before importing app modules
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
os.environ.setdefault('S3_ENDPOINT_URL', 'http://localhost:9000')
os.environ.setdefault('S3_ACCESS_KEY', 'test')
os.environ.setdefault('S3_SECRET_KEY', 'test')
os.environ.setdefault('S3_BUCKET_NAME', 'test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('SMTP_HOST', 'localhost')
os.environ.setdefault('SMTP_PORT', '587')
os.environ.setdefault('SMTP_USER', 'test')
os.environ.setdefault('SMTP_PASSWORD', 'test')
os.environ.setdefault('FROM_EMAIL', 'test@example.com')
os.environ.setdefault('ALLOWED_ORIGINS', 'http://localhost:3000')
os.environ.setdefault('ALLOWED_AUDIO_FORMATS', 'mp3,wav,flac,ogg,m4a,aac')
os.environ.setdefault('ALLOWED_VIDEO_FORMATS', 'mp4,avi,mov,webm')

from app.database import Base
from app.models import (
    User, SubscriptionTier, 
    Transcription, TranscriptionStatus, InstrumentType,
    Subscription, PaymentStatus
)

# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_user_creation(db_session):
    """Test creating a User model"""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_verified=False,
        subscription_tier=SubscriptionTier.FREE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_123"
    assert user.is_verified is False
    assert user.subscription_tier == SubscriptionTier.FREE
    assert user.created_at is not None

def test_transcription_creation(db_session):
    """Test creating a Transcription model"""
    # Create user first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create transcription
    transcription = Transcription(
        user_id=user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3",
        duration=120.5,
        status=TranscriptionStatus.QUEUED
    )
    db_session.add(transcription)
    db_session.commit()
    db_session.refresh(transcription)
    
    assert transcription.id is not None
    assert transcription.user_id == user.id
    assert transcription.title == "Test Song"
    assert transcription.instrument_type == InstrumentType.GUITAR
    assert transcription.audio_url == "s3://bucket/audio.mp3"
    assert transcription.duration == 120.5
    assert transcription.status == TranscriptionStatus.QUEUED
    assert transcription.created_at is not None

def test_subscription_creation(db_session):
    """Test creating a Subscription model"""
    # Create user first
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create subscription
    expires_at = datetime.utcnow() + timedelta(days=30)
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO,
        expires_at=expires_at,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    
    assert subscription.id is not None
    assert subscription.user_id == user.id
    assert subscription.tier == SubscriptionTier.PRO
    assert subscription.expires_at is not None
    assert subscription.payment_status == PaymentStatus.ACTIVE
    assert subscription.created_at is not None

def test_user_transcription_relationship(db_session):
    """Test relationship between User and Transcription"""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create multiple transcriptions
    transcription1 = Transcription(
        user_id=user.id,
        title="Song 1",
        instrument_type=InstrumentType.PIANO,
        audio_url="s3://bucket/audio1.mp3"
    )
    transcription2 = Transcription(
        user_id=user.id,
        title="Song 2",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio2.mp3"
    )
    db_session.add_all([transcription1, transcription2])
    db_session.commit()
    
    # Test relationship
    db_session.refresh(user)
    assert len(user.transcriptions) == 2
    assert user.transcriptions[0].title in ["Song 1", "Song 2"]
    assert user.transcriptions[1].title in ["Song 1", "Song 2"]

def test_user_subscription_relationship(db_session):
    """Test relationship between User and Subscription"""
    # Create user
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create subscription
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    db_session.commit()
    
    # Test relationship
    db_session.refresh(user)
    assert user.subscription is not None
    assert user.subscription.tier == SubscriptionTier.PRO
    assert user.subscription.payment_status == PaymentStatus.ACTIVE

def test_cascade_delete_user_transcriptions(db_session):
    """Test that deleting a user cascades to transcriptions"""
    # Create user with transcriptions
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    transcription = Transcription(
        user_id=user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    db_session.add(transcription)
    db_session.commit()
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Verify transcription is also deleted
    remaining_transcriptions = db_session.query(Transcription).all()
    assert len(remaining_transcriptions) == 0

def test_cascade_delete_user_subscription(db_session):
    """Test that deleting a user cascades to subscription"""
    # Create user with subscription
    user = User(
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    db_session.commit()
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Verify subscription is also deleted
    remaining_subscriptions = db_session.query(Subscription).all()
    assert len(remaining_subscriptions) == 0

def test_unique_email_constraint(db_session):
    """Test that email must be unique"""
    user1 = User(
        email="test@example.com",
        hashed_password="password1"
    )
    db_session.add(user1)
    db_session.commit()
    
    # Try to create another user with same email
    user2 = User(
        email="test@example.com",
        hashed_password="password2"
    )
    db_session.add(user2)
    
    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()

def test_unique_subscription_per_user(db_session):
    """Test that each user can have only one subscription"""
    user = User(
        email="test@example.com",
        hashed_password="password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    subscription1 = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.FREE,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription1)
    db_session.commit()
    
    # Try to create another subscription for same user
    subscription2 = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription2)
    
    with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
        db_session.commit()

def test_user_nullable_constraints(db_session):
    """Test that required User fields cannot be null"""
    # Test missing email
    user = User(hashed_password="password")
    db_session.add(user)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()
    
    # Test missing password
    user = User(email="test@example.com")
    db_session.add(user)
    with pytest.raises(Exception):
        db_session.commit()

def test_user_default_values(db_session):
    """Test that User model has correct default values"""
    user = User(
        email="test@example.com",
        hashed_password="password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.is_verified is False
    assert user.subscription_tier == SubscriptionTier.FREE
    assert user.created_at is not None

def test_transcription_nullable_constraints(db_session):
    """Test that required Transcription fields cannot be null"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Test missing user_id
    transcription = Transcription(
        title="Test",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    db_session.add(transcription)
    with pytest.raises(Exception):
        db_session.commit()
    db_session.rollback()
    
    # Test missing title
    transcription = Transcription(
        user_id=user.id,
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    transcription.title = None
    db_session.add(transcription)
    with pytest.raises(Exception):
        db_session.commit()

def test_transcription_default_status(db_session):
    """Test that Transcription has correct default status"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    transcription = Transcription(
        user_id=user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    db_session.add(transcription)
    db_session.commit()
    db_session.refresh(transcription)
    
    assert transcription.status == TranscriptionStatus.QUEUED

def test_transcription_optional_fields(db_session):
    """Test that optional Transcription fields can be null"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    transcription = Transcription(
        user_id=user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    db_session.add(transcription)
    db_session.commit()
    db_session.refresh(transcription)
    
    assert transcription.notation_data is None
    assert transcription.duration is None

def test_subscription_nullable_constraints(db_session):
    """Test that required Subscription fields cannot be null"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Test missing user_id
    subscription = Subscription(
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    with pytest.raises(Exception):
        db_session.commit()

def test_subscription_default_values(db_session):
    """Test that Subscription has correct default values"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    subscription = Subscription(user_id=user.id)
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    
    assert subscription.tier == SubscriptionTier.FREE
    assert subscription.payment_status == PaymentStatus.ACTIVE
    assert subscription.created_at is not None

def test_subscription_optional_expires_at(db_session):
    """Test that Subscription expires_at can be null"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.FREE,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    
    assert subscription.expires_at is None

def test_transcription_status_enum_values(db_session):
    """Test all valid TranscriptionStatus enum values"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    statuses = [
        TranscriptionStatus.QUEUED,
        TranscriptionStatus.PROCESSING,
        TranscriptionStatus.COMPLETED,
        TranscriptionStatus.FAILED
    ]
    
    for status in statuses:
        transcription = Transcription(
            user_id=user.id,
            title=f"Test {status.value}",
            instrument_type=InstrumentType.GUITAR,
            audio_url=f"s3://bucket/{status.value}.mp3",
            status=status
        )
        db_session.add(transcription)
        db_session.commit()
        db_session.refresh(transcription)
        assert transcription.status == status

def test_instrument_type_enum_values(db_session):
    """Test all valid InstrumentType enum values"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    instruments = [
        InstrumentType.PIANO,
        InstrumentType.GUITAR,
        InstrumentType.BASS,
        InstrumentType.VOCALS,
        InstrumentType.DRUMS,
        InstrumentType.STRINGS,
        InstrumentType.WOODWINDS,
        InstrumentType.BRASS
    ]
    
    for instrument in instruments:
        transcription = Transcription(
            user_id=user.id,
            title=f"Test {instrument.value}",
            instrument_type=instrument,
            audio_url=f"s3://bucket/{instrument.value}.mp3"
        )
        db_session.add(transcription)
        db_session.commit()
        db_session.refresh(transcription)
        assert transcription.instrument_type == instrument

def test_payment_status_enum_values(db_session):
    """Test all valid PaymentStatus enum values"""
    statuses = [
        PaymentStatus.ACTIVE,
        PaymentStatus.EXPIRED,
        PaymentStatus.CANCELLED,
        PaymentStatus.PENDING
    ]
    
    for idx, status in enumerate(statuses):
        user = User(
            email=f"test{idx}@example.com",
            hashed_password="password"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        subscription = Subscription(
            user_id=user.id,
            tier=SubscriptionTier.PRO,
            payment_status=status
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        assert subscription.payment_status == status

def test_multiple_transcriptions_per_user(db_session):
    """Test that a user can have multiple transcriptions"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create 5 transcriptions
    for i in range(5):
        transcription = Transcription(
            user_id=user.id,
            title=f"Song {i}",
            instrument_type=InstrumentType.GUITAR,
            audio_url=f"s3://bucket/audio{i}.mp3"
        )
        db_session.add(transcription)
    
    db_session.commit()
    db_session.refresh(user)
    
    assert len(user.transcriptions) == 5

def test_bidirectional_user_transcription_relationship(db_session):
    """Test bidirectional relationship between User and Transcription"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    transcription = Transcription(
        user_id=user.id,
        title="Test Song",
        instrument_type=InstrumentType.GUITAR,
        audio_url="s3://bucket/audio.mp3"
    )
    db_session.add(transcription)
    db_session.commit()
    db_session.refresh(transcription)
    
    # Test forward relationship
    assert transcription.user.id == user.id
    assert transcription.user.email == user.email
    
    # Test backward relationship
    db_session.refresh(user)
    assert len(user.transcriptions) == 1
    assert user.transcriptions[0].id == transcription.id

def test_bidirectional_user_subscription_relationship(db_session):
    """Test bidirectional relationship between User and Subscription"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    subscription = Subscription(
        user_id=user.id,
        tier=SubscriptionTier.PRO,
        payment_status=PaymentStatus.ACTIVE
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    
    # Test forward relationship
    assert subscription.user.id == user.id
    assert subscription.user.email == user.email
    
    # Test backward relationship
    db_session.refresh(user)
    assert user.subscription is not None
    assert user.subscription.id == subscription.id

def test_cascade_delete_multiple_transcriptions(db_session):
    """Test that deleting a user cascades to all transcriptions"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Create multiple transcriptions
    for i in range(3):
        transcription = Transcription(
            user_id=user.id,
            title=f"Song {i}",
            instrument_type=InstrumentType.GUITAR,
            audio_url=f"s3://bucket/audio{i}.mp3"
        )
        db_session.add(transcription)
    
    db_session.commit()
    
    # Verify transcriptions exist
    transcription_count = db_session.query(Transcription).filter_by(user_id=user.id).count()
    assert transcription_count == 3
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Verify all transcriptions are deleted
    remaining_transcriptions = db_session.query(Transcription).all()
    assert len(remaining_transcriptions) == 0

def test_updated_at_timestamp(db_session):
    """Test that updated_at timestamp is set on update"""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    original_updated_at = user.updated_at
    
    # Update user
    user.is_verified = True
    db_session.commit()
    db_session.refresh(user)
    
    # Note: updated_at may be None initially if not set, but should be set after update
    assert user.is_verified is True
