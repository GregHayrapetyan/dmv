"""Helpers for joining a Subscription to CMS PricingPlan price IDs."""
from django.db import models

from site_details.models import PricingPlan


def resolve_subscription_price_fields(subscription):
    """
    Return (stripe_price_id_monthly, stripe_price_id_one_time) for the pricing UI.

    Prefers an active PricingPlan matched by purchased Stripe price ID, then by
    plan tier (English title or /checkout/<tier> button_url). Always falls back
    to the subscription's purchased price for monthly when CMS IDs are blank so
    the client can still mark the current plan active.
    """
    purchased_price_id = (subscription.stripe_price_id or '').strip() or None
    pricing_plan = None

    if purchased_price_id:
        pricing_plan = PricingPlan.objects.filter(
            is_active=True,
        ).filter(
            models.Q(stripe_price_id_monthly=purchased_price_id) |
            models.Q(stripe_price_id_one_time=purchased_price_id)
        ).first()

    if not pricing_plan and subscription.plan_tier:
        pricing_plan = PricingPlan.objects.filter(
            is_active=True,
        ).filter(
            models.Q(title__iexact=subscription.plan_tier) |
            models.Q(button_url__iendswith=f'/{subscription.plan_tier}')
        ).first()

    monthly = None
    one_time = None
    if pricing_plan:
        monthly = (pricing_plan.stripe_price_id_monthly or '').strip() or None
        one_time = (pricing_plan.stripe_price_id_one_time or '').strip() or None

    if not monthly and purchased_price_id:
        monthly = purchased_price_id

    return monthly, one_time
