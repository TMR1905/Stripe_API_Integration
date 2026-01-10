"""
Billing and subscription Pydantic schemas
"""
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.subscription import SubscriptionStatus, SubscriptionTier
from app.models.payment import PaymentStatus


class CheckoutSessionRequest(BaseModel):
    """Request to create a Stripe checkout session"""
    price_id: str
    success_url: HttpUrl
    cancel_url: HttpUrl

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "price_id": "price_1234567890",
                "success_url": "https://yourapp.com/success",
                "cancel_url": "https://yourapp.com/cancel"
            }
        }
    )


class CheckoutSessionResponse(BaseModel):
    """Response containing checkout session URL"""
    checkout_url: str
    session_id: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
                "session_id": "cs_test_1234567890"
            }
        }
    )


class SubscriptionResponse(BaseModel):
    """Subscription information response"""
    id: int
    user_id: int
    stripe_subscription_id: Optional[str]
    tier: SubscriptionTier
    status: SubscriptionStatus
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CancelSubscriptionResponse(BaseModel):
    """Response after canceling subscription"""
    message: str
    subscription: SubscriptionResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Subscription will be canceled at the end of the current billing period",
                "subscription": {
                    "id": 1,
                    "tier": "pro",
                    "status": "active",
                    "cancel_at_period_end": True
                }
            }
        }
    )


class PaymentResponse(BaseModel):
    """Payment record response"""
    id: int
    user_id: int
    stripe_payment_intent_id: Optional[str]
    stripe_invoice_id: Optional[str]
    amount: float
    currency: str
    status: PaymentStatus
    description: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
