"""
Stripe service for handling all Stripe API interactions
"""
import stripe
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionTier
from app.models.payment import Payment, PaymentStatus

# Initialize Stripe with secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_stripe_customer(db: Session, user: User) -> str:
    """
    Get existing Stripe customer ID or create new customer

    Args:
        db: Database session
        user: User model instance

    Returns:
        Stripe customer ID
    """
    # Return existing customer ID if available
    if user.stripe_customer_id:
        return user.stripe_customer_id

    # Create new Stripe customer
    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name,
        metadata={
            "user_id": str(user.id)
        }
    )

    # Save customer ID to database
    user.stripe_customer_id = customer.id
    db.commit()
    db.refresh(user)

    return customer.id


def create_checkout_session(
    db: Session,
    user: User,
    price_id: str,
    success_url: str,
    cancel_url: str
) -> Dict[str, Any]:
    """
    Create Stripe Checkout session for subscription

    Args:
        db: Database session
        user: User model instance
        price_id: Stripe price ID for the subscription plan
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels

    Returns:
        Dictionary with checkout session URL and ID
    """
    # Get or create Stripe customer
    customer_id = get_or_create_stripe_customer(db, user)

    # Create checkout session
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": str(user.id)
        }
    )

    return {
        "checkout_url": checkout_session.url,
        "session_id": checkout_session.id
    }


def get_user_subscription(db: Session, user: User) -> Optional[Subscription]:
    """
    Get user's active subscription

    Args:
        db: Database session
        user: User model instance

    Returns:
        Subscription object or None
    """
    return db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    ).first()


def cancel_subscription(db: Session, user: User) -> Subscription:
    """
    Cancel user's subscription (at period end)

    Args:
        db: Database session
        user: User model instance

    Returns:
        Updated subscription object

    Raises:
        ValueError: If no active subscription found
    """
    # Get active subscription
    subscription = get_user_subscription(db, user)
    if not subscription:
        raise ValueError("No active subscription found")

    # Cancel in Stripe (at period end)
    stripe.Subscription.modify(
        subscription.stripe_subscription_id,
        cancel_at_period_end=True
    )

    # Update database
    subscription.cancel_at_period_end = True
    db.commit()
    db.refresh(subscription)

    return subscription


def create_or_update_subscription(
    db: Session,
    user_id: int,
    stripe_subscription: Dict[str, Any]
) -> Subscription:
    """
    Create or update subscription from Stripe webhook data

    Args:
        db: Database session
        user_id: User ID
        stripe_subscription: Stripe subscription object (as dict)

    Returns:
        Subscription object
    """
    # Check if subscription already exists
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_subscription["id"]
    ).first()

    # Map Stripe status to our enum
    status_mapping = {
        "active": SubscriptionStatus.ACTIVE,
        "canceled": SubscriptionStatus.CANCELED,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "past_due": SubscriptionStatus.PAST_DUE,
        "trialing": SubscriptionStatus.TRIALING,
        "unpaid": SubscriptionStatus.UNPAID,
    }

    status = status_mapping.get(
        stripe_subscription["status"],
        SubscriptionStatus.INCOMPLETE
    )

    # Determine tier based on price_id (you'll need to configure this)
    price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
    tier = _determine_tier_from_price_id(price_id)

    if subscription:
        # Update existing subscription
        subscription.status = status
        subscription.tier = tier
        subscription.current_period_start = stripe_subscription.get("current_period_start")
        subscription.current_period_end = stripe_subscription.get("current_period_end")
        subscription.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)
        subscription.canceled_at = stripe_subscription.get("canceled_at")
    else:
        # Create new subscription
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription["id"],
            stripe_price_id=price_id,
            stripe_product_id=stripe_subscription["items"]["data"][0]["price"]["product"],
            tier=tier,
            status=status,
            current_period_start=stripe_subscription.get("current_period_start"),
            current_period_end=stripe_subscription.get("current_period_end"),
            cancel_at_period_end=stripe_subscription.get("cancel_at_period_end", False),
            canceled_at=stripe_subscription.get("canceled_at")
        )
        db.add(subscription)

    db.commit()
    db.refresh(subscription)
    return subscription


def create_payment_record(
    db: Session,
    user_id: int,
    stripe_invoice: Dict[str, Any]
) -> Payment:
    """
    Create payment record from Stripe invoice

    Args:
        db: Database session
        user_id: User ID
        stripe_invoice: Stripe invoice object (as dict)

    Returns:
        Payment object
    """
    payment_intent_id = stripe_invoice.get("payment_intent")

    # Check if payment already exists
    existing_payment = db.query(Payment).filter(
        Payment.stripe_payment_intent_id == payment_intent_id
    ).first()

    if existing_payment:
        return existing_payment

    # Map Stripe status to our enum
    status_mapping = {
        "paid": PaymentStatus.SUCCEEDED,
        "open": PaymentStatus.PENDING,
        "void": PaymentStatus.FAILED,
        "uncollectible": PaymentStatus.FAILED,
    }

    status = status_mapping.get(
        stripe_invoice.get("status"),
        PaymentStatus.PENDING
    )

    # Create payment record
    payment = Payment(
        user_id=user_id,
        stripe_payment_intent_id=payment_intent_id,
        stripe_invoice_id=stripe_invoice["id"],
        amount=stripe_invoice["amount_paid"] / 100,  # Convert cents to dollars
        currency=stripe_invoice["currency"],
        status=status,
        description=f"Invoice for subscription"
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def _determine_tier_from_price_id(price_id: str) -> SubscriptionTier:
    """
    Determine subscription tier from Stripe price ID

    You need to configure your actual Stripe price IDs here

    Args:
        price_id: Stripe price ID

    Returns:
        SubscriptionTier enum value
    """
    # TODO: Replace with your actual Stripe price IDs
    tier_mapping = {
        "price_basic_monthly": SubscriptionTier.BASIC,
        "price_pro_monthly": SubscriptionTier.PRO,
        "price_enterprise_monthly": SubscriptionTier.ENTERPRISE,
    }

    return tier_mapping.get(price_id, SubscriptionTier.FREE)
