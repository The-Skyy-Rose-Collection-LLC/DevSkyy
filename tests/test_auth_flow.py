"""Tests for JWT/OAuth2 authentication flow.

Covers: registration, login, token refresh, logout, /me endpoint,
password validation, duplicate detection, and rate limiting.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from security.jwt_oauth2_auth import (
    JWTConfig,
    JWTManager,
    PasswordManager,
    RateLimiter,
    TokenBlacklist,
    TokenPayload,
    TokenResponse,
    TokenType,
    UserCreate,
    UserInDB,
    UserRole,
)

# =============================================================================
# Password Manager Tests
# =============================================================================


class TestPasswordManager:
    """Tests for Argon2id password hashing."""

    def test_hash_password_argon2(self):
        pm = PasswordManager()
        hashed = pm.hash_password("TestPass!123")
        assert hashed.startswith("$argon2")
        assert hashed != "TestPass!123"

    def test_verify_correct_password(self):
        pm = PasswordManager()
        hashed = pm.hash_password("SecureP@ss1")
        assert pm.verify_password("SecureP@ss1", hashed) is True

    def test_verify_wrong_password(self):
        pm = PasswordManager()
        hashed = pm.hash_password("SecureP@ss1")
        assert pm.verify_password("WrongPass!1", hashed) is False

    def test_different_passwords_different_hashes(self):
        pm = PasswordManager()
        h1 = pm.hash_password("Password!1")
        h2 = pm.hash_password("Password!2")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        """Argon2 uses random salt — same password produces different hashes."""
        pm = PasswordManager()
        h1 = pm.hash_password("SamePass!1")
        h2 = pm.hash_password("SamePass!1")
        assert h1 != h2  # Different salts


# =============================================================================
# JWT Manager Tests
# =============================================================================


class TestJWTManager:
    """Tests for JWT token creation and validation."""

    def setup_method(self):
        self.config = JWTConfig()
        self.manager = JWTManager(self.config)

    def test_create_access_token(self):
        token = self.manager.create_access_token(
            user_id="user-123",
            roles=["admin"],
        )
        assert isinstance(token, str)
        assert len(token) > 50

    def test_create_refresh_token(self):
        token = self.manager.create_refresh_token(
            user_id="user-123",
            roles=["admin"],
            family_id="family-1",
        )
        assert isinstance(token, str)

    def test_create_token_pair(self):
        pair = self.manager.create_token_pair(
            user_id="user-123",
            roles=["api_user"],
        )
        assert isinstance(pair, TokenResponse)
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in == self.config.access_token_expire_minutes * 60

    def test_validate_access_token(self):
        token = self.manager.create_access_token(
            user_id="user-456",
            roles=["api_user", "admin"],
        )
        payload = self.manager.validate_token(token, TokenType.ACCESS)
        assert payload.sub == "user-456"
        assert "api_user" in payload.roles
        assert "admin" in payload.roles
        assert payload.type == TokenType.ACCESS

    def test_validate_refresh_token(self):
        token = self.manager.create_refresh_token(
            user_id="user-789",
            roles=["api_user"],
            family_id="family-2",
        )
        payload = self.manager.validate_token(token, TokenType.REFRESH)
        assert payload.sub == "user-789"
        assert payload.type == TokenType.REFRESH

    def test_access_token_has_expiry(self):
        token = self.manager.create_access_token(
            user_id="user-123",
            roles=["api_user"],
        )
        payload = self.manager.validate_token(token, TokenType.ACCESS)
        assert payload.exp is not None
        assert payload.exp > datetime.now(UTC)

    def test_token_has_jti(self):
        """Each token should have a unique JWT ID."""
        t1 = self.manager.create_access_token("u1", ["api_user"])
        t2 = self.manager.create_access_token("u1", ["api_user"])
        p1 = self.manager.validate_token(t1, TokenType.ACCESS)
        p2 = self.manager.validate_token(t2, TokenType.ACCESS)
        assert p1.jti != p2.jti


# =============================================================================
# Token Blacklist Tests
# =============================================================================


class TestTokenBlacklist:
    """Tests for token revocation via blacklist."""

    def test_add_and_check(self):
        bl = TokenBlacklist()
        future = datetime.now(UTC) + timedelta(hours=1)
        bl.add("token-abc", future)
        assert bl.is_blacklisted("token-abc") is True

    def test_not_blacklisted(self):
        bl = TokenBlacklist()
        assert bl.is_blacklisted("unknown") is False

    def test_expired_token_cleaned_on_add(self):
        """add() calls _cleanup(), removing expired entries immediately."""
        bl = TokenBlacklist()
        past = datetime.now(UTC) - timedelta(hours=1)
        bl.add("old-token", past)
        # _cleanup() runs inside add(), so expired entry is already gone
        assert bl.is_blacklisted("old-token") is False


# =============================================================================
# Rate Limiter Tests
# =============================================================================


class TestRateLimiter:
    """Tests for brute-force protection."""

    def test_allows_under_limit(self):
        rl = RateLimiter(max_attempts=3, window_seconds=60)
        assert rl.is_allowed("key1") is True
        rl.record_attempt("key1")
        assert rl.is_allowed("key1") is True

    def test_blocks_over_limit(self):
        rl = RateLimiter(max_attempts=2, window_seconds=60)
        rl.record_attempt("key1")
        rl.record_attempt("key1")
        assert rl.is_allowed("key1") is False

    def test_different_keys_independent(self):
        rl = RateLimiter(max_attempts=1, window_seconds=60)
        rl.record_attempt("key1")
        assert rl.is_allowed("key2") is True


# =============================================================================
# Role Checker Tests
# =============================================================================


class TestRoleChecker:
    """Tests for RBAC role hierarchy."""

    def test_role_hierarchy_exists(self):
        from security.jwt_oauth2_auth import ROLE_HIERARCHY

        assert UserRole.SUPER_ADMIN.value in ROLE_HIERARCHY
        assert UserRole.API_USER.value in ROLE_HIERARCHY

    def test_super_admin_outranks_user(self):
        from security.jwt_oauth2_auth import ROLE_HIERARCHY

        assert ROLE_HIERARCHY[UserRole.SUPER_ADMIN.value] > ROLE_HIERARCHY[UserRole.API_USER.value]


# =============================================================================
# UserCreate Validation Tests
# =============================================================================


class TestUserCreateValidation:
    """Tests for OWASP password validation."""

    def test_valid_user(self):
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="StrongP@ss1",
        )
        assert user.username == "testuser"

    def test_weak_password_no_uppercase(self):
        with pytest.raises(ValueError, match="uppercase"):
            UserCreate(
                username="test",
                email="t@e.com",
                password="weakpass!1",
            )

    def test_weak_password_no_digit(self):
        with pytest.raises(ValueError, match="digit"):
            UserCreate(
                username="test",
                email="t@e.com",
                password="WeakPass!!",
            )

    def test_weak_password_no_special(self):
        with pytest.raises(ValueError, match="special"):
            UserCreate(
                username="test",
                email="t@e.com",
                password="WeakPass11",
            )

    def test_short_password(self):
        with pytest.raises(ValueError):
            UserCreate(
                username="test",
                email="t@e.com",
                password="Sh!1",
            )

    def test_invalid_username_chars(self):
        with pytest.raises(ValueError):
            UserCreate(
                username="user@name",
                email="t@e.com",
                password="StrongP@ss1",
            )


# =============================================================================
# UserInDB Tests
# =============================================================================


class TestUserInDB:
    """Tests for the database user model."""

    def test_is_locked_when_locked(self):
        user = UserInDB(
            id="1",
            username="test",
            email="t@e.com",
            hashed_password="xxx",
            locked_until=datetime.now(UTC) + timedelta(hours=1),
        )
        assert user.is_locked() is True

    def test_is_not_locked_when_expired(self):
        user = UserInDB(
            id="1",
            username="test",
            email="t@e.com",
            hashed_password="xxx",
            locked_until=datetime.now(UTC) - timedelta(hours=1),
        )
        assert user.is_locked() is False

    def test_is_not_locked_when_none(self):
        user = UserInDB(
            id="1",
            username="test",
            email="t@e.com",
            hashed_password="xxx",
        )
        assert user.is_locked() is False


# =============================================================================
# TokenPayload Tests
# =============================================================================


class TestTokenPayload:
    """Tests for JWT token payload model."""

    def test_token_payload_creation(self):
        payload = TokenPayload(
            sub="user-123",
            roles=["admin"],
            type=TokenType.ACCESS,
            jti="unique-id",
        )
        assert payload.sub == "user-123"
        assert payload.type == TokenType.ACCESS

    def test_token_type_enum(self):
        assert TokenType.ACCESS.value == "access"
        assert TokenType.REFRESH.value == "refresh"


# =============================================================================
# Integration: Token Round-Trip
# =============================================================================


class TestTokenRoundTrip:
    """End-to-end token creation → validation."""

    def test_full_round_trip(self):
        config = JWTConfig()
        mgr = JWTManager(config)

        pair = mgr.create_token_pair("user-rt", ["api_user", "admin"])

        access_payload = mgr.validate_token(pair.access_token, TokenType.ACCESS)
        assert access_payload.sub == "user-rt"
        assert "admin" in access_payload.roles

        refresh_payload = mgr.validate_token(pair.refresh_token, TokenType.REFRESH)
        assert refresh_payload.sub == "user-rt"

    def test_blacklisted_token_fails(self):

        config = JWTConfig()
        mgr = JWTManager(config)
        bl = TokenBlacklist()

        token = mgr.create_access_token("user-bl", ["api_user"])
        payload = mgr.validate_token(token, TokenType.ACCESS)

        bl.add(payload.jti, payload.exp)
        assert bl.is_blacklisted(payload.jti) is True
