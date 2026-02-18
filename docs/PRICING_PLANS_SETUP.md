# Pricing Plans Setup Guide

## Overview

Your DMV app now has **3 time-limited access plans** that users can purchase as one-time payments:

| Plan | Price | Duration | Description |
|------|-------|----------|-------------|
| **Starter** | $9.99 | 7 days | Quick preparation for last-minute test-takers |
| **Standard** | $19.99 | 30 days | Most Popular - Comprehensive study time |
| **Premium** | $29.99 | 90 days | Best Value - Extended access for thorough prep |

## How It Works

### One-Time Payments (Not Recurring Subscriptions)

Unlike traditional subscriptions that charge monthly, your plans are **one-time purchases** that grant time-limited access:

1. User selects a plan (Starter, Standard, or Premium)
2. User completes one-time payment via Stripe Checkout
3. System automatically grants access for the specified duration (7/30/90 days)
4. Access expires after the duration ends
5. User can purchase again to renew access

### Database Structure

The `Subscription` model now tracks:
- `plan_tier`: Which plan the user purchased (starter/standard/premium)
- `access_duration_days`: How many days of access (7/30/90)
- `is_one_time_purchase`: True for these plans
- `current_period_end`: When access expires
- `stripe_price_id`: Which Stripe Price ID was used

## Stripe Setup

### Step 1: Create Products in Stripe

Go to [Stripe Dashboard → Products](https://dashboard.stripe.com/products) and create **3 products**:

#### Product 1: Starter Plan
- **Name**: DMV Starter - 7 Days Access
- **Description**: 7 days of full access to DMV test preparation
- **Pricing**: One-time payment
- **Price**: $9.99 USD
- **Copy the Price ID**: It will look like `price_ABC123...`

#### Product 2: Standard Plan
- **Name**: DMV Standard - 30 Days Access
- **Description**: 30 days of full access to DMV test preparation
- **Pricing**: One-time payment
- **Price**: $19.99 USD
- **Copy the Price ID**: It will look like `price_DEF456...`

#### Product 3: Premium Plan
- **Name**: DMV Premium - 90 Days Access
- **Description**: 90 days of full access to DMV test preparation
- **Pricing**: One-time payment
- **Price**: $29.99 USD
- **Copy the Price ID**: It will look like `price_GHI789...`

### Step 2: Update PricingPlan Records

After running migrations, update the pricing plans in Django Admin or via migration:

1. Go to Django Admin → **Site Details** → **Pricing Plans**
2. Edit each plan and add the corresponding Stripe Price ID:
   - **Starter**: Add `price_ABC123...` to `stripe_price_id_one_time`
   - **Standard**: Add `price_DEF456...` to `stripe_price_id_one_time`
   - **Premium**: Add `price_GHI789...` to `stripe_price_id_one_time`

### Step 3: Configure Webhooks

You **must** add the `checkout.session.completed` event to your webhook configuration.

#### For Local Development:
```bash
stripe listen --forward-to http://localhost:8000/api/accounts/subscription/webhook/
```

The Stripe CLI automatically forwards all events including `checkout.session.completed`.

#### For Production:
1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks)
2. Click on your webhook endpoint
3. Click **"Add events"**
4. Add these events:
   - ✓ `checkout.session.completed` **(CRITICAL - New!)**
   - ✓ `customer.subscription.created`
   - ✓ `customer.subscription.updated`
   - ✓ `customer.subscription.deleted`
   - ✓ `invoice.payment_succeeded`
   - ✓ `invoice.payment_failed`

## Running Migrations

```bash
source venv/bin/activate
python manage.py migrate accounts
python manage.py migrate site_details
```

This will:
- Add new fields to `Subscription` model
- Create the 3 pricing plans with features

## API Usage

### Frontend Checkout Flow

When a user clicks on a pricing plan, make a POST request with the `plan_tier`:

```javascript
// User clicks "Get Started" on Standard plan
const response = await fetch('/api/accounts/subscription/checkout/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    price_id: 'price_DEF456...',  // Stripe Price ID for Standard
    plan_tier: 'standard',         // Important: tells system which plan
    success_url: `${window.location.origin}/success`,
    cancel_url: `${window.location.origin}/pricing`,
  }),
});

const data = await response.json();
if (data.success) {
  // Redirect to Stripe Checkout
  window.location.href = data.data.url;
}
```

