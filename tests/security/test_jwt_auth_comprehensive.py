"""
Comprehensive Test Suite for JWT Authentication Module (RFC 7519 compliant)

Tests JWT token creation, verification, refresh, RBAC enforcement, password hashing,
account lockout, token blacklisting, and security validation.

Per CLAUDE.md Rule #8: Target ≥85% coverage
Per CLAUDE.md Rule #13: Security baseline verification
Per CLAUDE.md Rule #6: Test all 5 RBAC roles

Author: DevSkyy Enterprise Team
Version: 2.0.0
Python: >=3.11.0
"""

from datetime import UTC, datetime, timedelta
import os

from fastapi import HTTPException
import jwt as jwt_lib
import pytest


# Set test JWT secret before importing jwt_auth
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-comprehensive-testing-min-32-chars"

from security.jwt_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    # Constants
    JWT_SECRET_KEY,
    LOCKOUT_DURATION_MINUTES,
    MAX_LOGIN_ATTEMPTS,
    REFRESH_TOKEN_EXPIRE_DAYS,
    APIKeyAuth,
    JWTManager,
    # RBAC
    RoleChecker,
    TokenData,
    TokenResponse,
    # Models
    User,
    # Classes
    UserManager,
    UserRole,
    blacklist_token,
    blacklisted_tokens,
    clear_failed_login_attempts,
    # JWT utilities
    create_access_token,
    create_refresh_token,
    # Helper functions
    create_user_tokens,
    # Globals
    failed_login_attempts,
    get_current_active_user,
    # Authentication dependencies
    get_current_user,
    get_token_payload,
    # Password utilities
    hash_password,
    # Security functions
    is_account_locked,
    is_token_blacklisted,
    locked_accounts,
    record_failed_login,
    require_admin,
    require_authenticated,
    require_developer,
    require_super_admin,
    validate_token_security,
    verify_password,
    verify_token,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def clean_security_state():
    """Clean security state before each test"""
    failed_login_attempts.clear()
    locked_accounts.clear()
    blacklisted_tokens.clear()
    yield
    failed_login_attempts.clear()
    locked_accounts.clear()
    blacklisted_tokens.clear()


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        user_id="test_user_001",
        email="test@devskyy.com",
        username="testuser",
        role=UserRole.DEVELOPER,
        password_hash=hash_password("SecurePass123!"),
    )


@pytest.fixture
def sample_users_all_roles():
    """Create sample users for all 5 RBAC roles"""
    return {
        "super_admin": User(
            user_id="super_001",
            email="super@devskyy.com",
            username="superadmin",
            role=UserRole.SUPER_ADMIN,
            password_hash=hash_password("Super123!"),
        ),
        "admin": User(
            user_id="admin_001",
            email="admin@devskyy.com",
            username="admin",
            role=UserRole.ADMIN,
            password_hash=hash_password("Admin123!"),
        ),
        "developer": User(
            user_id="dev_001",
            email="dev@devskyy.com",
            username="developer",
            role=UserRole.DEVELOPER,
            password_hash=hash_password("Dev123!"),
        ),
        "api_user": User(
            user_id="api_001",
            email="api@devskyy.com",
            username="apiuser",
            role=UserRole.API_USER,
            password_hash=hash_password("Api123!"),
        ),
        "read_only": User(
            user_id="readonly_001",
            email="readonly@devskyy.com",
            username="readonly",
            role=UserRole.READ_ONLY,
            password_hash=hash_password("Read123!"),
        ),
    }


# ============================================================================
# PASSWORD UTILITIES TESTS
# ============================================================================


class TestPasswordUtilities:
    """Test password hashing and verification (Rule #13: Argon2id + bcrypt)"""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string"""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password

    def test_hash_password_different_results(self):
        """Test that hashing same password twice gives different results (salt)"""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "CorrectPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        correct_password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(correct_password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test password verification with empty password"""
        hashed = hash_password("RealPassword123!")

        assert verify_password("", hashed) is False


# ============================================================================
# ACCOUNT SECURITY TESTS
# ============================================================================


