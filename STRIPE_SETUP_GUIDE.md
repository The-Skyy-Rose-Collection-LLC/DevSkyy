# Stripe Payment Integration Guide

**Date:** 2025-11-20
**Status:** Publishable Key ✅ | Secret Key ⚠️ Needed

---

## Current Status

### ✅ Publishable Key Configured

Your Stripe **publishable key** has been securely added to `.env`:
```
STRIPE_PUBLISHABLE_KEY=pk_live_51MsM1iJ...
```

**What is it for?**
- Used in **frontend/client-side** code
- Embedded in HTML/JavaScript
- **Safe to expose publicly**
- Used with Stripe.js, Stripe Elements
- Creates payment tokens, validates cards

### ⚠️ Secret Key Required

You still need to add your **secret key** to `.env`:
```
STRIPE_SECRET_KEY=sk_live_...  # ⚠️ YOU NEED THIS
```

**What is it for?**
- Used in **backend/server-side** code
- **MUST be kept secret** (never expose in frontend)
- Creates charges, subscriptions, customers
- Accesses sensitive account data
- Full access to Stripe API

---

## Key Types Explained

### 1. Publishable Key (`pk_live_...` or `pk_test_...`)

**Purpose:** Client-side operations
**Security:** Public (safe to expose)
**Used for:**
- Stripe.js initialization
- Creating payment tokens
- Card validation
- 3D Secure authentication
- Apple Pay / Google Pay

**Example (Frontend):**
```html
<script src="https://js.stripe.com/v3/"></script>
<script>
  const stripe = Stripe('pk_live_51MsM1iJGv6CRbKbg5EWN4swnwt1zwMs2Oe3K9xKsU4cDVPPzqd19MxYYfgYQ0EcXG3uf5CiAxgv4HAMEoJcaoglW00Lxy1kvRJ');

  // Create payment element
  const elements = stripe.elements();
  const cardElement = elements.create('card');
  cardElement.mount('#card-element');
</script>
```

### 2. Secret Key (`sk_live_...` or `sk_test_...`)

**Purpose:** Server-side operations
**Security:** SECRET (never expose)
**Used for:**
- Creating charges
- Managing subscriptions
- Creating customers
- Issuing refunds
- Accessing account data

**Example (Backend):**
```python
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # sk_live_...

# Create a customer
customer = stripe.Customer.create(
    email="user@example.com",
    name="John Doe"
)

# Create a subscription
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{"price": "price_1234"}]
)
```

### 3. Webhook Secret (`whsec_...`)

**Purpose:** Verify webhook signatures
**Security:** SECRET (server-side only)
**Used for:**
- Validating webhook events from Stripe
- Preventing webhook spoofing

**Example:**
```python
import stripe
import os

def verify_webhook(payload, sig_header):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError:
        # Invalid payload
        return None
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return None
```

---

## How to Get Your Keys

### Step 1: Access Stripe Dashboard

Go to: **https://dashboard.stripe.com/apikeys**

### Step 2: Find Your Keys

You'll see:
- ✅ **Publishable key** (pk_live_...) - Already configured
- ⚠️ **Secret key** (sk_live_...) - **YOU NEED THIS**

### Step 3: Reveal Secret Key

1. Click **"Reveal test key token"** or **"Reveal live key token"**
2. Copy the key (starts with `sk_live_` or `sk_test_`)
3. Add to `.env` file

### Step 4: Update .env

```bash
# Edit .env file
nano .env  # or use your preferred editor

# Replace this line:
STRIPE_SECRET_KEY=your_secret_key_here

# With your actual secret key:
STRIPE_SECRET_KEY=sk_live_your_actual_key_here
```

### Step 5: Verify

```bash
# Test Stripe connection
python3 << 'PYEOF'
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

try:
    # Test API access
    account = stripe.Account.retrieve()
    print(f"✅ Stripe connected: {account.business_profile.name}")
    print(f"   Account ID: {account.id}")
    print(f"   Mode: {'LIVE' if 'live' in os.getenv('STRIPE_SECRET_KEY', '') else 'TEST'}")
except stripe.error.AuthenticationError:
    print("❌ Invalid Stripe secret key")
except Exception as e:
    print(f"❌ Error: {e}")
PYEOF
```

