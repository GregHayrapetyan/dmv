# Stripe Integration Guide for DMV App

This guide explains how to set up and use Stripe subscriptions in your Django DMV application.

## Overview

The integration allows you to:
- **Charge users** for access to premium lessons and tests
- **Demo tests** remain free (marked with `is_demo=True`)
- **All lessons** require an active subscription
- **Premium tests** (non-demo) require an active subscription
- **Manage subscriptions** through Stripe's billing portal

## Architecture

### Models
- **`Subscription`** (`accounts/models.py`): Tracks user subscription status, Stripe customer ID, and subscription details

### Services
- **`StripeService`** (`accounts/stripe_service.py`): Handles all Stripe API interactions
  - Create customers
  - Create checkout sessions
  - Handle webhooks
  - Manage subscriptions

### Views
- **`CreateCheckoutSessionView`**: Creates Stripe checkout for new subscriptions
- **`CreateBillingPortalSessionView`**: Opens Stripe portal for managing subscriptions
- **`SubscriptionStatusView`**: Returns current subscription status
- **`CancelSubscriptionView`**: Cancels subscription at period end
- **`StripeWebhookView`**: Receives Stripe webhook events

### Permissions
- **`HasActiveSubscriptionOrDemo`**: Checks if user has access (for tests with demo flag)
- **`HasActiveSubscription`**: Requires active subscription (for lessons)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `stripe==7.8.0` along with other dependencies.

### 2. Create Stripe Account

1. Go to [https://stripe.com](https://stripe.com) and create an account
2. Use **Test Mode** for development (toggle in dashboard)

### 3. Get Stripe API Keys

1. Go to [https://dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys)
2. Copy your **Publishable key** (starts with `pk_test_`)
3. Copy your **Secret key** (starts with `sk_test_`)

### 4. Create Subscription Product and Price

1. Go to [https://dashboard.stripe.com/products](https://dashboard.stripe.com/products)
2. Click **"Add product"**
3. Fill in:
   - **Name**: "DMV Premium Access" (or your choice)
   - **Description**: "Access to all lessons and premium tests"
   - **Pricing model**: Recurring
   - **Price**: e.g., $9.99/month
   - **Billing period**: Monthly (or your choice)
4. Click **"Save product"**
5. **Copy the Price ID** (starts with `price_`) - you'll need this for checkout

### 5. Configure Environment Variables

Create or update your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret  # Get this in step 6
```

### 6. Set Up Webhooks (Important!)

Webhooks keep your database in sync with Stripe subscription changes.

#### For Local Development (using Stripe CLI):

1. Install Stripe CLI: [https://stripe.com/docs/stripe-cli](https://stripe.com/docs/stripe-cli)

2. Login to Stripe CLI:
   ```bash
   stripe login
   ```

3. Forward webhooks to your local server:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/accounts/subscription/webhook/
   ```

4. Copy the **webhook signing secret** (starts with `whsec_`) and add to `.env`

#### For Production:

1. Go to [https://dashboard.stripe.com/webhooks](https://dashboard.stripe.com/webhooks)
2. Click **"Add endpoint"**
3. Enter your endpoint URL: `https://yourdomain.com/api/accounts/subscription/webhook/`
4. Select events to listen to:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copy the **Signing secret** and add to your production `.env`

### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Create Superuser (if not already done)

```bash
python manage.py createsuperuser
```

### 9. Start Development Server

```bash
python manage.py runserver
```

## API Endpoints

### Subscription Management

#### 1. Create Checkout Session
**POST** `/api/accounts/subscription/checkout/`

Creates a Stripe Checkout session to start a subscription.

**Request:**
```json
{
  "price_id": "price_1234567890",
  "success_url": "http://localhost:3000/success",
  "cancel_url": "http://localhost:3000/cancel"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "cs_test_...",
    "url": "https://checkout.stripe.com/c/pay/cs_test_...",
    "publishable_key": "pk_test_..."
  },
  "message": "Checkout session created successfully"
}
```

**Usage:** Redirect user to the `url` to complete payment.

#### 2. Get Subscription Status
**GET** `/api/accounts/subscription/status/`

Returns current subscription status for authenticated user.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "active",
    "current_period_start": "2024-01-01T00:00:00Z",
    "current_period_end": "2024-02-01T00:00:00Z",
    "cancel_at_period_end": false,
    "has_access": true
  }
}
```

#### 3. Create Billing Portal Session
**POST** `/api/accounts/subscription/portal/`

Creates a session for Stripe's customer portal (manage payment, cancel, etc.).

**Request:**
```json
{
  "return_url": "http://localhost:3000/account"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://billing.stripe.com/session/..."
  }
}
```

#### 4. Cancel Subscription
**POST** `/api/accounts/subscription/cancel/`

Cancels subscription at the end of current billing period.

**Response:**
```json
{
  "success": true,
  "message": "Subscription will be cancelled at the end of the current billing period"
}
```

### Content Access

#### Lessons
- **GET** `/api/learning/lessons/{slug}/` - Requires active subscription
- Returns 403 if no active subscription

#### Tests
- **GET** `/api/learning/tests/{id}/` - Free for demo tests, requires subscription for premium
- **POST** `/api/learning/tests/{id}/submit/` - Same access rules as GET

## Frontend Integration Example

### React/Next.js Example

```javascript
// Subscribe to premium
const handleSubscribe = async () => {
  try {
    const response = await fetch('/api/accounts/subscription/checkout/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        price_id: 'price_1234567890', // Your Stripe price ID
        success_url: `${window.location.origin}/success`,
        cancel_url: `${window.location.origin}/cancel`,
      }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Redirect to Stripe Checkout
      window.location.href = data.data.url;
    }
  } catch (error) {
    console.error('Subscription error:', error);
  }
};