class TestAccountSecurity:
    """Test account lockout and failed login tracking"""

    def test_is_account_locked_initially_false(self):
        """Test that account is not locked initially"""
        assert is_account_locked("test@example.com") is False

    def test_record_failed_login_single_attempt(self):
        """Test recording a single failed login attempt"""
        email = "test@example.com"
        is_locked = record_failed_login(email)

        assert is_locked is False
        assert email in failed_login_attempts
        assert len(failed_login_attempts[email]) == 1

    def test_record_failed_login_multiple_attempts(self):
        """Test recording multiple failed login attempts"""
        email = "test@example.com"

        for i in range(MAX_LOGIN_ATTEMPTS - 1):
            is_locked = record_failed_login(email)
            assert is_locked is False

        assert len(failed_login_attempts[email]) == MAX_LOGIN_ATTEMPTS - 1

    def test_account_locks_after_max_attempts(self):
        """Test account locks after MAX_LOGIN_ATTEMPTS"""
        email = "test@example.com"

        # Record MAX_LOGIN_ATTEMPTS failed attempts
        for i in range(MAX_LOGIN_ATTEMPTS):
            record_failed_login(email)

        assert is_account_locked(email) is True
        assert email in locked_accounts

    def test_clear_failed_login_attempts(self):
        """Test clearing failed login attempts"""
        email = "test@example.com"

        # Record some failed attempts
        for i in range(3):
            record_failed_login(email)

        # Clear attempts
        clear_failed_login_attempts(email)

        assert email not in failed_login_attempts
        assert email not in locked_accounts

    def test_account_lock_expires(self):
        """Test that account lock expires after LOCKOUT_DURATION_MINUTES"""
        email = "test@example.com"

        # Lock account with expired time
        past_time = datetime.now() - timedelta(minutes=LOCKOUT_DURATION_MINUTES + 1)
        locked_accounts[email] = past_time

        # Should not be locked anymore
        assert is_account_locked(email) is False
        assert email not in locked_accounts

    def test_failed_attempts_cleaned_after_one_hour(self):
        """Test that old failed attempts are cleaned"""
        email = "test@example.com"

        # Add old attempt (>1 hour ago)
        old_time = datetime.now() - timedelta(hours=2)
        failed_login_attempts[email] = [old_time]

        # Record new attempt (should clean old ones)
        record_failed_login(email)

        # Should only have 1 attempt (the new one)
        assert len(failed_login_attempts[email]) == 1
        assert failed_login_attempts[email][0] > old_time


# ============================================================================
# TOKEN BLACKLIST TESTS
# ============================================================================


class TestTokenBlacklist:
    """Test token blacklisting functionality"""

    def test_blacklist_token_adds_to_set(self):
        """Test that blacklist_token adds token to blacklist"""
        token = "test.jwt.token"
        blacklist_token(token)

        assert token in blacklisted_tokens

    def test_is_token_blacklisted_returns_true(self):
        """Test is_token_blacklisted for blacklisted token"""
        token = "test.jwt.token"
        blacklist_token(token)

        assert is_token_blacklisted(token) is True

    def test_is_token_blacklisted_returns_false(self):
        """Test is_token_blacklisted for non-blacklisted token"""
        token = "test.jwt.token"

        assert is_token_blacklisted(token) is False

    def test_validate_token_security_blacklisted(self):
        """Test validate_token_security rejects blacklisted token"""
        token = "test.jwt.token"
        blacklist_token(token)

        token_data = TokenData(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            role=UserRole.DEVELOPER,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )

        assert validate_token_security(token, token_data) is False


# ============================================================================
# JWT TOKEN CREATION TESTS
# ============================================================================


