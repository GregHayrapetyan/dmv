"""
Provider ownership of the one-per-user Subscription row: a new Stripe purchase takes the row
from a lapsed Apple sub (and vice versa), and late events from the previous provider must
not overwrite it.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import Subscription
from accounts.stripe_service import StripeService

User = get_user_model()


class StripeProviderOwnershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='xplat@example.com', password='pw12345678', is_email_verified=True
        )

    def _lapsed_apple_sub(self, **extra):
        fields = dict(
            user=self.user, payment_provider='apple', status='expired',
            apple_original_transaction_id='1000000000123', apple_product_id='com.mytestdmv.standard',
            plan_tier='standard', stripe_customer_id='cus_x', cancel_at_period_end=True,
            current_period_end=timezone.now() - timedelta(days=1),
        )
        fields.update(extra)
        return Subscription.objects.create(**fields)

    @patch('accounts.stripe_service.stripe.PaymentMethod.list', side_effect=Exception('offline'))
    @patch('accounts.stripe_service.stripe.Subscription.retrieve', side_effect=Exception('offline'))
    def test_checkout_completed_moves_lapsed_apple_sub_to_stripe(self, _retrieve, _pm_list):
        sub = self._lapsed_apple_sub()

        StripeService._handle_checkout_completed({
            'id': 'cs_1', 'mode': 'subscription', 'customer': 'cus_x', 'subscription': 'sub_new',
            'metadata': {'user_id': str(self.user.id), 'plan_tier': 'premium', 'price_id': 'price_p'},
        })

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'stripe')
        self.assertEqual(sub.stripe_subscription_id, 'sub_new')
        self.assertEqual(sub.status, 'active')
        self.assertFalse(sub.cancel_at_period_end)

    def test_subscription_created_moves_lapsed_apple_sub_to_stripe(self):
        sub = self._lapsed_apple_sub()

        StripeService._handle_subscription_created({'id': 'sub_new', 'customer': 'cus_x', 'status': 'active'})

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'stripe')
        self.assertEqual(sub.stripe_subscription_id, 'sub_new')
        self.assertFalse(sub.cancel_at_period_end)

    def test_late_stripe_events_do_not_touch_apple_owned_sub(self):
        # User left Stripe for Apple; the old Stripe sub id is still on the row.
        end = timezone.now() + timedelta(days=20)
        sub = self._lapsed_apple_sub(
            status='active', stripe_subscription_id='sub_old', cancel_at_period_end=False,
            current_period_end=end,
        )

        StripeService._handle_subscription_deleted({'id': 'sub_old'})
        StripeService._handle_subscription_updated({
            'id': 'sub_old', 'status': 'canceled', 'cancel_at_period_end': True,
        })
        StripeService._handle_payment_failed({'subscription': 'sub_old'})

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'apple')
        self.assertEqual(sub.status, 'active')
        self.assertFalse(sub.cancel_at_period_end)
        self.assertEqual(sub.current_period_end, end)

    def test_sync_from_stripe_skips_apple_owned_sub(self):
        self._lapsed_apple_sub(status='incomplete')
        with patch('accounts.stripe_service.stripe.Subscription.list') as stripe_list:
            self.assertIsNone(StripeService.sync_subscription_from_stripe(self.user))
        stripe_list.assert_not_called()

    def test_stripe_management_actions_refuse_apple_owned_sub(self):
        self._lapsed_apple_sub(status='active', stripe_subscription_id='sub_old')
        with patch('accounts.stripe_service.stripe.Subscription.modify') as modify:
            for action in (
                lambda: StripeService.cancel_subscription(self.user),
                lambda: StripeService.reactivate_subscription(self.user),
                lambda: StripeService.change_plan(self.user, 'price_p', 'premium'),
            ):
                with self.assertRaisesMessage(ValueError, 'purchased through Apple'):
                    action()
        modify.assert_not_called()

    def test_stripe_owned_sub_still_updated_by_webhooks(self):
        sub = Subscription.objects.create(
            user=self.user, payment_provider='stripe', status='active',
            stripe_customer_id='cus_x', stripe_subscription_id='sub_1',
        )
        StripeService._handle_subscription_deleted({'id': 'sub_1'})
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'canceled')
