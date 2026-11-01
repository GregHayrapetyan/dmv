from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from accounts.models import Subscription
from accounts.stripe_service import StripeService

User = get_user_model()


@override_settings(STRIPE_TRIAL_PERIOD_DAYS=3)
class StripeTrialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='trial@example.com', password='pw12345678', is_email_verified=True
        )

    def _create_session(self):
        with patch('accounts.stripe_service.stripe.Customer.create',
                   return_value=SimpleNamespace(id='cus_test')), \
             patch('accounts.stripe_service.stripe.checkout.Session.create',
                   return_value=SimpleNamespace(id='cs_test', url='https://x')) as create:
            StripeService.create_checkout_session(
                self.user, 'price_x', 'https://ok', 'https://cancel', plan_tier='standard'
            )
        return create.call_args.kwargs

    def test_first_time_subscriber_gets_trial(self):
        kwargs = self._create_session()
        self.assertEqual(kwargs['subscription_data'], {'trial_period_days': 3})

    def test_returning_subscriber_gets_no_trial(self):
        Subscription.objects.create(
            user=self.user, stripe_customer_id='cus_test',
            stripe_subscription_id='sub_old', status='canceled'
        )
        kwargs = self._create_session()
        self.assertNotIn('subscription_data', kwargs)

    def test_abandoned_checkout_still_eligible(self):
        Subscription.objects.create(user=self.user, stripe_customer_id='cus_test', status='incomplete')
        kwargs = self._create_session()
        self.assertEqual(kwargs['subscription_data'], {'trial_period_days': 3})

    @override_settings(STRIPE_TRIAL_PERIOD_DAYS=0)
    def test_trial_disabled(self):
        kwargs = self._create_session()
        self.assertNotIn('subscription_data', kwargs)

    def test_zero_dollar_trial_invoice_keeps_trialing(self):
        sub = Subscription.objects.create(
            user=self.user, stripe_customer_id='cus_test',
            stripe_subscription_id='sub_1', status='trialing'
        )
        StripeService._handle_payment_succeeded({'subscription': 'sub_1', 'amount_paid': 0})
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'trialing')

        StripeService._handle_payment_succeeded({'subscription': 'sub_1', 'amount_paid': 1999})
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'active')

    def test_trialing_subscription_has_access(self):
        sub = Subscription.objects.create(user=self.user, status='trialing')
        self.assertTrue(sub.has_access())
