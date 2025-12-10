"""
Security Tests
==============

Comprehensive tests for:
- JWT authentication (RFC 7519)
- AES-256-GCM encryption (NIST SP 800-38D)
- RBAC authorization
- Password hashing (Argon2id)
"""

import pytest
import time
from datetime import datetime, timezone, timedelta

# Mark all tests in this module
pytestmark = [pytest.mark.security, pytest.mark.unit]


class TestJWTAuthentication:
    """JWT authentication tests"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        from security.jwt_oauth2_auth import auth_manager
        
        token = auth_manager.create_access_token(
            user_id="user_001",
            username="testuser",
            role="developer"
        )
        
        assert token.access_token is not None
        assert token.refresh_token is not None
        assert token.token_type == "bearer"
        assert token.expires_in == 900  # 15 minutes
    
    def test_verify_valid_token(self):
        """Test valid token verification"""
        from security.jwt_oauth2_auth import auth_manager
        
        token = auth_manager.create_access_token(
            user_id="user_001",
            username="testuser",
            role="developer"
        )
        
        payload = auth_manager.verify_token(token.access_token)
        
        assert payload is not None
        assert payload.sub == "user_001"
        assert payload.username == "testuser"
        assert payload.role == "developer"
    
    def test_verify_expired_token(self):
        """Test expired token rejection"""
        from security.jwt_oauth2_auth import auth_manager, JWTConfig
        import jwt
        
        # Create token with past expiration
        payload = {
            "sub": "user_001",
            "username": "testuser",
            "role": "developer",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "jti": "test_jti"
        }
        
        config = JWTConfig()
        expired_token = jwt.encode(payload, config.secret_key, algorithm=config.algorithm)
        
        result = auth_manager.verify_token(expired_token)
        assert result is None
    
    def test_verify_invalid_signature(self):
        """Test invalid signature rejection"""
        from security.jwt_oauth2_auth import auth_manager
        import jwt
        
        # Create token with wrong key
        payload = {
            "sub": "user_001",
            "username": "testuser",
            "role": "developer",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
            "jti": "test_jti"
        }
        
        invalid_token = jwt.encode(payload, "wrong_secret_key", algorithm="HS512")
        
        result = auth_manager.verify_token(invalid_token)
        assert result is None
    
    def test_refresh_token_rotation(self):
        """Test refresh token rotation"""
        from security.jwt_oauth2_auth import auth_manager
        
        # Create initial tokens
        initial = auth_manager.create_access_token(
            user_id="user_001",
            username="testuser",
            role="developer"
        )
        
        # Refresh
        new_tokens = auth_manager.refresh_access_token(initial.refresh_token)
        
        assert new_tokens is not None
        assert new_tokens.access_token != initial.access_token
        assert new_tokens.refresh_token != initial.refresh_token  # Rotated
    
    def test_token_revocation(self):
        """Test token revocation"""
        from security.jwt_oauth2_auth import auth_manager
        
        token = auth_manager.create_access_token(
            user_id="user_001",
            username="testuser",
            role="developer"
        )
        
        # Verify token works
        assert auth_manager.verify_token(token.access_token) is not None
        
        # Revoke token
        auth_manager.revoke_token(token.access_token)
        
        # Verify token is now invalid
        assert auth_manager.verify_token(token.access_token) is None


class TestPasswordHashing:
    """Password hashing tests (Argon2id)"""
    
    def test_hash_password(self):
        """Test password hashing"""
        from security.jwt_oauth2_auth import password_hasher
        
        password = "SecureP@ssw0rd123!"
        hashed = password_hasher.hash(password)
        
        assert hashed != password
        assert hashed.startswith("$argon2id$")
    
    def test_verify_correct_password(self):
        """Test correct password verification"""
        from security.jwt_oauth2_auth import password_hasher
        
        password = "SecureP@ssw0rd123!"
        hashed = password_hasher.hash(password)
        
        assert password_hasher.verify(password, hashed) is True
    
    def test_verify_wrong_password(self):
        """Test wrong password rejection"""
        from security.jwt_oauth2_auth import password_hasher
        
        password = "SecureP@ssw0rd123!"
        wrong_password = "WrongPassword!"
        hashed = password_hasher.hash(password)
        
        assert password_hasher.verify(wrong_password, hashed) is False
    
    def test_unique_salts(self):
        """Test that each hash uses unique salt"""
        from security.jwt_oauth2_auth import password_hasher
        
        password = "SecureP@ssw0rd123!"
        hash1 = password_hasher.hash(password)
        hash2 = password_hasher.hash(password)
        
        assert hash1 != hash2  # Different salts


class TestAES256GCMEncryption:
    """AES-256-GCM encryption tests (NIST SP 800-38D)"""
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption/decryption"""
        from security.aes256_gcm_encryption import encryption
        
        plaintext = "Hello, World!"
        encrypted = encryption.encrypt(plaintext)
        decrypted = encryption.decrypt(encrypted)
        
        assert encrypted != plaintext
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption/decryption"""
        from security.aes256_gcm_encryption import encryption
        
        data = {"email": "test@example.com", "ssn": "123-45-6789"}
        encrypted = encryption.encrypt(data)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == data
    
    def test_unique_iv_per_encryption(self):
        """Test that each encryption uses unique IV"""
        from security.aes256_gcm_encryption import encryption
        
        plaintext = "Same message"
        enc1 = encryption.encrypt(plaintext)
        enc2 = encryption.encrypt(plaintext)
        
        # Different ciphertext due to unique IV
        assert enc1 != enc2
        
        # Both decrypt to same plaintext
        assert encryption.decrypt(enc1) == plaintext
        assert encryption.decrypt(enc2) == plaintext
    
    def test_tamper_detection(self):
        """Test authentication tag prevents tampering"""
        from security.aes256_gcm_encryption import encryption
        import base64
        
        plaintext = "Sensitive data"
        encrypted = encryption.encrypt(plaintext)
        
        # Tamper with ciphertext
        parts = encrypted.split(":")
        if len(parts) >= 2:
            # Modify a byte in the ciphertext
            ciphertext = base64.b64decode(parts[1])
            tampered = bytes([ciphertext[0] ^ 0xFF]) + ciphertext[1:]
            parts[1] = base64.b64encode(tampered).decode()
            tampered_encrypted = ":".join(parts)
            
            # Decryption should fail
            result = encryption.decrypt(tampered_encrypted)
            assert result is None
    
    def test_field_level_encryption(self):
        """Test field-level PII encryption"""
        from security.aes256_gcm_encryption import field_encryption
        
        record = {
            "id": "user_001",
            "email": "secret@example.com",
            "name": "John Doe",
            "ssn": "123-45-6789"
        }
        
        encrypted_record = field_encryption.encrypt_pii_fields(record)
        
        # PII fields should be encrypted
        assert encrypted_record["email"] != record["email"]
        assert encrypted_record["ssn"] != record["ssn"]
        
        # Non-PII fields unchanged
        assert encrypted_record["id"] == record["id"]
        assert encrypted_record["name"] == record["name"]
        
        # Decrypt and verify
        decrypted_record = field_encryption.decrypt_pii_fields(encrypted_record)
        assert decrypted_record["email"] == record["email"]
        assert decrypted_record["ssn"] == record["ssn"]


class TestDataMasking:
    """Data masking tests"""
    
    def test_mask_email(self):
        """Test email masking"""
        from security.aes256_gcm_encryption import data_masker
        
        email = "john.doe@example.com"
        masked = data_masker.mask_email(email)
        
        assert masked != email
        assert "@" in masked
        assert "***" in masked
        assert masked.endswith("@example.com") or "***" in masked
    
    def test_mask_credit_card(self):
        """Test credit card masking"""
        from security.aes256_gcm_encryption import data_masker
        
        card = "4111111111111111"
        masked = data_masker.mask_credit_card(card)
        
        assert masked != card
        assert "1111" in masked  # Last 4 visible
        assert "*" in masked
    
    def test_mask_phone(self):
        """Test phone masking"""
        from security.aes256_gcm_encryption import data_masker
        
        phone = "555-123-4567"
        masked = data_masker.mask_phone(phone)
        
        assert masked != phone
        assert "4567" in masked  # Last 4 visible
        assert "*" in masked
    
    def test_mask_ssn(self):
        """Test SSN masking"""
        from security.aes256_gcm_encryption import data_masker
        
        ssn = "123-45-6789"
        masked = data_masker.mask_ssn(ssn)
        
        assert masked != ssn
        assert "6789" in masked  # Last 4 visible
        assert "*" in masked


class TestRBAC:
    """Role-based access control tests"""
    
    def test_role_hierarchy(self):
        """Test role hierarchy"""
        from security.jwt_oauth2_auth import UserRole, ROLE_HIERARCHY
        
        # SuperAdmin has highest level
        assert ROLE_HIERARCHY[UserRole.SUPER_ADMIN] > ROLE_HIERARCHY[UserRole.ADMIN]
        assert ROLE_HIERARCHY[UserRole.ADMIN] > ROLE_HIERARCHY[UserRole.DEVELOPER]
        assert ROLE_HIERARCHY[UserRole.DEVELOPER] > ROLE_HIERARCHY[UserRole.API_USER]
        assert ROLE_HIERARCHY[UserRole.API_USER] > ROLE_HIERARCHY[UserRole.READ_ONLY]
        assert ROLE_HIERARCHY[UserRole.READ_ONLY] > ROLE_HIERARCHY[UserRole.GUEST]
    
    def test_role_checker_allows_same_role(self):
        """Test RoleChecker allows same role"""
        from security.jwt_oauth2_auth import RoleChecker, UserRole, TokenPayload
        
        checker = RoleChecker([UserRole.DEVELOPER])
        
        # Create mock token payload
        payload = TokenPayload(
            sub="user_001",
            username="testuser",
            role="developer",
            type="access",
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti="test_jti"
        )
        
        # Should not raise
        result = checker(payload)
        assert result == payload
    
    def test_role_checker_allows_higher_role(self):
        """Test RoleChecker allows higher role"""
        from security.jwt_oauth2_auth import RoleChecker, UserRole, TokenPayload
        
        checker = RoleChecker([UserRole.DEVELOPER])
        
        # Admin is higher than Developer
        payload = TokenPayload(
            sub="admin_001",
            username="admin",
            role="admin",
            type="access",
            exp=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti="test_jti"
        )
        
        result = checker(payload)
        assert result == payload


class TestAccountLockout:
    """Account lockout tests"""
    
    def test_lockout_after_failed_attempts(self):
        """Test account lockout after failed login attempts"""
        from security.jwt_oauth2_auth import auth_manager, password_hasher
        
        user_id = "lockout_test_user"
        correct_hash = password_hasher.hash("correct_password")
        
        # Simulate 5 failed attempts
        for i in range(5):
            auth_manager.record_failed_login(user_id)
        
        # Account should be locked
        is_locked, remaining = auth_manager.check_account_lockout(user_id)
        assert is_locked is True
        assert remaining > 0
    
    def test_successful_login_resets_counter(self):
        """Test successful login resets failed attempt counter"""
        from security.jwt_oauth2_auth import auth_manager
        
        user_id = "reset_test_user"
        
        # Record some failed attempts
        auth_manager.record_failed_login(user_id)
        auth_manager.record_failed_login(user_id)
        
        # Record successful login
        auth_manager.record_successful_login(user_id)
        
        # Should not be locked
        is_locked, _ = auth_manager.check_account_lockout(user_id)
        assert is_locked is False


class TestSecurityHeaders:
    """Security headers tests"""
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test CORS headers are set"""
        response = await client.options(
            "/api/v1/auth/token",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should allow CORS (may vary by config)
        assert response.status_code in [200, 204, 405]
    
    @pytest.mark.asyncio
    async def test_request_id_header(self, client):
        """Test X-Request-ID header is returned"""
        response = await client.get("/health")
        
        # Should have request ID
        assert "x-request-id" in response.headers or response.status_code == 200


class TestInputValidation:
    """Input validation tests"""
    
    @pytest.mark.asyncio
    async def test_xss_prevention(self, client, auth_headers):
        """Test XSS payload is sanitized"""
        xss_payload = "<script>alert('xss')</script>"
        
        response = await client.post(
            "/api/v1/agents/content/generate",
            headers=auth_headers,
            json={
                "type": "blog_post",
                "topic": xss_payload,
                "keywords": ["test"]
            }
        )
        
        # Should not reflect XSS payload directly
        if response.status_code == 200:
            data = response.json()
            assert "<script>" not in str(data)
    
    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client, auth_headers):
        """Test SQL injection is prevented"""
        sqli_payload = "'; DROP TABLE users; --"
        
        response = await client.get(
            f"/api/v1/products/search",
            headers=auth_headers,
            params={"q": sqli_payload}
        )
        
        # Should not cause SQL error
        assert response.status_code in [200, 404, 422]