---

## Test Mode vs Live Mode

### Test Mode (`pk_test_...` / `sk_test_...`)

**Use for:** Development and testing
**Features:**
- No real money
- Test card numbers (4242 4242 4242 4242)
- Test webhooks
- Separate data from live

### Live Mode (`pk_live_...` / `sk_live_...`)

**Use for:** Production
**Features:**
- Real money transactions
- Real customer data
- Requires business verification
- PCI compliance needed

**You are in:** 🟢 **LIVE MODE** (based on `pk_live_` key)

---

## Security Best Practices

### ✅ DO

- ✅ Store secret key in `.env` file (gitignored)
- ✅ Use environment variables in code
- ✅ Keep secret key on server-side only
- ✅ Use HTTPS for all Stripe API calls
- ✅ Verify webhook signatures
- ✅ Enable Stripe Radar (fraud protection)
- ✅ Log all payment events
- ✅ Use strong authentication for Stripe dashboard

### ❌ DON'T

- ❌ Never commit secret key to git
- ❌ Never expose secret key in frontend
- ❌ Never log secret key
- ❌ Never share secret key in chat/email
- ❌ Never hardcode keys in source code
- ❌ Never use live keys in development

---

## Integration Examples

### 1. Create Payment Intent (Backend)

```python
# api/v1/payments.py
import stripe
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentIntentRequest(BaseModel):
    amount: int  # Amount in cents (e.g., 1000 = $10.00)
    currency: str = "usd"

@router.post("/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    """Create a Stripe Payment Intent."""
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            automatic_payment_methods={"enabled": True}
        )

        return {
            "client_secret": payment_intent.client_secret,
            "id": payment_intent.id
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. Create Subscription

```python
# api/v1/subscriptions.py
import stripe
import os
from fastapi import APIRouter, Depends
from security.jwt_auth import get_current_user

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/create")
async def create_subscription(
    price_id: str,
    current_user = Depends(get_current_user)
):
    """Create a subscription for the current user."""
    try:
        # Create or retrieve customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            # Save to database

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[{"price": price_id}],
            trial_period_days=14  # Optional: 14-day free trial
        )

        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 3. Handle Webhooks

```python
# api/v1/webhooks.py
import stripe
import os
from fastapi import APIRouter, Request, HTTPException

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle event
    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object
        print(f"✅ Payment succeeded: {payment_intent.id}")
        # Update database, send confirmation email, etc.

    elif event.type == "customer.subscription.created":
        subscription = event.data.object
        print(f"✅ Subscription created: {subscription.id}")
        # Grant access, send welcome email, etc.

    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        print(f"❌ Subscription cancelled: {subscription.id}")
        # Revoke access, send cancellation email, etc.

    return {"status": "success"}
```

### 4. Frontend Payment Form

```html
<!-- templates/checkout.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Checkout</title>
    <script src="https://js.stripe.com/v3/"></script>
</head>
<body>
    <form id="payment-form">
        <div id="card-element"></div>
        <button id="submit">Pay $10.00</button>
        <div id="error-message"></div>
    </form>

    <script>
        const stripe = Stripe('{{ STRIPE_PUBLISHABLE_KEY }}');
        const elements = stripe.elements();
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');

        const form = document.getElementById('payment-form');
        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            // Create Payment Intent on backend
            const response = await fetch('/api/v1/payments/create-payment-intent', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount: 1000, currency: 'usd'})
            });
            const {client_secret} = await response.json();

            // Confirm payment with card
            const {error} = await stripe.confirmCardPayment(client_secret, {
                payment_method: {card: cardElement}
            });

            if (error) {
                document.getElementById('error-message').textContent = error.message;
            } else {
                alert('Payment successful!');
            }
        });
    </script>
</body>
</html>
```

---

