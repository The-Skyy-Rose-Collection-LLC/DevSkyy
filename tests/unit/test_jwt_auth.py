"""
DevSkyy Enterprise - JWT Authentication Unit Tests
Comprehensive tests for JWT token creation, validation, and security
"""

import unittest
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from security.jwt_auth import (
    create_access_token,
    create_refresh_token,
    get_token_payload,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    verify_token,
)


class TestJWTTokenCreation(unittest.TestCase):
    """Test JWT token creation functions"""

    def test_create_access_token_basic(self, test_user_data):
        """Test basic access token creation"""
        token = create_access_token(data=test_user_data)

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 50  # JWT tokens are reasonably long)

        # Verify token can be decoded
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload["user_id"], test_user_data["user_id"])
        self.assertEqual(payload["email"], test_user_data["email"])
        self.assertEqual(payload["token_type"], "access")

    def test_create_access_token_with_custom_expiry(self, test_user_data):
        """Test access token with custom expiration time"""
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data=test_user_data, expires_delta=expires_delta)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        exp_timestamp = payload["exp"]
        iat_timestamp = payload["iat"]

        # Verify expiration is approximately 30 minutes from issued time
        self.assertEqual((exp_timestamp - iat_timestamp), 30 * 60  # 30 minutes in seconds)

    def test_create_refresh_token_basic(self, test_user_data):
        """Test basic refresh token creation"""
        token = create_refresh_token(data=test_user_data)

        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        self.assertEqual(payload["user_id"], test_user_data["user_id"])
        self.assertEqual(payload["token_type"], "refresh")

    def test_create_token_contains_all_user_data(self, test_user_data):
        """Test that token contains all provided user data"""
        token = create_access_token(data=test_user_data)
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        for key, value in test_user_data.items():
            self.assertEqual(payload[key], value)

    def test_create_token_with_utc_timestamps(self, test_user_data):
        """Test that tokens use UTC timestamps (critical bug fix)"""
        before_time = datetime.now(timezone.utc)
        token = create_access_token(data=test_user_data)
        after_time = datetime.now(timezone.utc)

        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        # Issued time should be between before and after
        self.assertLess(before_time, = iat_time <= after_time)


class TestJWTTokenVerification(unittest.TestCase):
    """Test JWT token verification functions"""

    def test_verify_valid_access_token(self, test_access_token):
        """Test verification of valid access token"""
        result = verify_token(test_access_token, expected_type="access")

        self.assertIsNotNone(result)
        self.assertEqual(result["user_id"], "test_user_001")
        self.assertEqual(result["token_type"], "access")

    def test_verify_valid_refresh_token(self, test_refresh_token):
        """Test verification of valid refresh token"""
        result = verify_token(test_refresh_token, expected_type="refresh")

        self.assertIsNotNone(result)
        self.assertEqual(result["user_id"], "test_user_001")
        self.assertEqual(result["token_type"], "refresh")

    def test_verify_token_wrong_type(self, test_access_token):
        """Test that access token fails when expecting refresh token"""
        result = verify_token(test_access_token, expected_type="refresh")

        self.assertIs(result, None  # Should return None for wrong type)

    def test_verify_expired_token(self, test_user_data):
        """Test that expired tokens are rejected"""
        # Create token that expired 1 minute ago
        expires_delta = timedelta(minutes=-1)
        expired_token = create_access_token(
            data=test_user_data, expires_delta=expires_delta
        )

        result = verify_token(expired_token)
        self.assertIs(result, None  # Expired token should be rejected)

    def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected"""
        invalid_token = "this.is.not.a.valid.jwt.token"

        result = verify_token(invalid_token)
        self.assertIsNone(result)

    def test_verify_tampered_token(self, test_access_token):
        """Test that tampered tokens are rejected"""
        # Tamper with the token by changing a character
        tampered_token = test_access_token[:-5] + "AAAAA"

        result = verify_token(tampered_token)
        self.assertIsNone(result)

    def test_verify_token_with_wrong_secret(self, test_user_data):
        """Test that token signed with different secret is rejected"""
        # Create token with different secret
        wrong_secret_token = jwt.encode(
            test_user_data, "wrong_secret_key", algorithm=JWT_ALGORITHM
        )

        result = verify_token(wrong_secret_token)
        self.assertIsNone(result)


class TestJWTTokenPayload(unittest.TestCase):
    """Test JWT token payload extraction"""

    def test_get_token_payload_success(self, test_access_token):
        """Test successful payload extraction"""
        payload = get_token_payload(test_access_token)

        self.assertIsNotNone(payload)
        self.assertIn("user_id", payload)
        self.assertIn("email", payload)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_get_token_payload_invalid_token(self):
        """Test payload extraction from invalid token"""
        payload = get_token_payload("invalid.token.here")

        self.assertIsNone(payload)

    def test_get_token_payload_expired_token(self, test_user_data):
        """Test payload extraction from expired token (should still work)"""
        # Create expired token
        expired_token = create_access_token(
            data=test_user_data, expires_delta=timedelta(minutes=-1)
        )

        # Payload extraction should work even for expired tokens
        payload = get_token_payload(expired_token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["user_id"], test_user_data["user_id"])


class TestJWTSecurity(unittest.TestCase):
    """Test JWT security features"""

    def test_tokens_are_unique(self, test_user_data):
        """Test that each token generated is unique"""
        token1 = create_access_token(data=test_user_data)
        token2 = create_access_token(data=test_user_data)

        # Tokens should be different due to different iat timestamps
        self.assertNotEqual(token1, token2)

    def test_token_contains_no_sensitive_data_in_clear(self, test_access_token):
        """Test that token doesn't contain clear passwords or secrets"""
        # JWT tokens are base64 encoded, not encrypted
        # Ensure we're not putting sensitive data in claims
        payload = get_token_payload(test_access_token)

        self.assertIn("password" not, payload)
        self.assertIn("secret" not, payload.get("user_id", "").lower())

    def test_token_expiration_is_future_date(self, test_access_token):
        """Test that token expiration is in the future"""
        payload = get_token_payload(test_access_token)
        exp_timestamp = payload["exp"]
        current_timestamp = datetime.now(timezone.utc).timestamp()

        self.assertGreater(exp_timestamp, current_timestamp)

    def test_access_token_shorter_expiry_than_refresh(self, test_user_data):
        """Test that access tokens expire sooner than refresh tokens"""
        access_token = create_access_token(data=test_user_data)
        refresh_token = create_refresh_token(data=test_user_data)

        access_payload = get_token_payload(access_token)
        refresh_payload = get_token_payload(refresh_token)

        # Refresh token should expire later than access token
        self.assertGreater(refresh_payload["exp"], access_payload["exp"])


class TestJWTEdgeCases(unittest.TestCase):
    """Test JWT edge cases and error handling"""

    def test_create_token_with_empty_data(self):
        """Test token creation with empty data"""
        token = create_access_token(data={})

        self.assertIsNotNone(token)
        payload = get_token_payload(token)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_create_token_with_special_characters(self):
        """Test token creation with special characters in data"""
        data = {
            "user_id": "user@#$%^&*()",
            "email": "test+special@example.com",
            "name": "Test O'Reilly",
        }

        token = create_access_token(data=data)
        payload = get_token_payload(token)

        self.assertEqual(payload["user_id"], data["user_id"])
        self.assertEqual(payload["email"], data["email"])

    def test_create_token_with_large_payload(self):
        """Test token creation with large data payload"""
        large_data = {
            "user_id": "test_001",
            "permissions": ["perm_" + str(i) for i in range(100)],
            "metadata": {"key_" + str(i): "value_" + str(i) for i in range(50)},
        }

        token = create_access_token(data=large_data)

        self.assertIsNotNone(token)
        self.assertGreater(len(token), 500  # Should be reasonably large)

    def test_verify_token_none_input(self):
        """Test verification with None input"""
        result = verify_token(None)
        self.assertIsNone(result)

    def test_verify_token_empty_string(self):
        """Test verification with empty string"""
        result = verify_token("")
        self.assertIsNone(result)


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.slow
class TestJWTPerformance(unittest.TestCase):
    """Test JWT token performance"""

    def test_token_creation_performance(self, test_user_data, performance_timer):
        """Test that token creation is fast"""
        for _ in range(100):
            create_access_token(data=test_user_data)

        elapsed = performance_timer()
        self.assertLess(elapsed, 1.0  # Should create 100 tokens in under 1 second)

    def test_token_verification_performance(self, test_access_token, performance_timer):
        """Test that token verification is fast"""
        for _ in range(100):
            verify_token(test_access_token)

        elapsed = performance_timer()
        self.assertLess(elapsed, 1.0  # Should verify 100 tokens in under 1 second)
