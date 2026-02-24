# Preventing Duplicate Subscriptions for the Same Plan

This guide covers how to prevent a user from subscribing to the same plan twice, with both **backend** and **frontend** implementations tailored to the DMV app.

---

## Why This Matters

Stripe does **not** natively block duplicate subscriptions. Without protection, a user could:
- Click "Subscribe" multiple times and get charged twice
- Open multiple checkout tabs and complete payment on both
- Re-subscribe to the same plan they already have

---

## Current Protection (Already in Place)

Your `Subscription` model uses `OneToOneField` with `User`:

```python
# accounts/models.py
user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
```

This means each user can only have **one** `Subscription` row. However, Stripe can still create multiple subscriptions on the Stripe side if the checkout session is created without checking first.

---

## Backend Protection

### 1. Guard in `CreateCheckoutSessionView`

Add an active subscription check **before** creating a checkout session in `accounts/subscription_views.py`:

```python
class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        price_id = request.data.get('price_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')
        plan_tier = request.data.get('plan_tier')

        if not all([price_id, success_url, cancel_url]):
            return APIResponse.error(
                message="price_id, success_url, and cancel_url are required",
                error_code=ErrorCodes.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # --- Duplicate subscription check ---
        try:
            existing = Subscription.objects.get(user=request.user)
            if existing.has_access():
                # User already has an active subscription
                if existing.stripe_price_id == price_id:
                    return APIResponse.error(
                        message="You already have an active subscription to this plan",
                        error_code=ErrorCodes.VALIDATION_ERROR,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Different plan — suggest using change-plan endpoint instead
                    return APIResponse.error(
                        message="You already have an active subscription. Use the change-plan endpoint to switch plans.",
                        error_code=ErrorCodes.VALIDATION_ERROR,
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
        except Subscription.DoesNotExist:
            pass  # No subscription yet — proceed
        # --- End duplicate check ---

        try:
            session = StripeService.create_checkout_session(
                user=request.user,
                price_id=price_id,
                success_url=success_url,
                cancel_url=cancel_url,
                plan_tier=plan_tier
            )
            return APIResponse.success(
                data={
                    'session_id': session.id,
                    'url': session.url,
                    'publishable_key': settings.STRIPE_PUBLISHABLE_KEY
                },
                message="Checkout session created successfully"
            )
        except Exception as e:
            return APIResponse.error(
                message="Failed to create checkout session",
                error_code=ErrorCodes.INTERNAL_SERVER_ERROR,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 2. Webhook Safety Net

In `accounts/stripe_service.py`, the `_handle_subscription_created` webhook handler can detect and cancel duplicate Stripe subscriptions:

```python
@staticmethod
def _handle_subscription_created(stripe_subscription):
    """Handle subscription.created event with duplicate protection."""
    try:
        subscription = Subscription.objects.get(
            stripe_customer_id=stripe_subscription['customer']
        )

        # If user already has a different active subscription in Stripe, cancel the new one
        if (subscription.stripe_subscription_id
                and subscription.stripe_subscription_id != stripe_subscription['id']
                and subscription.status in ['active', 'trialing']):
            logger.warning(
                f"Duplicate subscription detected for customer {stripe_subscription['customer']}. "
                f"Cancelling new subscription {stripe_subscription['id']}"
            )
            stripe.Subscription.cancel(stripe_subscription['id'])
            return

        # Normal flow — update subscription record
        subscription.stripe_subscription_id = stripe_subscription['id']
        subscription.status = stripe_subscription['status']
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            stripe_subscription['current_period_start'], tz=timezone.utc
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            stripe_subscription['current_period_end'], tz=timezone.utc
        )
        subscription.save()
        logger.info(f"Subscription created: {subscription.stripe_subscription_id}")
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found for customer {stripe_subscription['customer']}")
```

---

## Frontend Protection

### 1. Check Subscription Status Before Showing Subscribe Button

```javascript
// React / React Native example
const [subscription, setSubscription] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  checkSubscriptionStatus();
}, []);