## Common Use Cases

### 1. One-Time Payments

```python
# Charge $50.00 once
payment_intent = stripe.PaymentIntent.create(
    amount=5000,  # $50.00 in cents
    currency="usd",
    payment_method_types=["card"]
)
```

### 2. Subscriptions

```python
# Monthly subscription at $29/month
subscription = stripe.Subscription.create(
    customer="cus_xxxxx",
    items=[{"price": "price_monthly_29"}],
    trial_period_days=14
)
```

### 3. Usage-Based Billing

```python
import time

# Metered billing (e.g., per API call)
stripe.SubscriptionItem.create_usage_record(
    subscription_item="si_xxxxx",
    quantity=100,  # 100 API calls
    timestamp=int(time.time())
)
```

### 4. Invoices

```python
# Create invoice
invoice = stripe.Invoice.create(
    customer="cus_xxxxx",
    auto_advance=True  # Auto-finalize and send
)

# Add line items
stripe.InvoiceItem.create(
    customer="cus_xxxxx",
    invoice=invoice.id,
    amount=5000,
    currency="usd",
    description="Custom service"
)
```

---

## Webhook Setup

### Step 1: Create Webhook Endpoint

1. Go to: https://dashboard.stripe.com/webhooks
2. Click **"Add endpoint"**
3. Enter URL: `https://your-domain.com/api/v1/webhooks/stripe`
4. Select events to listen for:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`

### Step 2: Get Webhook Secret

1. After creating webhook, click **"Reveal"** under "Signing secret"
2. Copy the secret (starts with `whsec_`)
3. Add to `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```

### Step 3: Test Webhook

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Trigger test event
stripe trigger payment_intent.succeeded
```

---

## Testing

### Test Cards

Stripe provides test card numbers for development:

| Card Number | Description | Result |
|-------------|-------------|--------|
| `4242 4242 4242 4242` | Visa | Success |
| `4000 0000 0000 0002` | Visa | Declined |
| `4000 0000 0000 9995` | Visa | Insufficient funds |
| `4000 0025 0000 3155` | Visa | 3D Secure required |
| `5555 5555 5555 4444` | Mastercard | Success |

**Any future expiry date and any 3-digit CVC will work.**

### Test Subscription Flow

```bash
# 1. Create customer
curl -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json"

# 2. Create subscription
curl -X POST http://localhost:8000/api/v1/subscriptions/create \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"price_id": "price_xxxxx"}'

# 3. Verify subscription
curl http://localhost:8000/api/v1/subscriptions/me \
  -H "Authorization: Bearer YOUR_JWT"
```

---

## Error Handling

```python
import stripe

try:
    payment_intent = stripe.PaymentIntent.create(
        amount=1000,
        currency="usd"
    )
except stripe.error.CardError as e:
    # Card was declined
    print(f"Card declined: {e.user_message}")
except stripe.error.RateLimitError:
    # Too many requests
    print("Rate limit exceeded")
except stripe.error.InvalidRequestError as e:
    # Invalid parameters
    print(f"Invalid request: {e}")
except stripe.error.AuthenticationError:
    # Invalid API key
    print("Authentication failed - check API key")
except stripe.error.APIConnectionError:
    # Network error
    print("Network error")
except stripe.error.StripeError as e:
    # Generic error
    print(f"Stripe error: {e}")
```

---

## Monitoring & Analytics

### Stripe Dashboard

Monitor payments at: https://dashboard.stripe.com/

**Key Metrics:**
- Successful payments
- Failed payments
- Subscription churn
- Revenue (MRR, ARR)
- Customer lifetime value

### Integration with DevSkyy

Use PostHog to track payment events:

```python
from posthog import Posthog
import os

posthog = Posthog(
    project_api_key=os.getenv("POSTHOG_API_KEY"),
    host='https://app.posthog.com'
)

# Track payment success
posthog.capture(
    user_id,
    'payment_succeeded',
    properties={
        'amount': 5000,
        'currency': 'usd',
        'payment_intent_id': payment_intent.id
    }
)

# Track subscription created
posthog.capture(
    user_id,
    'subscription_created',
    properties={
        'plan': 'pro',
        'amount': 2900,
        'interval': 'month'
    }
)
```

