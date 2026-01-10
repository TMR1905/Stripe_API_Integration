# Stripe Integration Setup Guide

## Overview

Your FastAPI SaaS platform now has complete Stripe billing integration with:
- ✅ Subscription checkout sessions
- ✅ Subscription management
- ✅ Webhook handling for automatic updates
- ✅ Payment history tracking

---

## Prerequisites

1. **Stripe Account**: Sign up at https://stripe.com
2. **Stripe CLI**: For testing webhooks locally (https://stripe.com/docs/stripe-cli)

---

## Step 1: Get Your Stripe Keys

### 1. Go to Stripe Dashboard
Visit: https://dashboard.stripe.com/test/apikeys

### 2. Copy Your Keys
- **Publishable Key**: `pk_test_...`
- **Secret Key**: `sk_test_...`

### 3. Create a Webhook Secret
1. Go to: https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. For local testing, use Stripe CLI (see below)
4. Copy the webhook signing secret: `whsec_...`

---

## Step 2: Create Stripe Products & Prices

### 1. Go to Products
Visit: https://dashboard.stripe.com/test/products

### 2. Create Your Plans

**Example: Basic Plan**
- Name: Basic Plan
- Price: $9.99/month
- Billing: Recurring monthly
- After creating, copy the **Price ID**: `price_1234567890`

**Example: Pro Plan**
- Name: Pro Plan
- Price: $29.99/month
- Billing: Recurring monthly
- Copy the **Price ID**: `price_0987654321`

### 3. Update Price IDs in Code

Edit [app/services/stripe_service.py](app/services/stripe_service.py) line 238:

```python
def _determine_tier_from_price_id(price_id: str) -> SubscriptionTier:
    tier_mapping = {
        "price_1234567890": SubscriptionTier.BASIC,    # Your actual Basic price ID
        "price_0987654321": SubscriptionTier.PRO,      # Your actual Pro price ID
        "price_enterprise_monthly": SubscriptionTier.ENTERPRISE,
    }
    return tier_mapping.get(price_id, SubscriptionTier.FREE)
```

---

## Step 3: Configure Environment Variables

Update your `.env` file:

```env
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

---

## Step 4: Initialize Database

Make sure your database tables are created:

```bash
# If using Alembic
alembic upgrade head

# Or manually in Python
python
>>> from app.database import init_db
>>> init_db()
```

---

## Step 5: Test Webhooks Locally

### Install Stripe CLI
```bash
# Windows
scoop install stripe

# macOS
brew install stripe/stripe-cli/stripe

# Linux
# Download from https://github.com/stripe/stripe-cli/releases
```

### Login to Stripe CLI
```bash
stripe login
```

### Forward Webhooks to Your Local Server
```bash
stripe listen --forward-to http://localhost:8000/api/v1/webhooks/stripe
```

This will give you a webhook signing secret like: `whsec_...`

Update your `.env` with this secret:
```env
STRIPE_WEBHOOK_SECRET=whsec_the_secret_from_stripe_cli
```

---

## API Endpoints

### Authentication Endpoints

#### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

---

### Billing Endpoints

#### Create Checkout Session
```http
POST /api/v1/billing/create-checkout-session
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "price_id": "price_1234567890",
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/cancel"
}
```

Response:
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_1234567890"
}
```

**Flow:**
1. User calls this endpoint
2. Backend creates Stripe checkout session
3. Frontend redirects user to `checkout_url`
4. User enters payment details on Stripe
5. Stripe redirects to `success_url` or `cancel_url`
6. Webhook updates subscription in database

#### Get Subscription Status
```http
GET /api/v1/billing/subscription
Authorization: Bearer <access_token>
```

Response:
```json
{
  "id": 1,
  "user_id": 1,
  "stripe_subscription_id": "sub_1234567890",
  "tier": "pro",
  "status": "active",
  "current_period_start": "2026-01-11T00:00:00Z",
  "current_period_end": "2026-02-11T00:00:00Z",
  "cancel_at_period_end": false,
  "canceled_at": null,
  "created_at": "2026-01-11T10:30:00Z"
}
```

#### Cancel Subscription
```http
POST /api/v1/billing/cancel
Authorization: Bearer <access_token>
```

Response:
```json
{
  "message": "Subscription will be canceled at the end of the current billing period",
  "subscription": {
    "id": 1,
    "tier": "pro",
    "status": "active",
    "cancel_at_period_end": true,
    ...
  }
}
```

---

### Webhook Endpoint

```http
POST /api/v1/webhooks/stripe
Stripe-Signature: <stripe_signature>
```

