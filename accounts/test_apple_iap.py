"""
Tests for the Apple In-App Purchase (iOS) subscription path.

The cryptographic JWS/certificate-chain verification is exercised against Apple's
real signatures in sandbox; here we mock `decode_signed_jws` and focus on the
business logic: product->tier mapping, subscription activation, account-clash
protection, and server-notification handling. The Stripe path is untouched.
"""
import datetime
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.apple_iap_service import AppleIAPService, AppleIAPError
from accounts.models import Subscription

User = get_user_model()

TEST_PRODUCTS = {
    'com.mytestdmv.starter': 'starter',
    'com.mytestdmv.standard': 'standard',
    'com.mytestdmv.premium': 'premium',
}
TEST_BUNDLE = 'com.mytestdmv.app'


def make_transaction(product='com.mytestdmv.standard', original='1000000000123',
                     expires_in_days=30, purchased_days_ago=0, bundle=TEST_BUNDLE):
    now = timezone.now()
    return {
        'bundleId': bundle,
        'productId': product,
        'originalTransactionId': original,
        'transactionId': original,
        'purchaseDate': int((now - timedelta(days=purchased_days_ago)).timestamp() * 1000),
        'expiresDate': int((now + timedelta(days=expires_in_days)).timestamp() * 1000),
    }


@override_settings(APPLE_IAP_PRODUCTS=TEST_PRODUCTS, APPLE_IAP_BUNDLE_ID=TEST_BUNDLE)
class AppleIAPServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ios@example.com', password='pw12345678', is_email_verified=True
        )

    # -- product mapping -----------------------------------------------------

    def test_product_to_tier_maps_known_products(self):
        self.assertEqual(AppleIAPService.product_to_tier('com.mytestdmv.standard'), 'standard')
        self.assertEqual(AppleIAPService.product_to_tier('com.mytestdmv.premium'), 'premium')

    def test_product_to_tier_unknown_returns_none(self):
        self.assertIsNone(AppleIAPService.product_to_tier('com.mytestdmv.unknown'))

    # -- activation ----------------------------------------------------------

    def test_activate_creates_apple_subscription(self):
        txn = make_transaction(product='com.mytestdmv.standard')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            sub = AppleIAPService.activate_subscription(self.user, 'signed-jws')

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'apple')
        self.assertEqual(sub.plan_tier, 'standard')
        self.assertEqual(sub.access_duration_days, 30)
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.apple_original_transaction_id, '1000000000123')
        self.assertTrue(sub.has_access())

    def test_activate_updates_existing_stripe_subscription(self):
        # User already had a (say lapsed) Stripe subscription record.
        Subscription.objects.create(user=self.user, payment_provider='stripe',
                                    status='expired', stripe_customer_id='cus_x')
        txn = make_transaction(product='com.mytestdmv.premium')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            sub = AppleIAPService.activate_subscription(self.user, 'signed-jws')

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'apple')
        self.assertEqual(sub.plan_tier, 'premium')
        self.assertEqual(sub.status, 'active')

    def test_activate_rejects_transaction_owned_by_another_user(self):
        other = User.objects.create_user(email='other@example.com', password='pw12345678')
        Subscription.objects.create(
            user=other, payment_provider='apple',
            apple_original_transaction_id='1000000000123', status='active',
        )
        txn = make_transaction(original='1000000000123')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')

    def test_activate_blocked_when_active_subscription_on_another_provider(self):
        # An ACTIVE Stripe subscription must block a new Apple purchase (it would
        # double-bill). The iOS client also guards this before charging; this is
        # the server-side backstop. The Stripe record must NOT be overwritten.
        Subscription.objects.create(
            user=self.user, payment_provider='stripe', status='active',
            stripe_subscription_id='sub_x',
            current_period_end=timezone.now() + timedelta(days=15),
        )
        txn = make_transaction(product='com.mytestdmv.premium')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')

        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.payment_provider, 'stripe')
        self.assertEqual(sub.status, 'active')
        self.assertIsNone(sub.apple_original_transaction_id)

    def test_verify_rejects_wrong_bundle_id(self):
        txn = make_transaction(bundle='com.evil.app')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.verify_transaction('signed-jws')

    def test_verify_rejects_unknown_product(self):
        txn = make_transaction(product='com.mytestdmv.mystery')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.verify_transaction('signed-jws')

    # -- server notifications ------------------------------------------------

    def _existing_apple_sub(self, original='1000000000123', status='active'):
        return Subscription.objects.create(
            user=self.user, payment_provider='apple',
            apple_original_transaction_id=original, apple_product_id='com.mytestdmv.standard',
            plan_tier='standard', status=status,
            current_period_end=timezone.now() + timedelta(days=1),
        )

    def test_notification_did_renew_extends_and_activates(self):
        sub = self._existing_apple_sub(status='past_due')
        txn = make_transaction(expires_in_days=30)
        notification = {
            'notificationType': 'DID_RENEW', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        sub.refresh_from_db()
        self.assertEqual(sub.status, 'active')
        self.assertGreater(sub.current_period_end, timezone.now() + timedelta(days=20))

    def test_notification_refund_revokes_access(self):
        sub = self._existing_apple_sub()
        txn = make_transaction()
        notification = {
            'notificationType': 'REFUND', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        sub.refresh_from_db()
        self.assertEqual(sub.status, 'canceled')
        self.assertLessEqual(sub.current_period_end, timezone.now() + timedelta(seconds=5))
        self.assertFalse(sub.has_access())

    def test_notification_auto_renew_disabled_sets_cancel_flag(self):
        sub = self._existing_apple_sub()
        txn = make_transaction()
        notification = {
            'notificationType': 'DID_CHANGE_RENEWAL_STATUS', 'subtype': 'AUTO_RENEW_DISABLED',
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        sub.refresh_from_db()
        self.assertTrue(sub.cancel_at_period_end)

    def test_notification_for_unknown_transaction_is_ignored(self):
        txn = make_transaction(original='9999999999999')
        notification = {
            'notificationType': 'DID_RENEW', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            # Should not raise even though no subscription matches.
            AppleIAPService.handle_notification('signed-payload')


@override_settings(APPLE_IAP_PRODUCTS=TEST_PRODUCTS, APPLE_IAP_BUNDLE_ID=TEST_BUNDLE)
class AppleVerifyPurchaseEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ios2@example.com', password='pw12345678', is_email_verified=True
        )
        self.client = APIClient()
        self.url = reverse('subscription-apple-verify')

    def test_requires_authentication(self):
        resp = self.client.post(self.url, {'signed_transaction': 'x'}, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_missing_signed_transaction_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data['success'])

    def test_valid_purchase_returns_active_subscription(self):
        self.client.force_authenticate(self.user)
        txn = make_transaction(product='com.mytestdmv.standard')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            resp = self.client.post(self.url, {'signed_transaction': 'signed-jws'}, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['success'])
        self.assertEqual(resp.data['data']['status'], 'active')
        self.assertEqual(resp.data['data']['plan_tier'], 'standard')
        self.assertTrue(resp.data['data']['has_access'])

    def test_invalid_signature_returns_400(self):
        self.client.force_authenticate(self.user)
        with patch.object(AppleIAPService, 'decode_signed_jws',
                          side_effect=AppleIAPError('bad signature')):
            resp = self.client.post(self.url, {'signed_transaction': 'bad'}, format='json')

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.data['success'])
