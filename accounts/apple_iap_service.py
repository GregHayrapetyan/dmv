"""
Apple In-App Purchase (StoreKit 2) service.

This is the Apple counterpart to `stripe_service.StripeService`. It handles the
iOS payment path required by App Store Guideline 3.1.1:

  * verifying the signed transaction (JWS) the iOS app produces after a purchase,
  * activating / updating the user's Subscription from it, and
  * processing App Store Server Notifications (V2) so renewals, cancellations,
    refunds and expirations stay in sync — the Apple twin of the Stripe webhook.

Verification is done locally by validating the JWS certificate chain (x5c) up to
Apple's Root CA - G3 and checking the ES256 signature with the leaf certificate.
No secret is required to verify — the signature proves Apple issued the payload.
"""
import base64
import datetime
import logging

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.conf import settings
from django.utils import timezone

from .models import Subscription

logger = logging.getLogger(__name__)

# SHA-256 fingerprint of "Apple Root CA - G3" (the root that anchors every
# StoreKit 2 / App Store Server signature). We pin it so a valid-looking chain
# signed by some *other* root is rejected.
APPLE_ROOT_CA_G3_SHA256 = (
    "63343abfb89a6a03ebb57e9b3f5fa7be7c4f5c756f3017b3a8c488c3653e9179"
)

# Plan tier -> access window in days (mirrors the Stripe duration_map).
TIER_DURATION_DAYS = {"starter": 7, "standard": 30, "premium": 90}

# Notification types that mean "the subscription is (still) paid and active".
_ACTIVE_NOTIFICATIONS = {"SUBSCRIBED", "DID_RENEW", "OFFER_REDEEMED"}
# Notification types that mean "access has ended".
_ENDED_NOTIFICATIONS = {"EXPIRED", "GRACE_PERIOD_EXPIRED"}


class AppleIAPError(Exception):
    """Raised when an Apple transaction/notification cannot be verified."""


