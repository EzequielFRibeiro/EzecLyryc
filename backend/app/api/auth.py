from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister, UserLogin, Token, VerifyEmail,
    RequestPasswordReset, ResetPassword, UserResponse, RefreshToken
)
from app.services.auth import (
    get_password_hash, verify_password, create_access_token,
    create_verification_token, create_password_reset_token, verify_token,
    create_refresh_token, decode_token
)
from app.services.email import send_verification_email, send_password_reset_email
from app.services.rate_limiter import check_rate_limit, reset_rate_limit, get_client_ip
from datetime import timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password.
    Sends verification email after successful registration.
    """
    # Check rate limit
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_verified=False
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send verification email
    verification_token = create_verification_token(new_user.email)
    send_verification_email(new_user.email, verification_token)
    
    logger.info(f"New user registered: {new_user.email}")
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    Rate limited to 5 attempts per 15 minutes per IP.
    """
    # Check rate limit
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)
    
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Generic error message to avoid revealing which field is incorrect
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    # Reset rate limit on successful login
    reset_rate_limit(client_ip)
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    verification_data: VerifyEmail,
    db: Session = Depends(get_db)
):
    """
    Verify user email address using the token sent via email.
    """
    # Verify token
    email = verify_token(verification_data.token, "email_verification")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already verified
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Mark as verified
    user.is_verified = True
    db.commit()
    
    logger.info(f"Email verified: {user.email}")
    
    return {"message": "Email verified successfully"}


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_request: RequestPasswordReset,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request password reset. Sends reset link to email if user exists.
    Always returns success to avoid email enumeration.
    """
    # Check rate limit
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)
    
    # Find user
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    # Always return success to avoid email enumeration
    if user:
        # Send password reset email
        reset_token = create_password_reset_token(user.email)
        send_password_reset_email(user.email, reset_token)
        logger.info(f"Password reset requested: {user.email}")
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_data: ResetPassword,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reset user password using the token sent via email.
    """
    # Check rate limit
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)
    
    # Verify token
    email = verify_token(reset_data.token, "password_reset")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    db.commit()
    
    logger.info(f"Password reset completed: {user.email}")
    
    return {"message": "Password reset successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    Returns a new access token and refresh token pair.
    """
    # Check rate limit
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)
    
    # Decode and validate refresh token
    payload = decode_token(token_data.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token type
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info
    email = payload.get("sub")
    user_id = payload.get("user_id")
    
    if not email or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    # Create new refresh token
    new_refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )
    
    logger.info(f"Token refreshed for user: {user.email}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