class TestJWTTokenCreation:
    """Test JWT token creation (RFC 7519)"""

    def test_create_access_token_basic(self):
        """Test basic access token creation"""
        data = {"user_id": "user123", "email": "test@example.com", "role": UserRole.DEVELOPER}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT format: header.payload.signature

    def test_create_access_token_payload_structure(self):
        """Test access token payload structure"""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.DEVELOPER,
        }
        token = create_access_token(data)

        payload = get_token_payload(token)
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["token_type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_custom_expiry(self):
        """Test access token with custom expiration"""
        data = {"user_id": "user123", "email": "test@example.com"}
        custom_expiry = timedelta(minutes=5)
        token = create_access_token(data, expires_delta=custom_expiry)

        payload = get_token_payload(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=UTC)

        # Check expiry is approximately 5 minutes from issue time
        time_diff = exp_time - iat_time
        assert 4.9 * 60 < time_diff.total_seconds() < 5.1 * 60

    def test_create_refresh_token_basic(self):
        """Test basic refresh token creation"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_payload_structure(self):
        """Test refresh token payload structure"""
        data = {
            "user_id": "user456",
            "email": "refresh@example.com",
            "username": "refreshuser",
            "role": UserRole.API_USER,
        }
        token = create_refresh_token(data)

        payload = get_token_payload(token)
        assert payload is not None
        assert payload["user_id"] == "user456"
        assert payload["token_type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_create_refresh_token_expiry_7_days(self):
        """Test refresh token expires in 7 days"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = create_refresh_token(data)

        payload = get_token_payload(token)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=UTC)

        # Check expiry is approximately 7 days
        time_diff = exp_time - iat_time
        expected_seconds = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        assert expected_seconds - 60 < time_diff.total_seconds() < expected_seconds + 60

    def test_get_token_payload_valid_token(self):
        """Test getting payload from valid token"""
        data = {"user_id": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        payload = get_token_payload(token)
        assert payload is not None
        assert isinstance(payload, dict)

    def test_get_token_payload_invalid_token(self):
        """Test getting payload from invalid token returns None"""
        invalid_token = "invalid.jwt.token"

        payload = get_token_payload(invalid_token)
        assert payload is None


# ============================================================================
# JWT TOKEN VERIFICATION TESTS
# ============================================================================


class TestJWTTokenVerification:
    """Test JWT token verification"""

    def test_verify_token_valid_access_token(self):
        """Test verifying valid access token"""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.DEVELOPER,
        }
        token = create_access_token(data)

        token_data = verify_token(token, token_type="access")

        assert token_data.user_id == "user123"
        assert token_data.email == "test@example.com"
        assert token_data.username == "testuser"
        assert token_data.role == UserRole.DEVELOPER
        assert token_data.token_type == "access"

    def test_verify_token_valid_refresh_token(self):
        """Test verifying valid refresh token"""
        data = {
            "user_id": "user456",
            "email": "refresh@example.com",
            "username": "refreshuser",
            "role": UserRole.API_USER,
        }
        token = create_refresh_token(data)

        token_data = verify_token(token, token_type="refresh")

        assert token_data.user_id == "user456"
        assert token_data.token_type == "refresh"

    def test_verify_token_wrong_type(self):
        """Test verify_token fails with wrong token type"""
        data = {"user_id": "user123", "email": "test@example.com"}
        access_token = create_access_token(data)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(access_token, token_type="refresh")

        assert exc_info.value.status_code == 401

    def test_verify_token_expired_token(self):
        """Test verify_token fails with expired token"""
        data = {"user_id": "user123", "email": "test@example.com"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_token_invalid_signature(self):
        """Test verify_token fails with invalid signature"""
        # Create token with different secret
        data = {"user_id": "user123", "email": "test@example.com", "token_type": "access"}
        token = jwt_lib.encode(
            {**data, "exp": datetime.now(UTC) + timedelta(minutes=15), "iat": datetime.now(UTC)},
            "wrong-secret-key",
            algorithm=JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_user_id(self):
        """Test verify_token fails with missing user_id"""
        # Create token without user_id
        payload = {
            "email": "test@example.com",
            "token_type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
        }
        token = jwt_lib.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_missing_email(self):
        """Test verify_token fails with missing email"""
        # Create token without email
        payload = {
            "user_id": "user123",
            "token_type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
            "iat": datetime.now(UTC),
        }
        token = jwt_lib.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")

        assert exc_info.value.status_code == 401

    def test_verify_token_blacklisted(self):
        """Test verify_token fails with blacklisted token"""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.DEVELOPER,
        }
        token = create_access_token(data)

        # Blacklist the token
        blacklist_token(token)

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token, token_type="access")

        assert exc_info.value.status_code == 401
        # May raise either security validation error or general validation error
        assert ("security validation failed" in exc_info.value.detail.lower() or
                "could not validate" in exc_info.value.detail.lower())


# ============================================================================
# AUTHENTICATION DEPENDENCIES TESTS
# ============================================================================