class AppleIAPService:
    """Service class for Apple In-App Purchase operations."""

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def product_to_tier(product_id):
        """Map an App Store product identifier to one of our plan tiers."""
        return settings.APPLE_IAP_PRODUCTS.get(product_id)

    @staticmethod
    def _ms_to_datetime(milliseconds):
        """Convert an Apple epoch-milliseconds timestamp to an aware datetime."""
        if not milliseconds:
            return None
        return datetime.datetime.fromtimestamp(
            int(milliseconds) / 1000, tz=datetime.timezone.utc
        )

    # ------------------------------------------------------- JWS verification

    @staticmethod
    def _verify_cert_signed_by(cert, issuer):
        """Raise if `cert` was not signed by `issuer`'s public key."""
        issuer_key = issuer.public_key()
        if isinstance(issuer_key, ec.EllipticCurvePublicKey):
            issuer_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                ec.ECDSA(cert.signature_hash_algorithm),
            )
        else:  # RSA fallback (Apple's chain is EC today, but be defensive)
            issuer_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )

    @classmethod
    def _leaf_public_key_pem(cls, x5c):
        """
        Validate the x5c certificate chain (leaf -> intermediate -> Apple root)
        and return the leaf certificate's public key as PEM bytes.
        """
        if not x5c:
            raise AppleIAPError("Signed payload is missing its x5c certificate chain")

        try:
            certs = [
                x509.load_der_x509_certificate(base64.b64decode(entry))
                for entry in x5c
            ]
        except Exception as exc:  # noqa: BLE001
            raise AppleIAPError(f"Could not parse x5c certificates: {exc}") from exc

        now = datetime.datetime.now(datetime.timezone.utc)
        for cert in certs:
            not_before = cert.not_valid_before_utc
            not_after = cert.not_valid_after_utc
            if not (not_before <= now <= not_after):
                raise AppleIAPError("A certificate in the chain is expired or not yet valid")

        # Each cert must be signed by the next one up the chain.
        for i in range(len(certs) - 1):
            try:
                cls._verify_cert_signed_by(certs[i], certs[i + 1])
            except Exception as exc:  # noqa: BLE001
                raise AppleIAPError(f"Certificate chain verification failed: {exc}") from exc

        # The root (last cert) must be Apple Root CA - G3.
        root_fingerprint = certs[-1].fingerprint(hashes.SHA256()).hex()
        if root_fingerprint != APPLE_ROOT_CA_G3_SHA256:
            raise AppleIAPError("Certificate chain is not anchored to Apple Root CA - G3")

        return certs[0].public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
        )

    @classmethod
    def decode_signed_jws(cls, signed_jws):
        """
        Verify an Apple-signed JWS (a transaction, renewal info, or notification
        payload) and return its decoded claims as a dict.

        Raises AppleIAPError if the signature or certificate chain is invalid.
        """
        if not signed_jws or not isinstance(signed_jws, str):
            raise AppleIAPError("Missing signed payload")

        try:
            header = jwt.get_unverified_header(signed_jws)
        except jwt.InvalidTokenError as exc:
            raise AppleIAPError(f"Malformed signed payload: {exc}") from exc

        # DEBUG-only: a local StoreKit configuration file (Xcode simulator
        # testing) signs transactions with Xcode's own test certificate rather
        # than Apple Root CA - G3, so the chain check below can never pass. When
        # explicitly opted in for local dev, trust the decoded claims without
        # verifying the signature. Gated on DEBUG *and* the flag, so production
        # (DEBUG=False) always does full verification.
        if settings.DEBUG and getattr(settings, "APPLE_IAP_ALLOW_UNVERIFIED", False):
            logger.warning(
                "APPLE_IAP_ALLOW_UNVERIFIED: decoding Apple JWS without signature "
                "verification (local StoreKit testing only)."
            )
            try:
                return jwt.decode(
                    signed_jws,
                    options={
                        "verify_signature": False,
                        "verify_aud": False,
                        "verify_iss": False,
                        "verify_exp": False,
                        "verify_nbf": False,
                    },
                )
            except jwt.InvalidTokenError as exc:
                raise AppleIAPError(f"Malformed signed payload: {exc}") from exc

        public_key_pem = cls._leaf_public_key_pem(header.get("x5c"))

        try:
            return jwt.decode(
                signed_jws,
                public_key_pem,
                algorithms=["ES256"],
                # Apple payloads carry custom claims (not standard exp/aud/iss),
                # so only the cryptographic signature matters here.
                options={
                    "verify_aud": False,
                    "verify_iss": False,
                    "verify_exp": False,
                    "verify_nbf": False,
                },
            )
        except jwt.InvalidTokenError as exc:
            raise AppleIAPError(f"Signature verification failed: {exc}") from exc

    # -------------------------------------------------- transaction handling

    @classmethod
    def verify_transaction(cls, signed_transaction):
        """
        Verify a StoreKit 2 signed transaction (JWS) and return its claims after
        sanity-checking the bundle id and product.
        """
        transaction = cls.decode_signed_jws(signed_transaction)

        expected_bundle = settings.APPLE_IAP_BUNDLE_ID
        bundle_id = transaction.get("bundleId")
        if expected_bundle and bundle_id and bundle_id != expected_bundle:
            raise AppleIAPError(
                f"Transaction bundle id '{bundle_id}' does not match '{expected_bundle}'"
            )

        product_id = transaction.get("productId")
        if not cls.product_to_tier(product_id):
            raise AppleIAPError(f"Unknown product identifier: {product_id}")

        return transaction

    @classmethod
    def _apply_transaction(cls, subscription, transaction, status="active"):
        """Copy fields from a verified transaction onto a Subscription (unsaved)."""
        product_id = transaction.get("productId")
        tier = cls.product_to_tier(product_id)

        subscription.payment_provider = "apple"
        subscription.apple_original_transaction_id = transaction.get("originalTransactionId")
        subscription.apple_product_id = product_id
        subscription.is_one_time_purchase = False
        if tier:
            subscription.plan_tier = tier
            subscription.access_duration_days = TIER_DURATION_DAYS.get(tier)

        purchase_date = cls._ms_to_datetime(transaction.get("purchaseDate"))
        expires_date = cls._ms_to_datetime(transaction.get("expiresDate"))
        if purchase_date:
            subscription.current_period_start = purchase_date
        if expires_date:
            subscription.current_period_end = expires_date

        if status is not None:
            subscription.status = status
        return subscription

    @classmethod
    def activate_subscription(cls, user, signed_transaction):
        """
        Verify a purchase made in the iOS app and activate the user's Subscription.
        Called by the authenticated verify endpoint (user is known).

        Returns the updated Subscription instance.
        """
        transaction = cls.verify_transaction(signed_transaction)
        original_txn_id = transaction.get("originalTransactionId")

        # Guard: an Apple transaction may only belong to one account.
        clash = Subscription.objects.filter(
            apple_original_transaction_id=original_txn_id
        ).exclude(user=user).first()
        if clash:
            raise AppleIAPError(
                "This Apple purchase is already linked to a different account"
            )

        # Cross-platform guard: don't overwrite an active subscription bought on
        # another provider (e.g. Stripe on the web) with this Apple one — that
        # would double-bill and lose the original. The iOS client blocks this
        # before charging; this is the server-side backstop.
        existing = Subscription.objects.filter(user=user).first()
        if existing and existing.conflicts_with_purchase_on("apple"):
            raise AppleIAPError(
                "You already have an active subscription purchased on the web. "
                "Cancel it before subscribing through Apple."
            )

        subscription, _ = Subscription.objects.get_or_create(user=user)
        subscription.refresh_from_db()
        cls._apply_transaction(subscription, transaction, status="active")
        subscription.save()

        logger.info(
            "Apple IAP activated for user %s: product=%s tier=%s expires=%s",
            user.email, subscription.apple_product_id, subscription.plan_tier,
            subscription.current_period_end,
        )
        return subscription

    # ------------------------------------------------ server notifications

    @classmethod
    def handle_notification(cls, signed_payload):
        """
        Process an App Store Server Notification (V2). Apple POSTs a `signedPayload`
        JWS; we verify it, read the notification type + embedded transaction, and
        update the matching Subscription. Apple twin of StripeService webhook.
        """
        payload = cls.decode_signed_jws(signed_payload)

        notification_type = payload.get("notificationType")
        subtype = payload.get("subtype")
        data = payload.get("data", {}) or {}

        signed_transaction = data.get("signedTransactionInfo")
        if not signed_transaction:
            logger.info("Apple notification %s has no transaction info; ignoring",
                        notification_type)
            return

        transaction = cls.decode_signed_jws(signed_transaction)
        original_txn_id = transaction.get("originalTransactionId")

        try:
            subscription = Subscription.objects.get(
                apple_original_transaction_id=original_txn_id
            )
        except Subscription.DoesNotExist:
            # We only learn about a subscription we activated via the app first.
            logger.warning(
                "Apple notification %s for unknown transaction %s; ignoring",
                notification_type, original_txn_id,
            )
            return

        cls._apply_notification_status(subscription, transaction, notification_type, subtype)
        subscription.save()
        logger.info(
            "Apple notification %s/%s applied to user %s -> status=%s",
            notification_type, subtype, subscription.user.email, subscription.status,
        )

    @classmethod
    def _apply_notification_status(cls, subscription, transaction, notification_type, subtype):
        """Update a Subscription's status based on the notification type."""
        if notification_type in _ACTIVE_NOTIFICATIONS:
            cls._apply_transaction(subscription, transaction, status="active")
            subscription.cancel_at_period_end = False

        elif notification_type in _ENDED_NOTIFICATIONS:
            cls._apply_transaction(subscription, transaction, status="expired")

        elif notification_type == "DID_FAIL_TO_RENEW":
            # Billing retry / grace period — access may still be valid until expiry.
            cls._apply_transaction(subscription, transaction, status="past_due")

        elif notification_type == "DID_CHANGE_RENEWAL_STATUS":
            # AUTO_RENEW_DISABLED = user turned off renewal (cancel at period end).
            cls._apply_transaction(subscription, transaction, status=None)
            subscription.cancel_at_period_end = (subtype == "AUTO_RENEW_DISABLED")

        elif notification_type in ("REFUND", "REVOKE"):
            cls._apply_transaction(subscription, transaction, status="canceled")
            subscription.current_period_end = timezone.now()

        else:
            # Unhandled but harmless types (e.g. TEST, RENEWAL_EXTENDED) — refresh
            # the period window without changing status.
            logger.info("Unhandled Apple notification type: %s", notification_type)
            cls._apply_transaction(subscription, transaction, status=None)