**Events Handled:**
- `checkout.session.completed` - Subscription created after successful payment
- `customer.subscription.updated` - Subscription status changed
- `customer.subscription.deleted` - Subscription canceled
- `invoice.payment_succeeded` - Payment succeeded
- `invoice.payment_failed` - Payment failed

**Webhook Flow:**
1. Event occurs in Stripe (payment, subscription change, etc.)
2. Stripe sends POST to `/api/v1/webhooks/stripe`
3. Backend verifies signature
4. Updates database accordingly
5. Returns 200 OK

---

## Testing the Integration

### Test Flow with Stripe Test Cards

1. **Register a User**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'
```

2. **Create Checkout Session**
```bash
curl -X POST http://localhost:8000/api/v1/billing/create-checkout-session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "price_id": "price_1234567890",
    "success_url": "http://localhost:3000/success",
    "cancel_url": "http://localhost:3000/cancel"
  }'
```

3. **Visit the Checkout URL** (from response)

4. **Use Stripe Test Card**
- Card Number: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

5. **Complete Payment**

6. **Webhook Triggers** (if Stripe CLI is running)
- Check console logs for webhook events

7. **Check Subscription Status**
```bash
curl -X GET http://localhost:8000/api/v1/billing/subscription \
  -H "Authorization: Bearer <access_token>"
```

---

## Database Schema

### Users Table
- `id` - Primary key
- `email` - User email
- `hashed_password` - Bcrypt hash
- `stripe_customer_id` - Stripe customer ID (links to Stripe)
- ...

### Subscriptions Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `stripe_subscription_id` - Stripe subscription ID
- `tier` - BASIC, PRO, ENTERPRISE
- `status` - ACTIVE, CANCELED, PAST_DUE, etc.
- `current_period_start` - Billing period start
- `current_period_end` - Billing period end
- `cancel_at_period_end` - Will cancel at end of period
- ...

### Payments Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `stripe_payment_intent_id` - Stripe payment ID
- `amount` - Payment amount in dollars
- `status` - PENDING, SUCCEEDED, FAILED
- ...

---

## Security Best Practices

✅ **Webhook Signature Verification** - Always verify `Stripe-Signature` header
✅ **Environment Variables** - Never commit API keys to git
✅ **HTTPS in Production** - Stripe requires HTTPS for webhooks
✅ **JWT Authentication** - Protected billing endpoints require valid token
✅ **Database Transactions** - Webhook handlers use transactions

---

## Production Deployment Checklist

### 1. Switch to Live Mode
- Get live API keys from Stripe dashboard
- Update `.env` with live keys:
  - `STRIPE_SECRET_KEY=sk_live_...`
  - `STRIPE_PUBLISHABLE_KEY=pk_live_...`

### 2. Configure Production Webhook
1. Go to: https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://yourdomain.com/api/v1/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy webhook signing secret to `.env`

### 3. Update Price IDs
- Replace test price IDs with live price IDs in `stripe_service.py`

### 4. Enable HTTPS
- Stripe webhooks require HTTPS in production
- Use Let's Encrypt, Cloudflare, or your hosting provider's SSL

### 5. Monitor Webhooks
- Check webhook logs in Stripe dashboard
- Set up error alerts for failed webhooks

---

## Common Issues & Solutions

### Issue: "Invalid signature" on webhook
**Solution**:
- Make sure `STRIPE_WEBHOOK_SECRET` matches your webhook endpoint
- For local testing, use the secret from `stripe listen` command
- For production, use the secret from Stripe dashboard

### Issue: Subscription not updating after payment
**Solution**:
- Check if webhook endpoint is reachable
- Verify webhook signature is correct
- Check server logs for errors
- Use `stripe listen` to see webhook events

### Issue: "No active subscription found"
**Solution**:
- Complete a test payment first
- Wait for webhook to process (usually instant)
- Check database `subscriptions` table

---

## File Structure

```
app/
├── services/
│   └── stripe_service.py          # Stripe API logic
├── schemas/
│   └── billing.py                 # Billing request/response schemas
├── api/v1/endpoints/
│   ├── billing.py                 # Billing endpoints
│   └── webhooks.py                # Webhook handler
└── models/
    ├── subscription.py            # Subscription database model
    └── payment.py                 # Payment database model
```

---

## Additional Resources

- **Stripe API Docs**: https://stripe.com/docs/api
- **Stripe Testing**: https://stripe.com/docs/testing
- **Stripe Webhooks**: https://stripe.com/docs/webhooks
- **Stripe CLI**: https://stripe.com/docs/stripe-cli

---

## Support

If you encounter issues:
1. Check Stripe dashboard logs
2. Review webhook event details
3. Check server logs for errors
4. Use Stripe CLI for local debugging

Happy building! 🚀
