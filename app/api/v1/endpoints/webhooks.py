"""
Stripe webhook endpoint for handling subscription and payment events
"""
import stripe
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.services.stripe_service import create_or_update_subscription, create_payment_record
from app.services.user_service import get_user_by_id


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Stripe webhook events.

    Processes events like:
    - checkout.session.completed: When user completes payment
    - customer.subscription.updated: When subscription status changes
    - customer.subscription.deleted: When subscription is canceled
    - invoice.payment_succeeded: When payment succeeds
    - invoice.payment_failed: When payment fails
    """
    # Get raw body for signature verification
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    # Handle the event
    event_type = event["type"]
    data_object = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            # Payment is successful and subscription is created
            handle_checkout_session_completed(db, data_object)

        elif event_type == "customer.subscription.updated":
            # Subscription status changed (renewed, canceled, etc.)
            handle_subscription_updated(db, data_object)

        elif event_type == "customer.subscription.deleted":
            # Subscription was deleted/canceled
            handle_subscription_deleted(db, data_object)

        elif event_type == "invoice.payment_succeeded":
            # Payment succeeded
            handle_invoice_payment_succeeded(db, data_object)

        elif event_type == "invoice.payment_failed":
            # Payment failed
            handle_invoice_payment_failed(db, data_object)

        else:
            # Unhandled event type
            print(f"Unhandled event type: {event_type}")

    except Exception as e:
        # Log error but return 200 to acknowledge receipt
        print(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )

    return {"status": "success"}


def handle_checkout_session_completed(db: Session, session: dict):
    """
    Handle successful checkout session.

    Creates subscription record in database.
    """
    # Get user ID from metadata
    user_id = int(session["metadata"]["user_id"])

    # Get subscription from Stripe
    subscription_id = session["subscription"]
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)

    # Create or update subscription in database
    create_or_update_subscription(db, user_id, stripe_subscription)

    print(f"Checkout completed for user {user_id}")


def handle_subscription_updated(db: Session, subscription: dict):
    """
    Handle subscription update event.

    Updates subscription status in database.
    """
    # Get user ID from customer
    customer_id = subscription["customer"]
    customer = stripe.Customer.retrieve(customer_id)
    user_id = int(customer["metadata"]["user_id"])

    # Update subscription in database
    create_or_update_subscription(db, user_id, subscription)

    print(f"Subscription updated for user {user_id}: {subscription['status']}")


def handle_subscription_deleted(db: Session, subscription: dict):
    """
    Handle subscription deletion event.

    Marks subscription as canceled in database.
    """
    # Get user ID from customer
    customer_id = subscription["customer"]
    customer = stripe.Customer.retrieve(customer_id)
    user_id = int(customer["metadata"]["user_id"])

    # Update subscription status to canceled
    create_or_update_subscription(db, user_id, subscription)

    print(f"Subscription deleted for user {user_id}")


def handle_invoice_payment_succeeded(db: Session, invoice: dict):
    """
    Handle successful payment event.

    Creates payment record in database.
    """
    # Get user ID from customer
    customer_id = invoice["customer"]
    customer = stripe.Customer.retrieve(customer_id)
    user_id = int(customer["metadata"]["user_id"])

    # Create payment record
    create_payment_record(db, user_id, invoice)

    print(f"Payment succeeded for user {user_id}: ${invoice['amount_paid'] / 100}")


def handle_invoice_payment_failed(db: Session, invoice: dict):
    """
    Handle failed payment event.

    Creates failed payment record and could trigger notifications.
    """
    # Get user ID from customer
    customer_id = invoice["customer"]
    customer = stripe.Customer.retrieve(customer_id)
    user_id = int(customer["metadata"]["user_id"])

    # Create payment record with failed status
    create_payment_record(db, user_id, invoice)

    print(f"Payment failed for user {user_id}")
    # TODO: Send email notification to user about failed payment