// Check subscription status
const checkSubscription = async () => {
  const response = await fetch('/api/accounts/subscription/status/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  
  const data = await response.json();
  
  if (data.success && data.data.has_access) {
    console.log('User has active subscription');
  }
};

// Manage subscription (billing portal)
const manageSubscription = async () => {
  const response = await fetch('/api/accounts/subscription/portal/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      return_url: `${window.location.origin}/account`,
    }),
  });
  
  const data = await response.json();
  
  if (data.success) {
    window.location.href = data.data.url;
  }
};
```

## Testing

### Test Mode

Stripe provides test card numbers for testing:

- **Success**: `4242 4242 4242 4242`
- **Requires authentication**: `4000 0025 0000 3155`
- **Declined**: `4000 0000 0000 0002`

Use any future expiry date, any 3-digit CVC, and any ZIP code.

### Testing Webhooks Locally

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```

2. In another terminal, start Stripe CLI webhook forwarding:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/accounts/subscription/webhook/
   ```

3. Trigger test events:
   ```bash
   stripe trigger customer.subscription.created
   stripe trigger invoice.payment_succeeded
   ```

### Manual Testing Flow

1. **Register a user** via `/api/accounts/register/`
2. **Login** via `/api/accounts/login/`
3. **Create checkout session** with your price ID
4. **Complete payment** using test card `4242 4242 4242 4242`
5. **Check subscription status** - should show `active`
6. **Access a lesson** - should work now
7. **Access a premium test** - should work now
8. **Try accessing without subscription** - should return 403

## Database Schema

### Subscription Model Fields

- `user` - OneToOne relationship with User
- `stripe_customer_id` - Stripe customer ID (unique)
- `stripe_subscription_id` - Stripe subscription ID (unique)
- `status` - Subscription status (active, canceled, past_due, etc.)
- `current_period_start` - Start of current billing period
- `current_period_end` - End of current billing period
- `cancel_at_period_end` - Whether subscription will cancel at period end
- `created_at` - When subscription was created
- `updated_at` - Last update timestamp

## Subscription Statuses

- **`active`** - Subscription is active and paid
- **`trialing`** - In trial period (if you set up trials)
- **`past_due`** - Payment failed, retrying
- **`canceled`** - Subscription has been canceled
- **`incomplete`** - Initial payment not completed
- **`unpaid`** - Payment failed and no retry

## Admin Interface

Access Django admin at `/admin/` to:
- View all subscriptions
- Check subscription status
- See Stripe customer and subscription IDs
- Monitor subscription periods

## Security Considerations

1. **Never expose secret keys** - Keep `STRIPE_SECRET_KEY` in environment variables
2. **Verify webhook signatures** - Already implemented in `StripeWebhookView`
3. **Use HTTPS in production** - Required for Stripe webhooks
4. **Validate price IDs** - Consider storing allowed price IDs in settings

## Troubleshooting

### Webhooks not working
- Check webhook secret is correct
- Ensure webhook URL is accessible
- Check Django logs for errors
- Verify Stripe CLI is running (local dev)

### Subscription not updating
- Check webhook events in Stripe Dashboard
- Verify webhook endpoint is receiving events
- Check Django logs for webhook processing errors

### User can't access content
- Verify subscription status is `active` or `trialing`
- Check `current_period_end` is in the future
- Ensure user is authenticated

### Payment fails
- Check Stripe Dashboard for payment details
- Verify test card numbers in test mode
- Check for any Stripe account issues

## Production Checklist

- [ ] Switch to live Stripe keys (remove `_test_` keys)
- [ ] Set up production webhook endpoint
- [ ] Configure HTTPS
- [ ] Set up proper error monitoring
- [ ] Test subscription flow end-to-end
- [ ] Set up email notifications for failed payments
- [ ] Configure Stripe billing portal settings
- [ ] Set up tax collection (if applicable)
- [ ] Review Stripe security best practices

## Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Subscriptions](https://stripe.com/docs/billing/subscriptions/overview)
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)

## Support

For issues related to:
- **Stripe integration**: Check Stripe Dashboard and logs
- **Django errors**: Check Django logs and console
- **Payment issues**: Contact Stripe support
