"""
Billing endpoints for Stripe subscription management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    SubscriptionResponse,
    CancelSubscriptionResponse
)
from app.services.stripe_service import (
    create_checkout_session,
    get_user_subscription,
    cancel_subscription
)


router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout(
    payload: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscription.

    Returns a checkout URL where the user will be redirected to complete payment.
    """
    try:
        checkout_data = create_checkout_session(
            db=db,
            user=current_user,
            price_id=payload.price_id,
            success_url=str(payload.success_url),
            cancel_url=str(payload.cancel_url)
        )
        return CheckoutSessionResponse(**checkout_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's active subscription information.

    Returns subscription details including tier, status, and billing period.
    """
    subscription = get_user_subscription(db, current_user)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    return subscription


@router.post("/cancel", response_model=CancelSubscriptionResponse)
def cancel_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel the current user's subscription.

    Subscription will remain active until the end of the current billing period.
    """
    try:
        subscription = cancel_subscription(db, current_user)
        return CancelSubscriptionResponse(
            message="Subscription will be canceled at the end of the current billing period",
            subscription=subscription
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )
