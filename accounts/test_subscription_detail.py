"""Subscription detail/status payloads used by the pricing "Now Active" badge."""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import Subscription
from accounts.serializers import SubscriptionSerializer
from accounts.subscription_pricing import resolve_subscription_price_fields
from site_details.models import PricingPlan

User = get_user_model()


@override_settings(ROOT_URLCONF='accounts.test_urls_subscription')
class SubscriptionDetailActivePlanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='active-plan@example.com', password='pw12345678', is_email_verified=True
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.period_end = timezone.now() + timedelta(days=30)

        self.starter = PricingPlan.objects.create(
            title='Starter',
            button_url='/checkout/starter',
            price_new=9.99,
            order=0,
            is_active=True,
            stripe_price_id_monthly='',  # seeded empty — common misconfig
        )
        self.standard = PricingPlan.objects.create(
            title='Standard',
            button_url='/checkout/standard',
            price_new=19.99,
            order=1,
            is_active=True,
            stripe_price_id_monthly='price_standard',
        )

    def _active_stripe(self, **extra):
        fields = dict(
            user=self.user,
            payment_provider='stripe',
            status='active',
            plan_tier='standard',
            stripe_price_id='price_standard',
            stripe_customer_id='cus_active',
            stripe_subscription_id='sub_active',
            current_period_end=self.period_end,
            cancel_at_period_end=False,
        )
        fields.update(extra)
        return Subscription.objects.create(**fields)

    def test_resolve_falls_back_to_purchased_price_when_cms_ids_empty(self):
        sub = SimpleNamespace(stripe_price_id='price_live_starter', plan_tier='starter')
        monthly, _ = resolve_subscription_price_fields(sub)
        self.assertEqual(monthly, 'price_live_starter')

    def test_resolve_matches_cms_plan_by_price_id(self):
        sub = SimpleNamespace(stripe_price_id='price_standard', plan_tier='standard')
        monthly, _ = resolve_subscription_price_fields(sub)
        self.assertEqual(monthly, 'price_standard')

    def test_resolve_skips_empty_string_price_matches(self):
        sub = SimpleNamespace(stripe_price_id='', plan_tier='standard')
        monthly, _ = resolve_subscription_price_fields(sub)
        # No purchased price; CMS Standard monthly is set, but we only fill from
        # a PricingPlan match — tier match still finds Standard.
        self.assertEqual(monthly, 'price_standard')

    def test_resolve_tier_fallback_when_price_unknown(self):
        sub = SimpleNamespace(stripe_price_id='price_unknown_elsewhere', plan_tier='starter')
        monthly, _ = resolve_subscription_price_fields(sub)
        # Tier finds Starter (blank CMS monthly) → fall back to purchased ID.
        self.assertEqual(monthly, 'price_unknown_elsewhere')

    def test_serializer_includes_stripe_price_id(self):
        sub = self._active_stripe()
        data = SubscriptionSerializer(sub).data
        self.assertEqual(data['stripe_price_id'], 'price_standard')

    @patch('accounts.subscription_views.StripeService.get_billing_info', return_value=None)
    def test_detail_returns_purchased_price_when_cms_ids_empty(self, _billing):
        self._active_stripe(plan_tier='starter', stripe_price_id='price_live_starter')

        resp = self.client.get('/api/accounts/subscription/detail/')
        self.assertEqual(resp.status_code, 200)
        plan = resp.data['data']['plan']
        self.assertTrue(plan['has_access'])
        self.assertEqual(plan['stripe_price_id'], 'price_live_starter')
        self.assertEqual(plan['stripe_price_id_monthly'], 'price_live_starter')

    @patch('accounts.subscription_views.StripeService.get_billing_info', return_value=None)
    def test_detail_matches_cms_plan_by_price_id(self, _billing):
        self._active_stripe()

        resp = self.client.get('/api/accounts/subscription/detail/')
        self.assertEqual(resp.status_code, 200)
        plan = resp.data['data']['plan']
        self.assertEqual(plan['stripe_price_id_monthly'], 'price_standard')
        self.assertTrue(plan['has_access'])

    def test_status_includes_stripe_price_id(self):
        self._active_stripe()

        resp = self.client.get('/api/accounts/subscription/status/')
        self.assertEqual(resp.status_code, 200)
        plan = resp.data['data']
        self.assertEqual(plan['stripe_price_id'], 'price_standard')
        self.assertTrue(plan['has_access'])