const checkSubscriptionStatus = async () => {
  try {
    const response = await fetch('/api/accounts/subscription/status/', {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });
    const data = await response.json();
    if (data.success) {
      setSubscription(data.data);
    }
  } catch (error) {
    console.error('Failed to check subscription:', error);
  } finally {
    setLoading(false);
  }
};
```

### 2. Conditionally Render Subscribe vs Manage

```jsx
const PricingCard = ({ plan, priceId }) => {
  const isCurrentPlan = subscription?.has_access && subscription?.stripe_price_id === priceId;
  const hasAnyActivePlan = subscription?.has_access;

  if (isCurrentPlan) {
    return (
      <div className="pricing-card current">
        <span className="badge">Current Plan</span>
        <h3>{plan.name}</h3>
        <p>{plan.price}</p>
        <button onClick={manageSubscription} className="btn-secondary">
          Manage Subscription
        </button>
      </div>
    );
  }

  if (hasAnyActivePlan) {
    return (
      <div className="pricing-card">
        <h3>{plan.name}</h3>
        <p>{plan.price}</p>
        <button onClick={() => handleChangePlan(priceId, plan.tier)} className="btn-primary">
          Switch to This Plan
        </button>
      </div>
    );
  }

  return (
    <div className="pricing-card">
      <h3>{plan.name}</h3>
      <p>{plan.price}</p>
      <button onClick={() => handleSubscribe(priceId, plan.tier)} className="btn-primary">
        Subscribe
      </button>
    </div>
  );
};
```

### 3. Prevent Double-Click on Subscribe Button

```javascript
const [isProcessing, setIsProcessing] = useState(false);

const handleSubscribe = async (priceId, planTier) => {
  if (isProcessing) return;  // Block duplicate clicks
  setIsProcessing(true);

  try {
    const response = await fetch('/api/accounts/subscription/checkout/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        price_id: priceId,
        success_url: `${window.location.origin}/success`,
        cancel_url: `${window.location.origin}/pricing`,
        plan_tier: planTier,
      }),
    });

    const data = await response.json();

    if (data.success) {
      window.location.href = data.data.url;  // Redirect to Stripe Checkout
    } else {
      // Show error (e.g., "You already have an active subscription to this plan")
      alert(data.error || 'Something went wrong');
      setIsProcessing(false);
    }
  } catch (error) {
    console.error('Subscription error:', error);
    setIsProcessing(false);
  }
};
```

### 4. Handle Change Plan (Instead of New Subscription)

```javascript
const handleChangePlan = async (newPriceId, newTier) => {
  if (isProcessing) return;
  setIsProcessing(true);

  try {
    const response = await fetch('/api/accounts/subscription/change-plan/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        new_price_id: newPriceId,
        new_plan_tier: newTier,
      }),
    });

    const data = await response.json();

    if (data.success) {
      // Refresh subscription status
      await checkSubscriptionStatus();
      alert('Plan changed successfully!');
    } else {
      alert(data.error || 'Failed to change plan');
    }
  } catch (error) {
    console.error('Change plan error:', error);
  } finally {
    setIsProcessing(false);
  }
};
```

### 5. Manage Subscription (Billing Portal)

```javascript
const manageSubscription = async () => {
  try {
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
  } catch (error) {
    console.error('Portal error:', error);
  }
};
```

---

## Summary: Defense in Depth

| Layer | What It Does |
|-------|-------------|
| **Frontend: Status check** | Hides subscribe button when user already has an active plan |
| **Frontend: Double-click guard** | `isProcessing` state prevents multiple rapid clicks |
| **Frontend: Plan-aware UI** | Shows "Switch Plan" for active users instead of "Subscribe" |
| **Backend: View check** | `CreateCheckoutSessionView` rejects checkout if user has active subscription to same plan |
| **Backend: OneToOne model** | Database constraint ensures only one subscription row per user |
| **Backend: Webhook guard** | Cancels duplicate Stripe subscriptions if they slip through |

### API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/accounts/subscription/status/` | GET | Check current subscription status |
| `/api/accounts/subscription/checkout/` | POST | Create new subscription (blocked if already active) |
| `/api/accounts/subscription/change-plan/` | POST | Switch between plans (starter/standard/premium) |
| `/api/accounts/subscription/portal/` | POST | Open Stripe billing portal |
| `/api/accounts/subscription/cancel/` | POST | Cancel at period end |
| `/api/accounts/subscription/reactivate/` | POST | Reactivate cancelled subscription |
