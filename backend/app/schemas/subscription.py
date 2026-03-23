"""
Pydantic schemas for subscription management.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SubscriptionStatusResponse(BaseModel):
    """Response for subscription status"""
    user_id: int
    tier: str
    payment_status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    days_remaining: Optional[int] = None


class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade to Pro subscription"""
    payment_method_id: str = Field(..., description="Payment method identifier from payment provider")
    billing_email: Optional[str] = Field(None, description="Billing email if different from account email")


class SubscriptionUpgradeResponse(BaseModel):
    """Response after subscription upgrade"""
    message: str
    subscription_id: int
    tier: str
    expires_at: datetime
    payment_status: str


class WebhookPaymentEvent(BaseModel):
    """Payment webhook event data"""
    event_type: str = Field(..., description="Event type: payment.success, payment.failed, subscription.cancelled")
    user_id: int
    subscription_id: int
    payment_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    timestamp: datetime
