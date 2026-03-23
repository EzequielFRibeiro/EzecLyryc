"""
Subscription management API endpoints.

Handles Pro subscription upgrades, status checks, and payment webhooks.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription, PaymentStatus
from app.schemas.subscription import (
    SubscriptionStatusResponse,
    SubscriptionUpgradeRequest,
    SubscriptionUpgradeResponse,
    WebhookPaymentEvent
)
from app.middleware.auth import get_current_active_user
from datetime import datetime, timedelta
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription status.
    
    Returns subscription tier, payment status, expiration date, and days remaining.
    """
    # Get or create subscription record
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        # Create default free subscription
        subscription = Subscription(
            user_id=current_user.id,
            tier=SubscriptionTier.FREE,
            payment_status=PaymentStatus.ACTIVE
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    
    # Calculate if subscription is active
    is_active = True
    days_remaining = None
    
    if subscription.tier == SubscriptionTier.PRO:
        if subscription.expires_at:
            now = datetime.utcnow()
            if subscription.expires_at < now:
                is_active = False
                days_remaining = 0
            else:
                days_remaining = (subscription.expires_at - now).days
    
    return SubscriptionStatusResponse(
        user_id=current_user.id,
        tier=subscription.tier.value,
        payment_status=subscription.payment_status.value,
        expires_at=subscription.expires_at,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
        is_active=is_active,
        days_remaining=days_remaining
    )


@router.post("/upgrade", response_model=SubscriptionUpgradeResponse, status_code=status.HTTP_200_OK)
async def upgrade_to_pro(
    request: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upgrade user to Pro subscription.
    
    Processes payment and updates subscription tier.
    This is a placeholder implementation - integrate with actual payment provider (Stripe, etc.)
    
    Raises:
        HTTPException 400: Already Pro user or payment failed
    """
    # Get or create subscription
    subscription = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    
    if not subscription:
        subscription = Subscription(
            user_id=current_user.id,
            tier=SubscriptionTier.FREE,
            payment_status=PaymentStatus.ACTIVE
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
    
    # Check if already Pro
    if subscription.tier == SubscriptionTier.PRO and subscription.payment_status == PaymentStatus.ACTIVE:
        if subscription.expires_at and subscription.expires_at > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active Pro subscription"
            )
    
    # Placeholder payment processing
    # In production, integrate with Stripe, PayPal, or other payment provider
    payment_success = process_payment_placeholder(request.payment_method_id, current_user.id)
    
    if not payment_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment processing failed. Please check your payment method and try again."
        )
    
    # Update subscription to Pro
    subscription.tier = SubscriptionTier.PRO
    subscription.payment_status = PaymentStatus.ACTIVE
    subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # 30-day subscription
    
    # Update user tier
    current_user.subscription_tier = SubscriptionTier.PRO
    
    db.commit()
    db.refresh(subscription)
    
    logger.info(f"User upgraded to Pro: user_id={current_user.id}, email={current_user.email}")
    
    return SubscriptionUpgradeResponse(
        message="Successfully upgraded to Pro subscription",
        subscription_id=subscription.id,
        tier=subscription.tier.value,
        expires_at=subscription.expires_at,
        payment_status=subscription.payment_status.value
    )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature")
):
    """
    Webhook endpoint for payment provider callbacks.
    
    Handles payment success, failure, and subscription cancellation events.
    This is a placeholder implementation - integrate with actual payment provider webhooks.
    
    Security: Verify webhook signature to ensure authenticity.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature (placeholder)
    # In production, use actual payment provider's signature verification
    if not verify_webhook_signature_placeholder(body, x_webhook_signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook data
    try:
        data = await request.json()
        event_type = data.get("event_type")
        user_id = data.get("user_id")
        subscription_id = data.get("subscription_id")
        
        # Validate required fields
        if not event_type or not user_id or not subscription_id:
            raise ValueError("Missing required fields")
            
    except Exception as e:
        logger.error(f"Failed to parse webhook data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook data"
        )
    
    # Get subscription
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    if not subscription:
        logger.warning(f"Subscription not found: {subscription_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Handle different event types
    if event_type == "payment.success":
        # Payment successful - extend subscription
        subscription.payment_status = PaymentStatus.ACTIVE
        subscription.expires_at = datetime.utcnow() + timedelta(days=30)
        logger.info(f"Payment success: subscription_id={subscription_id}")
    
    elif event_type == "payment.failed":
        # Payment failed - mark as pending
        subscription.payment_status = PaymentStatus.PENDING
        logger.warning(f"Payment failed: subscription_id={subscription_id}")
    
    elif event_type == "subscription.cancelled":
        # Subscription cancelled - mark as cancelled
        subscription.payment_status = PaymentStatus.CANCELLED
        subscription.tier = SubscriptionTier.FREE
        
        # Update user tier
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.subscription_tier = SubscriptionTier.FREE
        
        logger.info(f"Subscription cancelled: subscription_id={subscription_id}")
    
    else:
        logger.warning(f"Unknown event type: {event_type}")
    
    db.commit()
    
    return {"message": "Webhook processed successfully"}


# Placeholder functions for payment processing
# In production, replace with actual payment provider integration

def process_payment_placeholder(payment_method_id: str, user_id: int) -> bool:
    """
    Placeholder payment processing function.
    
    In production, integrate with Stripe, PayPal, or other payment provider:
    - Validate payment method
    - Create payment intent
    - Process payment
    - Handle errors and retries
    
    Args:
        payment_method_id: Payment method identifier
        user_id: User ID
    
    Returns:
        True if payment successful, False otherwise
    """
    logger.info(f"Processing payment (placeholder): payment_method={payment_method_id}, user={user_id}")
    
    # Simulate successful payment
    # In production, this would call the payment provider API
    return True


def verify_webhook_signature_placeholder(body: bytes, signature: str) -> bool:
    """
    Placeholder webhook signature verification.
    
    In production, implement actual signature verification:
    - Stripe: stripe.Webhook.construct_event()
    - PayPal: Verify webhook signature with PayPal SDK
    
    Args:
        body: Raw webhook body
        signature: Webhook signature header
    
    Returns:
        True if signature is valid, False otherwise
    """
    # In production, verify signature using payment provider's method
    # Example for Stripe:
    # try:
    #     event = stripe.Webhook.construct_event(
    #         body, signature, webhook_secret
    #     )
    #     return True
    # except ValueError:
    #     return False
    
    # Placeholder: accept all webhooks (INSECURE - for development only)
    return True