---

## Compliance

### PCI Compliance

Stripe handles PCI compliance for you when using:
- ✅ Stripe.js (card elements)
- ✅ Stripe Checkout
- ✅ Stripe Payment Links

**Never:**
- ❌ Store card numbers
- ❌ Store CVV codes
- ❌ Process cards server-side without PCI certification

### GDPR Compliance

```python
# Delete customer data (GDPR right to be forgotten)
stripe.Customer.delete("cus_xxxxx")

# Export customer data
customer = stripe.Customer.retrieve("cus_xxxxx")
subscriptions = stripe.Subscription.list(customer="cus_xxxxx")
payments = stripe.PaymentIntent.list(customer="cus_xxxxx")

# Return all data to customer
customer_data = {
    "customer": customer,
    "subscriptions": subscriptions,
    "payments": payments
}
```

---

## Cost Optimization

### Stripe Fees

**Standard pricing:**
- **2.9% + $0.30** per successful transaction
- **No monthly fees**
- **No setup fees**

**Volume discounts:**
- Contact Stripe for custom pricing if processing > $1M/month

### Tips to Reduce Costs

1. **Batch operations** - Combine multiple charges
2. **Use ACH** - Lower fees than cards (0.8%, capped at $5)
3. **Annual billing** - Get paid upfront, reduce churn
4. **Optimize failed payments** - Use Smart Retries

---

## Next Steps

### 1. Get Secret Key ⚠️

**CRITICAL:** You need your secret key to process payments!

1. Go to: https://dashboard.stripe.com/apikeys
2. Reveal and copy your secret key (`sk_live_...`)
3. Add to `.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_live_your_actual_key_here
   ```

### 2. Test Connection

```bash
python3 << 'PYEOF'
import stripe, os
from dotenv import load_dotenv
load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
account = stripe.Account.retrieve()
print(f"✅ Connected: {account.business_profile.name}")
PYEOF
```

### 3. Implement Payment Flow

See integration examples above for:
- Payment intents
- Subscriptions
- Webhooks
- Frontend forms

### 4. Set Up Webhooks

1. Create endpoint: `/api/v1/webhooks/stripe`
2. Register at: https://dashboard.stripe.com/webhooks
3. Add secret to `.env`

### 5. Go Live

1. Complete Stripe account verification
2. Switch from test mode to live mode
3. Update API keys in production `.env`
4. Monitor dashboard for payments

---

## Resources

- **Stripe Dashboard:** https://dashboard.stripe.com/
- **API Documentation:** https://stripe.com/docs/api
- **Python Library:** https://github.com/stripe/stripe-python
- **Stripe CLI:** https://stripe.com/docs/stripe-cli
- **Testing Guide:** https://stripe.com/docs/testing
- **Webhook Guide:** https://stripe.com/docs/webhooks
- **PCI Compliance:** https://stripe.com/docs/security/guide

---

## Troubleshooting

### Issue: Authentication Error

**Symptoms:** `stripe.error.AuthenticationError`

**Solution:**
- Verify secret key is correct in `.env`
- Check key starts with `sk_live_` or `sk_test_`
- Ensure no extra spaces in `.env`

### Issue: Card Declined

**Symptoms:** `stripe.error.CardError`

**Solution:**
- Check card number is valid
- Verify expiry date is future
- Check sufficient funds
- Try test card: `4242 4242 4242 4242`

### Issue: Webhook Signature Failed

**Symptoms:** `stripe.error.SignatureVerificationError`

**Solution:**
- Verify webhook secret is correct
- Check webhook endpoint URL is correct
- Use raw request body (not parsed JSON)

---

**Status:** ✅ Publishable Key Configured | ⚠️ Secret Key Needed
**Next:** Add secret key to `.env` and test connection
**Documentation:** Complete setup guide with examples

