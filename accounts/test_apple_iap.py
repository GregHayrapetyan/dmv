"""
Tests for the Apple IAP (iOS) path. We mock `decode_signed_jws` (signature checks are in
test_apple_jws.py) and focus on business logic: activation, account-clash protection,
revocation/expiry, and notification handling.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.apple_iap_service import AppleIAPService, AppleIAPError
from accounts.models import AppleRevokedTransaction, Subscription
from onboarding.models import State, Vehicle

User = get_user_model()

TEST_PRODUCTS = {
    'com.mytestdmv.starter': 'starter',
    'com.mytestdmv.standard': 'standard',
    'com.mytestdmv.premium': 'premium',
}
TEST_BUNDLE = 'com.mytestdmv.app'


def make_transaction(product='com.mytestdmv.standard', original='1000000000123',
                     expires_in_days=30, purchased_days_ago=0, bundle=TEST_BUNDLE,
                     revocation_date_ms=None):
    now = timezone.now()
    txn = {
        'bundleId': bundle,
        'productId': product,
        'originalTransactionId': original,
        'transactionId': original,
        'purchaseDate': int((now - timedelta(days=purchased_days_ago)).timestamp() * 1000),
        'expiresDate': int((now + timedelta(days=expires_in_days)).timestamp() * 1000),
    }
    if revocation_date_ms is not None:
        txn['revocationDate'] = revocation_date_ms
    return txn


@override_settings(APPLE_IAP_PRODUCTS=TEST_PRODUCTS, APPLE_IAP_BUNDLE_ID=TEST_BUNDLE)
class AppleIAPServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ios@example.com', password='pw12345678', is_email_verified=True
        )

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
                                    status='expired', stripe_customer_id='cus_x',
                                    cancel_at_period_end=True)
        txn = make_transaction(product='com.mytestdmv.premium')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            sub = AppleIAPService.activate_subscription(self.user, 'signed-jws')

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'apple')
        self.assertEqual(sub.plan_tier, 'premium')
        self.assertEqual(sub.status, 'active')
        self.assertFalse(sub.cancel_at_period_end)

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
        # An active Stripe sub must block a new Apple purchase (would double-bill); the Stripe record must survive.
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

    def test_activate_rejects_revoked_transaction(self):
        # A revoked (refunded) transaction carries revocationDate; activation must refuse it.
        now_ms = int(timezone.now().timestamp() * 1000)
        txn = make_transaction(product='com.mytestdmv.standard', revocation_date_ms=now_ms)
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    def test_activate_rejects_already_expired_transaction(self):
        # An already-expired transaction cannot grant current access.
        txn = make_transaction(product='com.mytestdmv.standard', expires_in_days=-1)
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    def test_activate_rejects_transaction_refunded_via_notification(self):
        AppleRevokedTransaction.objects.create(
            transaction_id='1000000000123', original_transaction_id='1000000000123'
        )
        txn = make_transaction(product='com.mytestdmv.standard')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    # -- guest purchase moved onto a real account ------------------------------

    def _guest_with_purchase(self, **kwargs):
        return AppleIAPService._create_guest_subscription(make_transaction(**kwargs)).user

    def test_activate_moves_guest_purchase_to_user(self):
        guest = self._guest_with_purchase()
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction()):
            sub = AppleIAPService.activate_subscription(self.user, 'signed-jws')

        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.apple_original_transaction_id, '1000000000123')
        self.assertTrue(sub.has_access())
        self.assertFalse(User.objects.filter(id=guest.id).exists())
        self.assertEqual(Subscription.objects.count(), 1)

    def test_activate_moves_guest_purchase_over_users_lapsed_subscription(self):
        Subscription.objects.create(user=self.user, payment_provider='stripe',
                                    status='expired', stripe_customer_id='cus_x')
        guest = self._guest_with_purchase(product='com.mytestdmv.premium')
        txn = make_transaction(product='com.mytestdmv.premium')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            AppleIAPService.activate_subscription(self.user, 'signed-jws')

        sub = Subscription.objects.get(user=self.user)
        self.assertEqual(sub.payment_provider, 'apple')
        self.assertEqual(sub.plan_tier, 'premium')
        self.assertEqual(sub.stripe_customer_id, 'cus_x')
        self.assertFalse(User.objects.filter(id=guest.id).exists())

    def test_activate_keeps_users_active_apple_subscription_and_the_guest(self):
        self._existing_apple_sub(original='2000000000456')
        guest = self._guest_with_purchase()
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction()):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')

        self.assertEqual(Subscription.objects.get(user=self.user).apple_original_transaction_id, '2000000000456')
        self.assertEqual(Subscription.objects.get(user=guest).apple_original_transaction_id, '1000000000123')

    def test_activate_keeps_users_active_stripe_subscription_and_the_guest(self):
        Subscription.objects.create(
            user=self.user, payment_provider='stripe', status='active',
            stripe_subscription_id='sub_x',
            current_period_end=timezone.now() + timedelta(days=15),
        )
        guest = self._guest_with_purchase()
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction()):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.activate_subscription(self.user, 'signed-jws')

        self.assertEqual(Subscription.objects.get(user=self.user).payment_provider, 'stripe')
        self.assertTrue(User.objects.filter(id=guest.id).exists())

    def test_guest_verify_of_own_purchase_syncs_renewal(self):
        guest = self._guest_with_purchase(expires_in_days=1)
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction(expires_in_days=31)):
            sub = AppleIAPService.activate_subscription(guest, 'signed-jws')

        self.assertEqual(sub.user, guest)
        self.assertGreater(sub.current_period_end, timezone.now() + timedelta(days=30))

    def test_verify_rejects_wrong_bundle_id(self):
        txn = make_transaction(bundle='com.evil.app')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.verify_transaction('signed-jws')

    def test_verify_rejects_transaction_without_bundle_id(self):
        txn = make_transaction()
        del txn['bundleId']
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.verify_transaction('signed-jws')

    @override_settings(APPLE_IAP_BUNDLE_ID='')
    def test_verify_fails_closed_when_bundle_id_not_configured(self):
        txn = make_transaction(bundle='com.any.app')
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(ImproperlyConfigured):
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

    def test_notification_ignored_after_user_moved_to_stripe(self):
        # Old Apple sub lapsed, user bought on the web: a late REFUND must not cut off Stripe access.
        end = timezone.now() + timedelta(days=20)
        sub = self._existing_apple_sub()
        sub.payment_provider = 'stripe'
        sub.stripe_subscription_id = 'sub_new'
        sub.current_period_end = end
        sub.save()
        txn = make_transaction()
        notification = {
            'notificationType': 'REFUND', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        sub.refresh_from_db()
        self.assertEqual(sub.payment_provider, 'stripe')
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.current_period_end, end)

    def test_notification_for_unknown_transaction_is_ignored(self):
        txn = make_transaction(original='9999999999999')
        notification = {
            'notificationType': 'DID_RENEW', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            # Should not raise even though no subscription matches.
            AppleIAPService.handle_notification('signed-payload')

    def test_notification_refund_for_unknown_transaction_blocks_guest_login(self):
        txn = make_transaction(original='5555555555555')
        notification = {
            'notificationType': 'REFUND', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        self.assertTrue(AppleRevokedTransaction.objects.filter(transaction_id='5555555555555').exists())
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            with self.assertRaises(AppleIAPError):
                AppleIAPService.guest_login('signed-jws')
        self.assertFalse(User.objects.filter(is_guest=True).exists())

    def test_notification_refund_reversed_allows_guest_login_again(self):
        AppleRevokedTransaction.objects.create(
            transaction_id='5555555555555', original_transaction_id='5555555555555'
        )
        txn = make_transaction(original='5555555555555')
        notification = {
            'notificationType': 'REFUND_REVERSED', 'subtype': None,
            'data': {'signedTransactionInfo': 'txn-jws'},
        }
        with patch.object(AppleIAPService, 'decode_signed_jws', side_effect=[notification, txn]):
            AppleIAPService.handle_notification('signed-payload')

        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            sub = AppleIAPService.guest_login('signed-jws')
        self.assertTrue(sub.user.is_guest)
        self.assertTrue(sub.has_access())


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


@override_settings(APPLE_IAP_PRODUCTS=TEST_PRODUCTS, APPLE_IAP_BUNDLE_ID=TEST_BUNDLE)
class AppleGuestLoginEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('subscription-apple-login')

    def _login(self, txn, **extra):
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=txn):
            return self.client.post(self.url, {'signed_transaction': 'signed-jws'}, format='json', **extra)

    def test_first_purchase_creates_guest_and_logs_in(self):
        resp = self._login(make_transaction(product='com.mytestdmv.premium'))

        self.assertEqual(resp.status_code, 200)
        data = resp.data['data']
        self.assertTrue(data['access'])
        self.assertTrue(data['is_guest'])
        self.assertTrue(data['has_access'])
        self.assertTrue(resp.cookies['refresh_token']['httponly'])
        guest = User.objects.get(id=data['user']['id'])
        self.assertTrue(guest.is_guest)
        self.assertFalse(guest.has_usable_password())
        self.assertFalse(guest.is_email_verified)
        self.assertEqual(guest.subscription.apple_original_transaction_id, '1000000000123')
        self.assertEqual(guest.subscription.plan_tier, 'premium')
        self.assertEqual(guest.subscription.status, 'active')

    def test_access_token_opens_me_as_guest(self):
        access = self._login(make_transaction()).data['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        resp = self.client.get(reverse('me'))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['data']['is_guest'])
        self.assertTrue(resp.data['data']['has_active_subscription'])

    def test_repeat_login_reuses_the_same_guest(self):
        first = self._login(make_transaction()).data['data']['user']['id']
        second = self._login(make_transaction()).data['data']['user']['id']

        self.assertEqual(first, second)
        self.assertEqual(User.objects.filter(is_guest=True).count(), 1)

    def test_expired_purchase_logs_in_without_access(self):
        resp = self._login(make_transaction(expires_in_days=-1))

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['data']['has_access'])
        self.assertEqual(Subscription.objects.get().status, 'expired')

    def test_newer_transaction_extends_guest_subscription_and_older_one_is_ignored(self):
        self._login(make_transaction(expires_in_days=5))
        renewal = make_transaction(expires_in_days=35)
        renewal['transactionId'] = '1000000000999'
        self._login(renewal)
        renewed_end = Subscription.objects.get().current_period_end

        self._login(make_transaction(expires_in_days=5))

        self.assertGreater(renewed_end, timezone.now() + timedelta(days=30))
        self.assertEqual(Subscription.objects.get().current_period_end, renewed_end)

    def test_revoked_purchase_is_rejected(self):
        now_ms = int(timezone.now().timestamp() * 1000)
        resp = self._login(make_transaction(revocation_date_ms=now_ms))

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(is_guest=True).exists())

    def test_purchase_of_registered_account_returns_409_with_masked_email(self):
        owner = User.objects.create_user(email='alice@gmail.com', password='pw12345678', is_email_verified=True)
        Subscription.objects.create(user=owner, payment_provider='apple',
                                    apple_original_transaction_id='1000000000123', status='active')

        resp = self._login(make_transaction())

        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data['error'], 'This purchase belongs to a***@gmail.com. Please sign in.')
        self.assertNotIn('refresh_token', resp.cookies)
        self.assertFalse(User.objects.filter(is_guest=True).exists())

    def test_concurrent_first_login_reuses_the_guest_created_first(self):
        existing = AppleIAPService._create_guest_subscription(make_transaction())
        lookup = AppleIAPService._locked_subscription
        calls = []

        def miss_first_lookup(*args, **kwargs):
            calls.append(args)
            return None if len(calls) == 1 else lookup(*args, **kwargs)

        with patch.object(AppleIAPService, '_locked_subscription', side_effect=miss_first_lookup):
            resp = self._login(make_transaction())

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['data']['user']['id'], existing.user_id)
        self.assertEqual(User.objects.filter(is_guest=True).count(), 1)

    def test_stale_authorization_header_does_not_block_login(self):
        resp = self._login(make_transaction(), HTTP_AUTHORIZATION='Bearer expired-token')

        self.assertEqual(resp.status_code, 200)

    def test_missing_signed_transaction_returns_400(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, 400)

    @override_settings(APPLE_IAP_BUNDLE_ID='')
    def test_unconfigured_bundle_id_refuses_guest_login(self):
        resp = self._login(make_transaction(bundle='com.any.app'))

        self.assertEqual(resp.status_code, 500)
        self.assertFalse(User.objects.filter(is_guest=True).exists())

    def test_refresh_cookie_of_merged_guest_is_rejected(self):
        refresh_cookie = self._login(make_transaction()).cookies['refresh_token'].value
        user = User.objects.create_user(email='real@example.com', password='pw12345678', is_email_verified=True)
        with patch.object(AppleIAPService, 'decode_signed_jws', return_value=make_transaction()):
            AppleIAPService.activate_subscription(user, 'signed-jws')

        self.client.cookies['refresh_token'] = refresh_cookie
        resp = self.client.post(reverse('token-refresh'))

        self.assertEqual(resp.status_code, 401)

    def test_guest_can_set_state_and_vehicle(self):
        guest = AppleIAPService._create_guest_subscription(make_transaction()).user
        state = State.objects.create(name='California')
        vehicle = Vehicle.objects.create(name='Car')
        self.client.force_authenticate(guest)

        resp = self.client.put(reverse('me'), {'state': state.id, 'vehicle': vehicle.id}, format='json')

        self.assertEqual(resp.status_code, 200)
        guest.profile.refresh_from_db()
        self.assertEqual(guest.profile.state, state)
        self.assertEqual(guest.profile.vehicle, vehicle)

    def test_guest_cannot_start_stripe_checkout(self):
        guest = AppleIAPService._create_guest_subscription(make_transaction()).user
        self.client.force_authenticate(guest)

        resp = self.client.post(reverse('subscription-checkout'), {
            'price_id': 'price_x', 'success_url': 'https://example.com/s', 'cancel_url': 'https://example.com/c',
        }, format='json')

        self.assertEqual(resp.status_code, 403)