class TestAuthenticationDependencies:
    """Test FastAPI authentication dependencies"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test get_current_user with valid token"""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "username": "testuser",
            "role": UserRole.DEVELOPER,
        }
        token = create_access_token(data)

        user = await get_current_user(token)

        assert user.user_id == "user123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.DEVELOPER

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("invalid.token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_active_user(self):
        """Test get_current_active_user"""
        token_data = TokenData(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            role=UserRole.DEVELOPER,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )

        user = await get_current_active_user(token_data)

        assert user.user_id == "user123"
        assert user.email == "test@example.com"


# ============================================================================
# RBAC TESTS (ALL 5 ROLES)
# ============================================================================


class TestRBAC:
    """Test Role-Based Access Control for all 5 roles (Rule #6)"""

    def test_user_roles_exist(self):
        """Test all 5 user roles are defined"""
        assert UserRole.SUPER_ADMIN == "super_admin"
        assert UserRole.ADMIN == "admin"
        assert UserRole.DEVELOPER == "developer"
        assert UserRole.API_USER == "api_user"
        assert UserRole.READ_ONLY == "read_only"

    def test_role_checker_allows_correct_role(self):
        """Test RoleChecker allows correct role"""
        checker = RoleChecker([UserRole.DEVELOPER])

        token_data = TokenData(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            role=UserRole.DEVELOPER,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )

        # Should not raise exception
        result = checker(token_data)
        assert result == token_data

    def test_role_checker_denies_incorrect_role(self):
        """Test RoleChecker denies incorrect role"""
        checker = RoleChecker([UserRole.ADMIN])

        token_data = TokenData(
            user_id="user123",
            email="test@example.com",
            username="testuser",
            role=UserRole.READ_ONLY,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )

        with pytest.raises(HTTPException) as exc_info:
            checker(token_data)

        assert exc_info.value.status_code == 403
        assert "forbidden" in exc_info.value.detail.lower()

    def test_role_checker_allows_multiple_roles(self):
        """Test RoleChecker allows multiple roles"""
        checker = RoleChecker([UserRole.ADMIN, UserRole.DEVELOPER])

        # Test with ADMIN
        admin_data = TokenData(
            user_id="admin123",
            email="admin@example.com",
            username="admin",
            role=UserRole.ADMIN,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )
        result = checker(admin_data)
        assert result == admin_data

        # Test with DEVELOPER
        dev_data = TokenData(
            user_id="dev123",
            email="dev@example.com",
            username="developer",
            role=UserRole.DEVELOPER,
            token_type="access",
            exp=datetime.now() + timedelta(minutes=15),
        )
        result = checker(dev_data)
        assert result == dev_data

    def test_require_super_admin_checker(self):
        """Test require_super_admin predefined checker"""
        assert isinstance(require_super_admin, RoleChecker)
        assert UserRole.SUPER_ADMIN in require_super_admin.allowed_roles
        assert len(require_super_admin.allowed_roles) == 1

    def test_require_admin_checker(self):
        """Test require_admin predefined checker"""
        assert isinstance(require_admin, RoleChecker)
        assert UserRole.SUPER_ADMIN in require_admin.allowed_roles
        assert UserRole.ADMIN in require_admin.allowed_roles

    def test_require_developer_checker(self):
        """Test require_developer predefined checker"""
        assert isinstance(require_developer, RoleChecker)
        assert UserRole.SUPER_ADMIN in require_developer.allowed_roles
        assert UserRole.ADMIN in require_developer.allowed_roles
        assert UserRole.DEVELOPER in require_developer.allowed_roles

    def test_require_authenticated_checker(self):
        """Test require_authenticated checker allows all roles"""
        assert isinstance(require_authenticated, RoleChecker)
        assert UserRole.SUPER_ADMIN in require_authenticated.allowed_roles
        assert UserRole.ADMIN in require_authenticated.allowed_roles
        assert UserRole.DEVELOPER in require_authenticated.allowed_roles
        assert UserRole.API_USER in require_authenticated.allowed_roles
        assert UserRole.READ_ONLY in require_authenticated.allowed_roles

    def test_all_five_roles_token_creation(self, sample_users_all_roles):
        """Test token creation for all 5 RBAC roles"""
        for role_name, user in sample_users_all_roles.items():
            tokens = create_user_tokens(user)

            assert isinstance(tokens, TokenResponse)
            assert len(tokens.access_token) > 0
            assert len(tokens.refresh_token) > 0

            # Verify token contains correct role
            payload = get_token_payload(tokens.access_token)
            assert payload["role"] == user.role

    def test_all_five_roles_token_verification(self, sample_users_all_roles):
        """Test token verification for all 5 RBAC roles"""
        for role_name, user in sample_users_all_roles.items():
            data = {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
            }
            token = create_access_token(data)

            token_data = verify_token(token, token_type="access")
            assert token_data.role == user.role


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelperFunctions:
    """Test helper functions"""

    def test_create_user_tokens(self, sample_user):
        """Test create_user_tokens function"""
        tokens = create_user_tokens(sample_user)

        assert isinstance(tokens, TokenResponse)
        assert len(tokens.access_token) > 0
        assert len(tokens.refresh_token) > 0
        assert tokens.token_type == "bearer"
        assert tokens.expires_in == ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_create_user_tokens_payload_verification(self, sample_user):
        """Test create_user_tokens generates correct payloads"""
        tokens = create_user_tokens(sample_user)

        # Verify access token
        access_payload = get_token_payload(tokens.access_token)
        assert access_payload["user_id"] == sample_user.user_id
        assert access_payload["email"] == sample_user.email
        assert access_payload["username"] == sample_user.username
        assert access_payload["role"] == sample_user.role
        assert access_payload["token_type"] == "access"

        # Verify refresh token
        refresh_payload = get_token_payload(tokens.refresh_token)
        assert refresh_payload["user_id"] == sample_user.user_id
        assert refresh_payload["token_type"] == "refresh"


# ============================================================================
# USER MANAGER TESTS
# ============================================================================


class TestUserManager:
    """Test UserManager class"""

    def test_user_manager_initialization(self):
        """Test UserManager initializes with default users"""
        manager = UserManager()

        assert len(manager.users) >= 2  # At least admin and api_user
        assert "admin@devskyy.com" in manager.email_index
        assert "api@devskyy.com" in manager.email_index

    def test_create_user(self):
        """Test creating a new user"""
        manager = UserManager()

        user = manager.create_user(
            email="newuser@example.com",
            username="newuser",
            password="SecurePass123!",
            role=UserRole.DEVELOPER,
        )

        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.role == UserRole.DEVELOPER
        assert user.password_hash is not None
        assert user.user_id in manager.users

    def test_create_user_duplicate_email(self):
        """Test creating user with duplicate email fails"""
        manager = UserManager()

        manager.create_user(
            email="duplicate@example.com",
            username="user1",
            password="Pass123!",
        )

        with pytest.raises(ValueError) as exc_info:
            manager.create_user(
                email="duplicate@example.com",
                username="user2",
                password="Pass123!",
            )

        assert "already exists" in str(exc_info.value)

    def test_create_user_duplicate_username(self):
        """Test creating user with duplicate username fails"""
        manager = UserManager()

        manager.create_user(
            email="user1@example.com",
            username="duplicateuser",
            password="Pass123!",
        )

        with pytest.raises(ValueError) as exc_info:
            manager.create_user(
                email="user2@example.com",
                username="duplicateuser",
                password="Pass123!",
            )

        assert "already exists" in str(exc_info.value)

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        manager = UserManager()

        user = manager.create_user(
            email="test@example.com",
            username="testuser",
            password="Pass123!",
        )

        retrieved = manager.get_user_by_id(user.user_id)
        assert retrieved is not None
        assert retrieved.user_id == user.user_id
        assert retrieved.email == user.email

    def test_get_user_by_email(self):
        """Test getting user by email"""
        manager = UserManager()

        user = manager.create_user(
            email="email@example.com",
            username="testuser",
            password="Pass123!",
        )

        retrieved = manager.get_user_by_email("email@example.com")
        assert retrieved is not None
        assert retrieved.email == user.email

    def test_get_user_by_username(self):
        """Test getting user by username"""
        manager = UserManager()

        user = manager.create_user(
            email="test@example.com",
            username="uniqueuser",
            password="Pass123!",
        )

        retrieved = manager.get_user_by_username("uniqueuser")
        assert retrieved is not None
        assert retrieved.username == user.username

    def test_authenticate_user_success_with_email(self):
        """Test successful authentication with email"""
        manager = UserManager()
        password = "SecurePass123!"

        manager.create_user(
            email="auth@example.com",
            username="authuser",
            password=password,
        )

        authenticated = manager.authenticate_user("auth@example.com", password)
        assert authenticated is not None
        assert authenticated.email == "auth@example.com"

    def test_authenticate_user_success_with_username(self):
        """Test successful authentication with username"""
        manager = UserManager()
        password = "SecurePass123!"

        manager.create_user(
            email="auth@example.com",
            username="authuser",
            password=password,
        )

        authenticated = manager.authenticate_user("authuser", password)
        assert authenticated is not None
        assert authenticated.username == "authuser"

    def test_authenticate_user_wrong_password(self):
        """Test authentication fails with wrong password"""
        manager = UserManager()

        manager.create_user(
            email="auth@example.com",
            username="authuser",
            password="CorrectPass123!",
        )

        authenticated = manager.authenticate_user("auth@example.com", "WrongPass123!")
        assert authenticated is None

    def test_authenticate_user_nonexistent(self):
        """Test authentication fails for nonexistent user"""
        manager = UserManager()

        authenticated = manager.authenticate_user("nonexistent@example.com", "Pass123!")
        assert authenticated is None


# ============================================================================
# JWT MANAGER TESTS
# ============================================================================


class TestJWTManager:
    """Test JWTManager unified interface"""

    def test_jwt_manager_initialization(self):
        """Test JWTManager initializes correctly"""
        manager = JWTManager()

        assert manager.secret_key == JWT_SECRET_KEY
        assert manager.algorithm == JWT_ALGORITHM
        assert manager.access_token_expire_minutes == ACCESS_TOKEN_EXPIRE_MINUTES
        assert manager.refresh_token_expire_days == REFRESH_TOKEN_EXPIRE_DAYS

    def test_jwt_manager_create_access_token(self, sample_user):
        """Test JWTManager.create_access_token"""
        manager = JWTManager()

        token = manager.create_access_token(sample_user)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_manager_create_refresh_token(self, sample_user):
        """Test JWTManager.create_refresh_token"""
        manager = JWTManager()

        token = manager.create_refresh_token(sample_user)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_manager_create_user_tokens(self, sample_user):
        """Test JWTManager.create_user_tokens"""
        manager = JWTManager()

        tokens = manager.create_user_tokens(sample_user)

        assert isinstance(tokens, TokenResponse)
        assert len(tokens.access_token) > 0
        assert len(tokens.refresh_token) > 0

    def test_jwt_manager_verify_token(self, sample_user):
        """Test JWTManager.verify_token"""
        manager = JWTManager()

        # Use create_user_tokens which creates properly formatted tokens
        tokens = manager.create_user_tokens(sample_user)
        token_data = manager.verify_token(tokens.access_token, token_type="access")

        assert token_data.user_id == sample_user.user_id
        assert token_data.email == sample_user.email

    def test_jwt_manager_authenticate_user(self):
        """Test JWTManager.authenticate_user"""
        manager = JWTManager()
        password = "TestPass123!"

        # Create user via user_manager
        manager.user_manager.create_user(
            email="jwtauth@example.com",
            username="jwtuser",
            password=password,
        )

        authenticated = manager.authenticate_user("jwtauth@example.com", password)
        assert authenticated is not None
        assert authenticated.email == "jwtauth@example.com"

    def test_jwt_manager_blacklist_token(self):
        """Test JWTManager.blacklist_token"""
        manager = JWTManager()
        token = "test.jwt.token"

        manager.blacklist_token(token)
        assert manager.is_token_blacklisted(token) is True

    def test_jwt_manager_check_role_permission(self):
        """Test JWTManager.check_role_permission"""
        manager = JWTManager()

        # Super admin should have permission for everything
        assert manager.check_role_permission(UserRole.SUPER_ADMIN, UserRole.READ_ONLY) is True
        assert manager.check_role_permission(UserRole.SUPER_ADMIN, UserRole.ADMIN) is True

        # Admin should have permission for developer and below
        assert manager.check_role_permission(UserRole.ADMIN, UserRole.DEVELOPER) is True
        assert manager.check_role_permission(UserRole.ADMIN, UserRole.API_USER) is True

        # Developer should not have admin permission
        assert manager.check_role_permission(UserRole.DEVELOPER, UserRole.ADMIN) is False

        # Read-only should not have any higher permissions
        assert manager.check_role_permission(UserRole.READ_ONLY, UserRole.API_USER) is False


# ============================================================================
# API KEY AUTHENTICATION TESTS
# ============================================================================


class TestAPIKeyAuth:
    """Test API Key authentication"""

    def test_api_key_auth_validate_missing_security_manager(self):
        """Test API key validation when security_manager is not available"""
        from fastapi.security import HTTPAuthorizationCredentials

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-api-key-123",
        )

        # This should fail because security_manager might not be available
        with pytest.raises(HTTPException) as exc_info:
            APIKeyAuth.validate_api_key(credentials)

        assert exc_info.value.status_code == 401


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests for complete authentication flows"""

    def test_complete_authentication_flow(self):
        """Test complete user authentication flow"""
        manager = JWTManager()
        password = "SecurePass123!"

        # 1. Create user
        user = manager.user_manager.create_user(
            email="integration@example.com",
            username="integrationuser",
            password=password,
            role=UserRole.DEVELOPER,
        )

        # 2. Authenticate user
        authenticated = manager.authenticate_user("integration@example.com", password)
        assert authenticated is not None

        # 3. Create tokens
        tokens = manager.create_user_tokens(authenticated)
        assert len(tokens.access_token) > 0

        # 4. Verify access token
        token_data = manager.verify_token(tokens.access_token, token_type="access")
        assert token_data.user_id == user.user_id
        assert token_data.role == UserRole.DEVELOPER

        # 5. Verify refresh token
        refresh_data = manager.verify_token(tokens.refresh_token, token_type="refresh")
        assert refresh_data.user_id == user.user_id

    def test_failed_login_and_lockout_flow(self):
        """Test failed login attempts leading to account lockout"""
        manager = JWTManager()
        email = "lockout@example.com"

        # Create user
        manager.user_manager.create_user(
            email=email,
            username="lockoutuser",
            password="CorrectPass123!",
            role=UserRole.API_USER,
        )

        # Attempt multiple failed logins
        for i in range(MAX_LOGIN_ATTEMPTS):
            authenticated = manager.authenticate_user(email, "WrongPass!")
            assert authenticated is None
            record_failed_login(email)

        # Account should now be locked
        assert is_account_locked(email) is True

        # Even correct password should fail when locked
        # (In production, check lockout before authentication)
        clear_failed_login_attempts(email)

    def test_token_refresh_and_blacklist_flow(self, sample_user):
        """Test token refresh and old token blacklisting"""
        manager = JWTManager()

        # Create initial tokens
        tokens = manager.create_user_tokens(sample_user)
        old_access_token = tokens.access_token

        # Verify old token works
        token_data = manager.verify_token(old_access_token, token_type="access")
        assert token_data.user_id == sample_user.user_id

        # Blacklist old token (simulate refresh)
        manager.blacklist_token(old_access_token)

        # Old token should now fail
        with pytest.raises(HTTPException):
            manager.verify_token(old_access_token, token_type="access")


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_token_with_empty_user_id(self):
        """Test token creation with empty user_id"""
        data = {"user_id": "", "email": "test@example.com"}
        token = create_access_token(data)

        payload = get_token_payload(token)
        assert payload["user_id"] == ""

    def test_token_with_special_characters(self):
        """Test token with special characters in data"""
        data = {
            "user_id": "user@#$%123",
            "email": "special+chars@example.com",
            "username": "user-name_123",
        }
        token = create_access_token(data)

        payload = get_token_payload(token)
        assert payload["user_id"] == "user@#$%123"
        assert payload["email"] == "special+chars@example.com"

    def test_verify_token_with_malformed_jwt(self):
        """Test verify_token with malformed JWT"""
        malformed_tokens = [
            "not.a.jwt",
            "only.two",
            "too.many.parts.here.five",
            "",
            "single_string_no_dots",
        ]

        for malformed_token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                verify_token(malformed_token, token_type="access")
            assert exc_info.value.status_code == 401

    def test_password_hashing_unicode_characters(self):
        """Test password hashing with unicode characters"""
        password = "Pass密码🔐123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass!", hashed) is False

    def test_concurrent_failed_login_attempts(self):
        """Test concurrent failed login attempts from same email"""
        email = "concurrent@example.com"

        # Simulate concurrent attempts
        for i in range(MAX_LOGIN_ATTEMPTS + 2):
            record_failed_login(email)

        assert is_account_locked(email) is True
        assert len(failed_login_attempts[email]) >= MAX_LOGIN_ATTEMPTS


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=security.jwt_auth",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
