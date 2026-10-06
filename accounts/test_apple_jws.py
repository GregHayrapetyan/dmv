"""
Tests for Apple JWS certificate-chain verification. Builds a fake root/intermediate/leaf
chain (the pinned Apple root fingerprint is patched to the fake root) and checks that only a
chain with Apple's App Store marker extensions is accepted.
"""
import base64
import datetime
from unittest.mock import patch

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from django.test import SimpleTestCase

from accounts.apple_iap_service import (
    APPLE_INTERMEDIATE_CERT_OID,
    APPLE_LEAF_CERT_OID,
    AppleIAPError,
    AppleIAPService,
)


def _make_cert(subject, key, issuer_name, issuer_key, *, ca, marker_oid=None, valid_days=(-1, 1)):
    now = datetime.datetime.now(datetime.timezone.utc)
    builder = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
        .issuer_name(issuer_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now + datetime.timedelta(days=valid_days[0]))
        .not_valid_after(now + datetime.timedelta(days=valid_days[1]))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
    )
    if marker_oid is not None:
        builder = builder.add_extension(
            x509.UnrecognizedExtension(marker_oid, b"\x05\x00"), critical=False
        )
    return builder.sign(issuer_key, hashes.SHA256())


def _b64(cert):
    return base64.b64encode(cert.public_bytes(serialization.Encoding.DER)).decode()


class AppleJWSChainTests(SimpleTestCase):
    def setUp(self):
        self.root_key = ec.generate_private_key(ec.SECP256R1())
        root_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Fake Apple Root")])
        self.root = _make_cert(
            "Fake Apple Root", self.root_key, root_name, self.root_key, ca=True, valid_days=(-1000, 1000)
        )
        self.intermediate_key = ec.generate_private_key(ec.SECP256R1())
        self.leaf_key = ec.generate_private_key(ec.SECP256R1())

        root_fingerprint = self.root.fingerprint(hashes.SHA256()).hex()
        patcher = patch("accounts.apple_iap_service.APPLE_ROOT_CA_G3_SHA256", root_fingerprint)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _chain(self, *, leaf_oid=APPLE_LEAF_CERT_OID, intermediate_oid=APPLE_INTERMEDIATE_CERT_OID,
               intermediate_ca=True, leaf_valid_days=(-1, 1)):
        intermediate = _make_cert(
            "Fake WWDR", self.intermediate_key, self.root.subject, self.root_key,
            ca=intermediate_ca, marker_oid=intermediate_oid, valid_days=(-1000, 1000),
        )
        leaf = _make_cert(
            "Fake App Store signer", self.leaf_key, intermediate.subject, self.intermediate_key,
            ca=False, marker_oid=leaf_oid, valid_days=leaf_valid_days,
        )
        return [_b64(leaf), _b64(intermediate), _b64(self.root)]

    def _jws(self, x5c, **claims):
        return jwt.encode(
            {"productId": "com.mytestdmv.standard", **claims}, self.leaf_key, algorithm="ES256",
            headers={"x5c": x5c},
        )

    @staticmethod
    def _days_ago_ms(days):
        moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        return int(moment.timestamp() * 1000)

    def test_accepts_app_store_chain(self):
        claims = AppleIAPService.decode_signed_jws(self._jws(self._chain()))
        self.assertEqual(claims["productId"], "com.mytestdmv.standard")

    def test_accepts_payload_signed_before_leaf_expired(self):
        # Apple rotated its signing cert since this (still active) transaction was signed, e.g. Restore.
        chain = self._chain(leaf_valid_days=(-400, -10))
        claims = AppleIAPService.decode_signed_jws(self._jws(chain, signedDate=self._days_ago_ms(20)))
        self.assertEqual(claims["productId"], "com.mytestdmv.standard")

    def test_rejects_payload_signed_after_leaf_expired(self):
        chain = self._chain(leaf_valid_days=(-400, -10))
        with self.assertRaisesMessage(AppleIAPError, "expired or not yet valid"):
            AppleIAPService.decode_signed_jws(self._jws(chain, signedDate=self._days_ago_ms(5)))

    def test_rejects_leaf_without_app_store_marker(self):
        # e.g. an Apple Pay / other Apple-issued cert whose private key a developer controls
        with self.assertRaisesMessage(AppleIAPError, "not an App Store signing certificate"):
            AppleIAPService.decode_signed_jws(self._jws(self._chain(leaf_oid=None)))

    def test_rejects_intermediate_without_wwdr_marker(self):
        with self.assertRaisesMessage(AppleIAPError, "not an Apple WWDR CA"):
            AppleIAPService.decode_signed_jws(self._jws(self._chain(intermediate_oid=None)))

    def test_rejects_intermediate_that_is_not_a_ca(self):
        with self.assertRaisesMessage(AppleIAPError, "not a certificate authority"):
            AppleIAPService.decode_signed_jws(self._jws(self._chain(intermediate_ca=False)))

    def test_rejects_wrong_chain_length(self):
        leaf, _intermediate, root = self._chain()
        with self.assertRaisesMessage(AppleIAPError, "leaf -> intermediate -> Apple root"):
            AppleIAPService.decode_signed_jws(self._jws([leaf, root]))

    def test_rejects_chain_not_anchored_to_apple_root(self):
        with patch("accounts.apple_iap_service.APPLE_ROOT_CA_G3_SHA256", "0" * 64):
            with self.assertRaisesMessage(AppleIAPError, "not anchored to Apple Root CA - G3"):
                AppleIAPService.decode_signed_jws(self._jws(self._chain()))

    def test_rejects_payload_not_signed_by_leaf(self):
        forged = jwt.encode(
            {"productId": "com.mytestdmv.premium"}, ec.generate_private_key(ec.SECP256R1()),
            algorithm="ES256", headers={"x5c": self._chain()},
        )
        with self.assertRaisesMessage(AppleIAPError, "Signature verification failed"):
            AppleIAPService.decode_signed_jws(forged)