### Plan Tier Values

- `starter` → 7 days access
- `standard` → 30 days access
- `premium` → 90 days access

### Check Subscription Status

```javascript
const response = await fetch('/api/accounts/subscription/status/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  },
});

const data = await response.json();
console.log(data.data);
// {
//   "id": 1,
//   "status": "active",
//   "plan_tier": "standard",
//   "access_duration_days": 30,
//   "is_one_time_purchase": true,
//   "current_period_end": "2024-02-15T00:00:00Z",
//   "plan_display_name": "Standard - 30 Days Access",
//   "days_remaining": 25,
//   "has_access": true
// }
```

## How Webhooks Process Payments

1. User completes payment in Stripe Checkout
2. Stripe sends `checkout.session.completed` webhook
3. Your system processes it in `StripeService._handle_checkout_completed()`:
   - Extracts `plan_tier` from session metadata
   - Maps tier to duration: `starter=7`, `standard=30`, `premium=90`
   - Creates/updates Subscription record
   - Sets `current_period_end` to `now + duration_days`
   - Sets status to `active`

## Access Control

The `has_access()` method automatically checks:
1. Is subscription status `active` or `trialing`?
2. Is `current_period_end` in the future?

When access expires, users will need to purchase again.

## Testing

### Test the Flow

1. **Create a test user**
2. **Start checkout** with test data:
   ```json
   {
     "price_id": "price_your_test_price",
     "plan_tier": "starter",
     "success_url": "http://localhost:3000/success",
     "cancel_url": "http://localhost:3000/pricing"
   }
   ```
3. **Complete payment** using test card: `4242 4242 4242 4242`
4. **Check subscription** - should show:
   - `plan_tier: "starter"`
   - `access_duration_days: 7`
   - `days_remaining: 7`
5. **Access content** - should be allowed

### Test Expiration

To test expiration, you can manually update `current_period_end` in the database to a past date, then verify `has_access()` returns `False`.

## Upgrading/Downgrading

With one-time purchases, users can:
- **Buy again** after access expires
- **Buy a different tier** while current access is active (extends or replaces access)

The system will update their subscription with the new tier and access duration.

## Admin Interface

Go to Django Admin → **Accounts** → **Subscriptions** to see:
- Which plan tier each user has
- How many days remain
- When access expires
- Whether it's a one-time purchase or recurring subscription

## Pricing Display

The frontend can fetch all pricing plans:

```bash
GET /api/site-details/pricing-plans/
```

This returns all 3 plans with:
- Pricing details
- Feature lists
- Stripe Price IDs
- Display order (Standard is `is_featured=True`)

## Key Differences from Recurring Subscriptions

| Feature | One-Time Purchase | Recurring Subscription |
|---------|------------------|----------------------|
| Payment | Single charge | Monthly/yearly charges |
| Cancellation | Not needed (auto-expires) | User must cancel |
| Renewal | Manual repurchase | Automatic |
| Stripe Mode | `payment` | `subscription` |
| Webhook | `checkout.session.completed` | `customer.subscription.*` |

## Troubleshooting

### Payment succeeds but no access granted

- Check webhook logs for `checkout.session.completed` event
- Verify `plan_tier` was included in checkout request
- Check Django logs for errors in `_handle_checkout_completed()`

### Access expires immediately

- Verify `access_duration_days` is set correctly
- Check `current_period_end` timestamp
- Ensure server timezone is configured properly

### Webhook not received

- Verify webhook endpoint is accessible
- Check Stripe Dashboard → Webhooks → Recent deliveries
- Ensure `checkout.session.completed` is in the event list
- For local dev, ensure Stripe CLI is running

## Production Checklist

- [ ] Create 3 Stripe Products with one-time prices
- [ ] Update PricingPlan records with Stripe Price IDs
- [ ] Configure webhook to listen for `checkout.session.completed`
- [ ] Test complete purchase flow in test mode
- [ ] Verify access expires correctly
- [ ] Switch to live Stripe keys
- [ ] Test with real payment in live mode
- [ ] Monitor webhook deliveries

## Support

For questions about:
- **Stripe setup**: Check Stripe documentation or dashboard
- **Webhook issues**: Check webhook delivery logs in Stripe
- **Access issues**: Check Django admin and application logs
