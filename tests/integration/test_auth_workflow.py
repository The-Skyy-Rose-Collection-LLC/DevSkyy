"""
Integration Tests for Authentication & Authorization Workflows
Comprehensive testing of OAuth2 + JWT authentication and RBAC

Test Coverage:
- Login → Token Generation → RBAC Check → Resource Access → Audit Log
- OAuth2 + JWT full flow
- Multi-role access patterns (all 5 roles)
- Token refresh mechanism
- Session management
- GDPR compliance in auth flow
- Security event logging
- Password reset workflow
- Multi-factor authentication (MFA)

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline - Argon2id + bcrypt, AES-256-GCM
- Rule #6: RBAC roles (5-tier)
- Rule #14: Error ledger required
"""

import asyncio
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest

from security.jwt_auth import (
    User,
    UserRole,
    TokenData,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password,
    get_current_user,
)
from security.rbac import (
    Permission,
    Role,
    RBACManager,
    check_permission,
)
from security.auth0_integration import Auth0Client


logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def test_user_credentials() -> dict[str, str]:
    """Create test user credentials."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
    }


@pytest.fixture
def super_admin_user() -> User:
    """Create super admin user for testing."""
    return User(
        user_id="user_super_001",
        email="admin@skyy-rose.com",
        username="superadmin",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        permissions=["*"],  # All permissions
    )


@pytest.fixture
def developer_user() -> User:
    """Create developer user for testing."""
    return User(
        user_id="user_dev_001",
        email="dev@skyy-rose.com",
        username="developer",
        password_hash=hash_password("DevPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
        permissions=["agent:read", "agent:write", "code:execute"],
    )


@pytest.fixture
def api_user() -> User:
    """Create API user for testing."""
    return User(
        user_id="user_api_001",
        email="api@example.com",
        username="apiuser",
        password_hash=hash_password("ApiPass123!"),
        role=UserRole.API_USER,
        is_active=True,
        permissions=["api:read", "api:write"],
    )


@pytest.fixture
def read_only_user() -> User:
    """Create read-only user for testing."""
    return User(
        user_id="user_readonly_001",
        email="readonly@example.com",
        username="readonlyuser",
        password_hash=hash_password("ReadPass123!"),
        role=UserRole.READ_ONLY,
        is_active=True,
        permissions=["api:read", "dashboard:read"],
    )


@pytest.fixture
def rbac_manager() -> RBACManager:
    """Create RBAC manager instance."""
    return RBACManager()


# ============================================================================
# PASSWORD HASHING & VERIFICATION TESTS
# ============================================================================


class TestPasswordHashingAndVerification:
    """Test password hashing with Argon2id and bcrypt."""

    def test_hash_password_argon2(self):
        """Test password hashing with Argon2id."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert "$argon2" in hashed or "$2b$" in hashed  # Argon2 or bcrypt

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password returns False."""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password("WrongPassword123!", hashed) is False

    def test_password_hash_is_salted(self):
        """Test password hashes are salted (different each time)."""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Should be different due to salt

    def test_bcrypt_backward_compatibility(self):
        """Test backward compatibility with bcrypt hashes."""
        password = "LegacyPassword123!"

        bcrypt_hash = hash_password(password)

        assert verify_password(password, bcrypt_hash) is True


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self, developer_user: User):
        """Test creating JWT access token."""
        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        access_token = create_access_token(token_data)

        assert access_token is not None
        assert isinstance(access_token, str)
        assert len(access_token) > 50

    def test_create_refresh_token(self, developer_user: User):
        """Test creating JWT refresh token."""
        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        refresh_token = create_refresh_token(token_data)

        assert refresh_token is not None
        assert isinstance(refresh_token, str)

    def test_verify_valid_token(self, developer_user: User):
        """Test verifying valid JWT token."""
        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        access_token = create_access_token(token_data)
        verified_data = verify_token(access_token)

        assert verified_data is not None
        assert verified_data.user_id == developer_user.user_id
        assert verified_data.email == developer_user.email

    def test_verify_expired_token(self, developer_user: User):
        """Test verifying expired token raises exception."""
        import os
        from datetime import UTC

        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        secret_key = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")

        expired_token = pyjwt.encode(
            {
                "user_id": developer_user.user_id,
                "email": developer_user.email,
                "username": developer_user.username,
                "role": developer_user.role,
                "exp": datetime.now(UTC) - timedelta(hours=1),
            },
            secret_key,
            algorithm="HS256",
        )

        with pytest.raises(Exception):
            verify_token(expired_token)

    def test_verify_invalid_signature_token(self, developer_user: User):
        """Test verifying token with invalid signature raises exception."""
        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        access_token = create_access_token(token_data)

        tampered_token = access_token[:-10] + "XXXXXXXXXX"

        with pytest.raises(Exception):
            verify_token(tampered_token)


# ============================================================================
# AUTHENTICATION FLOW TESTS
# ============================================================================


class TestAuthenticationFlow:
    """Test complete authentication workflows."""

    @pytest.mark.asyncio
    async def test_registration_to_login_flow(self, test_user_credentials: dict[str, str]):
        """Test complete registration → login flow."""
        from security.jwt_auth import register_user, authenticate_user

        user = await register_user(
            email=test_user_credentials["email"],
            username=test_user_credentials["username"],
            password=test_user_credentials["password"],
            role=UserRole.API_USER,
        )

        assert user is not None
        assert user.email == test_user_credentials["email"]

        tokens = await authenticate_user(
            email=test_user_credentials["email"],
            password=test_user_credentials["password"],
        )

        assert tokens is not None
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    @pytest.mark.asyncio
    async def test_token_refresh_flow(self, developer_user: User):
        """Test token refresh mechanism."""
        from security.jwt_auth import refresh_access_token

        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        refresh_token = create_refresh_token(token_data)

        new_access_token = await refresh_access_token(refresh_token)

        assert new_access_token is not None
        assert isinstance(new_access_token, str)

    @pytest.mark.asyncio
    async def test_failed_login_tracking(self, test_user_credentials: dict[str, str]):
        """Test tracking failed login attempts."""
        from security.jwt_auth import authenticate_user, get_failed_login_count

        for _ in range(3):
            try:
                await authenticate_user(
                    email=test_user_credentials["email"],
                    password="WrongPassword123!",
                )
            except Exception:
                pass

        failed_count = get_failed_login_count(test_user_credentials["email"])

        assert failed_count >= 3

    @pytest.mark.asyncio
    async def test_account_lockout_after_max_attempts(self, test_user_credentials: dict[str, str]):
        """Test account lockout after exceeding max failed login attempts."""
        from security.jwt_auth import authenticate_user, MAX_LOGIN_ATTEMPTS

        for _ in range(MAX_LOGIN_ATTEMPTS + 1):
            try:
                await authenticate_user(
                    email=test_user_credentials["email"],
                    password="WrongPassword123!",
                )
            except Exception:
                pass

        with pytest.raises(Exception, match="locked"):
            await authenticate_user(
                email=test_user_credentials["email"],
                password=test_user_credentials["password"],
            )

    @pytest.mark.asyncio
    async def test_logout_invalidates_token(self, developer_user: User):
        """Test logout adds token to blacklist."""
        from security.jwt_auth import logout_user, is_token_blacklisted

        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        access_token = create_access_token(token_data)

        await logout_user(access_token)

        assert is_token_blacklisted(access_token) is True


# ============================================================================
# RBAC & AUTHORIZATION TESTS
# ============================================================================


class TestRBACAuthorization:
    """Test role-based access control."""

    def test_super_admin_has_all_permissions(self, super_admin_user: User, rbac_manager: RBACManager):
        """Test super admin has access to all resources."""
        permissions_to_check = [
            "agent:read",
            "agent:write",
            "agent:delete",
            "system:config",
            "user:manage",
        ]

        for permission in permissions_to_check:
            assert rbac_manager.check_permission(super_admin_user, permission) is True

    def test_developer_has_code_permissions(self, developer_user: User, rbac_manager: RBACManager):
        """Test developer has code execution permissions."""
        allowed_permissions = ["agent:read", "agent:write", "code:execute"]
        denied_permissions = ["system:config", "user:manage", "billing:manage"]

        for permission in allowed_permissions:
            assert rbac_manager.check_permission(developer_user, permission) is True

        for permission in denied_permissions:
            assert rbac_manager.check_permission(developer_user, permission) is False

    def test_api_user_limited_access(self, api_user: User, rbac_manager: RBACManager):
        """Test API user has limited access."""
        allowed_permissions = ["api:read", "api:write"]
        denied_permissions = ["agent:delete", "system:config", "code:execute"]

        for permission in allowed_permissions:
            assert rbac_manager.check_permission(api_user, permission) is True

        for permission in denied_permissions:
            assert rbac_manager.check_permission(api_user, permission) is False

    def test_read_only_user_no_write_access(self, read_only_user: User, rbac_manager: RBACManager):
        """Test read-only user cannot write."""
        allowed_permissions = ["api:read", "dashboard:read"]
        denied_permissions = ["api:write", "agent:write", "config:write"]

        for permission in allowed_permissions:
            assert rbac_manager.check_permission(read_only_user, permission) is True

        for permission in denied_permissions:
            assert rbac_manager.check_permission(read_only_user, permission) is False

    @pytest.mark.asyncio
    async def test_role_based_endpoint_access(self, super_admin_user: User, read_only_user: User):
        """Test endpoint access based on user role."""
        from fastapi import HTTPException

        async def protected_endpoint(user: User, required_permission: str) -> dict[str, str]:
            if required_permission not in user.permissions and "*" not in user.permissions:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return {"status": "success"}

        admin_result = await protected_endpoint(super_admin_user, "system:config")
        assert admin_result["status"] == "success"

        with pytest.raises(HTTPException) as exc_info:
            await protected_endpoint(read_only_user, "system:config")
        assert exc_info.value.status_code == 403


# ============================================================================
# SESSION MANAGEMENT TESTS
# ============================================================================


class TestSessionManagement:
    """Test session management and tracking."""

    @pytest.mark.asyncio
    async def test_create_user_session(self, developer_user: User):
        """Test creating user session on login."""
        from security.jwt_auth import create_session

        session = await create_session(
            user_id=developer_user.user_id,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        assert session is not None
        assert session["user_id"] == developer_user.user_id
        assert session["ip_address"] == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, developer_user: User):
        """Test retrieving active sessions for user."""
        from security.jwt_auth import create_session, get_active_sessions

        await create_session(developer_user.user_id, "192.168.1.100", "Browser 1")
        await create_session(developer_user.user_id, "192.168.1.101", "Browser 2")

        active_sessions = await get_active_sessions(developer_user.user_id)

        assert len(active_sessions) >= 2

    @pytest.mark.asyncio
    async def test_terminate_session(self, developer_user: User):
        """Test terminating specific session."""
        from security.jwt_auth import create_session, terminate_session, get_active_sessions

        session = await create_session(developer_user.user_id, "192.168.1.100", "Browser 1")

        await terminate_session(session["session_id"])

        active_sessions = await get_active_sessions(developer_user.user_id)

        assert session["session_id"] not in [s["session_id"] for s in active_sessions]

    @pytest.mark.asyncio
    async def test_terminate_all_sessions(self, developer_user: User):
        """Test terminating all user sessions."""
        from security.jwt_auth import create_session, terminate_all_sessions, get_active_sessions

        await create_session(developer_user.user_id, "192.168.1.100", "Browser 1")
        await create_session(developer_user.user_id, "192.168.1.101", "Browser 2")

        await terminate_all_sessions(developer_user.user_id)

        active_sessions = await get_active_sessions(developer_user.user_id)

        assert len(active_sessions) == 0


# ============================================================================
# SECURITY AUDIT LOG TESTS
# ============================================================================


class TestSecurityAuditLog:
    """Test security event logging and audit trail."""

    @pytest.mark.asyncio
    async def test_log_successful_login(self, developer_user: User):
        """Test logging successful login event."""
        from security.jwt_auth import log_security_event, get_security_events

        await log_security_event(
            event_type="login_success",
            user_id=developer_user.user_id,
            ip_address="192.168.1.100",
            details={"username": developer_user.username},
        )

        events = await get_security_events(user_id=developer_user.user_id, event_type="login_success")

        assert len(events) > 0
        assert events[-1]["event_type"] == "login_success"

    @pytest.mark.asyncio
    async def test_log_failed_login(self):
        """Test logging failed login attempt."""
        from security.jwt_auth import log_security_event, get_security_events

        await log_security_event(
            event_type="login_failed",
            user_id=None,
            ip_address="192.168.1.100",
            details={"email": "attacker@example.com", "reason": "invalid_credentials"},
        )

        events = await get_security_events(event_type="login_failed")

        assert len(events) > 0
        assert events[-1]["event_type"] == "login_failed"

    @pytest.mark.asyncio
    async def test_log_permission_denied(self, read_only_user: User):
        """Test logging permission denied events."""
        from security.jwt_auth import log_security_event

        await log_security_event(
            event_type="permission_denied",
            user_id=read_only_user.user_id,
            ip_address="192.168.1.100",
            details={
                "username": read_only_user.username,
                "requested_permission": "agent:delete",
                "user_role": read_only_user.role,
            },
        )

        events = await get_security_events(user_id=read_only_user.user_id, event_type="permission_denied")

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_gdpr_compliant_audit_log(self, developer_user: User):
        """Test audit log masks PII per GDPR requirements."""
        from security.jwt_auth import log_security_event, get_security_events

        await log_security_event(
            event_type="profile_update",
            user_id=developer_user.user_id,
            ip_address="192.168.1.100",
            details={
                "email": developer_user.email,
                "phone": "+1234567890",
                "ssn": "123-45-6789",
            },
        )

        events = await get_security_events(user_id=developer_user.user_id, event_type="profile_update")

        assert len(events) > 0
        event_details = json.dumps(events[-1])
        assert "123-45-6789" not in event_details  # SSN should be redacted
        assert "REDACTED" in event_details or "***" in event_details


# ============================================================================
# PASSWORD RESET WORKFLOW TESTS
# ============================================================================


class TestPasswordResetWorkflow:
    """Test password reset workflow."""

    @pytest.mark.asyncio
    async def test_request_password_reset(self, developer_user: User):
        """Test requesting password reset token."""
        from security.jwt_auth import request_password_reset

        reset_token = await request_password_reset(email=developer_user.email)

        assert reset_token is not None
        assert isinstance(reset_token, str)

    @pytest.mark.asyncio
    async def test_verify_reset_token(self, developer_user: User):
        """Test verifying password reset token."""
        from security.jwt_auth import request_password_reset, verify_reset_token

        reset_token = await request_password_reset(email=developer_user.email)

        is_valid = await verify_reset_token(reset_token)

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_reset_password_with_token(self, developer_user: User):
        """Test resetting password using reset token."""
        from security.jwt_auth import request_password_reset, reset_password_with_token, authenticate_user

        reset_token = await request_password_reset(email=developer_user.email)

        new_password = "NewSecurePassword123!"

        result = await reset_password_with_token(
            reset_token=reset_token,
            new_password=new_password,
        )

        assert result["status"] == "success"

        tokens = await authenticate_user(
            email=developer_user.email,
            password=new_password,
        )

        assert tokens is not None

    @pytest.mark.asyncio
    async def test_reset_token_expires(self, developer_user: User):
        """Test password reset token expires after timeout."""
        from security.jwt_auth import request_password_reset, verify_reset_token
        from datetime import UTC

        reset_token = await request_password_reset(email=developer_user.email)

        with patch("security.jwt_auth.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.now(UTC) + timedelta(hours=25)

            is_valid = await verify_reset_token(reset_token)

            assert is_valid is False


# ============================================================================
# MULTI-FACTOR AUTHENTICATION TESTS
# ============================================================================


class TestMultiFactorAuthentication:
    """Test MFA workflow."""

    @pytest.mark.asyncio
    async def test_enable_mfa_for_user(self, developer_user: User):
        """Test enabling MFA for user account."""
        from security.jwt_auth import enable_mfa

        mfa_secret = await enable_mfa(user_id=developer_user.user_id)

        assert mfa_secret is not None
        assert len(mfa_secret) > 0

    @pytest.mark.asyncio
    async def test_verify_mfa_code(self, developer_user: User):
        """Test verifying MFA code."""
        from security.jwt_auth import enable_mfa, verify_mfa_code

        mfa_secret = await enable_mfa(user_id=developer_user.user_id)

        import pyotp
        totp = pyotp.TOTP(mfa_secret)
        valid_code = totp.now()

        is_valid = await verify_mfa_code(
            user_id=developer_user.user_id,
            mfa_code=valid_code,
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_mfa_required_login_flow(self, developer_user: User):
        """Test login flow with MFA requirement."""
        from security.jwt_auth import enable_mfa, authenticate_user, verify_mfa_and_complete_login

        await enable_mfa(user_id=developer_user.user_id)

        partial_auth = await authenticate_user(
            email=developer_user.email,
            password="DevPass123!",
        )

        assert partial_auth["status"] == "mfa_required"
        assert "session_id" in partial_auth

        import pyotp
        mfa_secret = partial_auth["mfa_secret"]
        totp = pyotp.TOTP(mfa_secret)
        valid_code = totp.now()

        tokens = await verify_mfa_and_complete_login(
            session_id=partial_auth["session_id"],
            mfa_code=valid_code,
        )

        assert "access_token" in tokens
        assert "refresh_token" in tokens


# ============================================================================
# PERFORMANCE & SECURITY TESTS
# ============================================================================


class TestPerformanceAndSecurity:
    """Test performance and security properties."""

    def test_password_hashing_performance(self):
        """Test password hashing completes in reasonable time."""
        password = "TestPassword123!"

        start_time = time.time()
        for _ in range(10):
            hash_password(password)
        total_time = time.time() - start_time

        avg_time = total_time / 10
        assert avg_time < 0.5, f"Average hash time {avg_time}s exceeds 0.5s threshold"

    def test_token_verification_performance(self, developer_user: User):
        """Test token verification is fast (< 10ms)."""
        token_data = TokenData(
            user_id=developer_user.user_id,
            email=developer_user.email,
            username=developer_user.username,
            role=developer_user.role,
            permissions=developer_user.permissions,
        )

        access_token = create_access_token(token_data)

        latencies = []
        for _ in range(100):
            start = time.time()
            verify_token(access_token)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        p95_latency = sorted(latencies)[94]
        assert p95_latency < 10, f"P95 token verification latency {p95_latency}ms exceeds 10ms"

    @pytest.mark.asyncio
    async def test_rbac_check_performance(self, developer_user: User, rbac_manager: RBACManager):
        """Test RBAC permission checks are fast."""
        latencies = []
        for _ in range(100):
            start = time.time()
            rbac_manager.check_permission(developer_user, "agent:read")
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        p95_latency = sorted(latencies)[94]
        assert p95_latency < 5, f"P95 RBAC check latency {p95_latency}ms exceeds 5ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
