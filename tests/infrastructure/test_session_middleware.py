"""
Comprehensive tests for infrastructure/session_middleware.py

WHY: Ensure session middleware works correctly with ≥80% coverage
HOW: Test session management, authentication, FastAPI middleware, and dependencies
IMPACT: Validates enterprise session management infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥80%
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
import pytest
from starlette.responses import JSONResponse

from infrastructure.redis_manager import SessionData
from infrastructure.session_middleware import (
    SessionManager,
    SessionMiddleware,
    get_current_session,
    require_authentication,
    require_fashion_expert,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_redis_manager():
    """Mock Redis manager for testing."""
    with patch("infrastructure.session_middleware.redis_manager") as mock:
        mock.get_session = AsyncMock(return_value=None)
        mock.update_session_access = AsyncMock(return_value=True)
        mock.create_session = AsyncMock(return_value=True)
        mock.delete_session = AsyncMock(return_value=True)
        mock.cleanup_expired_sessions = AsyncMock(return_value=5)
        mock.get_metrics = AsyncMock(return_value={})
        yield mock


@pytest.fixture
def session_middleware(mock_redis_manager):
    """Create SessionMiddleware instance."""
    app = MagicMock()
    middleware = SessionMiddleware(
        app=app,
        session_cookie_name="test_session",
        session_cookie_max_age=3600,
        session_cookie_secure=True,
        session_cookie_httponly=True,
        session_cookie_samesite="lax",
    )
    return middleware


@pytest.fixture
def session_manager(session_middleware):
    """Create SessionManager instance."""
    return SessionManager(session_middleware)


@pytest.fixture
def sample_session_data():
    """Create sample session data."""
    return SessionData(
        user_id="user123",
        username="testuser",
        email="test@example.com",
        role="admin",
        permissions=["read", "write", "delete"],
        created_at=datetime(2025, 11, 23, 10, 0, 0),
        last_accessed=datetime(2025, 11, 23, 11, 0, 0),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
        fashion_preferences={"style": "modern"},
    )


@pytest.fixture
def mock_request():
    """Create mock FastAPI Request."""
    request = MagicMock()
    request.state = MagicMock()
    request.state.session_id = None
    request.state.session_data = None
    request.state.user_id = None
    request.state.user_role = None
    request.state.user_permissions = []
    request.url = MagicMock()
    request.url.path = "/api/v1/test"
    request.cookies = {}
    return request


@pytest.fixture
def mock_response():
    """Create mock FastAPI Response."""
    response = MagicMock()
    response.set_cookie = MagicMock()
    response.delete_cookie = MagicMock()
    response.headers = {}
    return response


# ============================================================================
# TEST SessionMiddleware Initialization
# ============================================================================


class TestSessionMiddlewareInitialization:
    """Test SessionMiddleware initialization."""

    def test_middleware_initialization(self, session_middleware):
        """Test middleware initializes with correct settings."""
        assert session_middleware.session_cookie_name == "test_session"
        assert session_middleware.session_cookie_max_age == 3600
        assert session_middleware.session_cookie_secure is True
        assert session_middleware.session_cookie_httponly is True
        assert session_middleware.session_cookie_samesite == "lax"

    def test_middleware_default_protected_paths(self, session_middleware):
        """Test middleware has default protected paths."""
        assert "/api/v1/agents/" in session_middleware.require_session_for_paths
        assert "/api/v1/ml/" in session_middleware.require_session_for_paths
        assert "/api/v1/analytics/" in session_middleware.require_session_for_paths
        assert "/api/v1/fashion/" in session_middleware.require_session_for_paths

    def test_middleware_fashion_tracking_enabled(self, session_middleware):
        """Test fashion tracking is enabled by default."""
        assert session_middleware.fashion_tracking_enabled is True


# ============================================================================
# TEST Session Loading
# ============================================================================


class TestSessionLoading:
    """Test session loading in middleware dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_no_session_cookie(self, session_middleware, mock_request, mock_redis_manager):
        """Test dispatch with no session cookie."""
        mock_request.cookies = {}

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        await session_middleware.dispatch(mock_request, call_next)

        assert mock_request.state.session_id is None
        assert mock_request.state.session_data is None

    @pytest.mark.asyncio
    async def test_dispatch_with_valid_session(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test dispatch with valid session cookie."""
        mock_request.cookies = {"test_session": "sess123"}
        mock_redis_manager.get_session = AsyncMock(return_value=sample_session_data)

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        await session_middleware.dispatch(mock_request, call_next)

        assert mock_request.state.session_id == "sess123"
        assert mock_request.state.session_data == sample_session_data
        assert mock_request.state.user_id == "user123"
        assert mock_request.state.user_role == "admin"

    @pytest.mark.asyncio
    async def test_dispatch_with_invalid_session(self, session_middleware, mock_request, mock_redis_manager):
        """Test dispatch with invalid session cookie."""
        mock_request.cookies = {"test_session": "invalid_sess"}
        mock_redis_manager.get_session = AsyncMock(return_value=None)

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        await session_middleware.dispatch(mock_request, call_next)

        assert mock_request.state.session_id is None
        assert mock_request.state.session_data is None

    @pytest.mark.asyncio
    async def test_dispatch_updates_session_access(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test dispatch updates session access time."""
        mock_request.cookies = {"test_session": "sess123"}
        mock_redis_manager.get_session = AsyncMock(return_value=sample_session_data)

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        await session_middleware.dispatch(mock_request, call_next)

        # Should have called update_session_access
        mock_redis_manager.update_session_access.assert_called_once_with("sess123")

    @pytest.mark.asyncio
    async def test_dispatch_loads_fashion_preferences(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test dispatch loads fashion preferences."""
        mock_request.cookies = {"test_session": "sess123"}
        mock_redis_manager.get_session = AsyncMock(return_value=sample_session_data)

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        await session_middleware.dispatch(mock_request, call_next)

        assert hasattr(mock_request.state, "fashion_preferences")
        assert mock_request.state.fashion_preferences == {"style": "modern"}


# ============================================================================
# TEST Protected Path Authentication
# ============================================================================


class TestProtectedPathAuthentication:
    """Test authentication for protected paths."""

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_no_session(self, session_middleware, mock_request, mock_redis_manager):
        """Test protected path rejects requests without session."""
        mock_request.url.path = "/api/v1/agents/list"
        mock_request.cookies = {}

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        response = await session_middleware.dispatch(mock_request, call_next)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dispatch_protected_path_with_session(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test protected path allows requests with valid session."""
        mock_request.url.path = "/api/v1/agents/list"
        mock_request.cookies = {"test_session": "sess123"}
        mock_redis_manager.get_session = AsyncMock(return_value=sample_session_data)

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        response = await session_middleware.dispatch(mock_request, call_next)

        # Should not be a 401 response
        assert not isinstance(response, JSONResponse) or response.status_code != 401

    @pytest.mark.asyncio
    async def test_dispatch_public_path_no_session(self, session_middleware, mock_request, mock_redis_manager):
        """Test public path allows requests without session."""
        mock_request.url.path = "/api/v1/health"
        mock_request.cookies = {}

        # Mock call_next
        async def call_next(request):
            return MagicMock(headers={})

        response = await session_middleware.dispatch(mock_request, call_next)

        # Should not be a 401 response
        assert not isinstance(response, JSONResponse) or response.status_code != 401


# ============================================================================
# TEST Session Creation
# ============================================================================


class TestSessionCreation:
    """Test session creation."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_middleware, mock_response, mock_redis_manager):
        """Test successful session creation."""
        session_id = await session_middleware.create_session(
            response=mock_response,
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role="admin",
            permissions=["read", "write"],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert session_id.startswith("sess_")
        mock_response.set_cookie.assert_called_once()
        mock_redis_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_with_fashion_preferences(self, session_middleware, mock_response, mock_redis_manager):
        """Test session creation with fashion preferences."""
        fashion_prefs = {"style": "casual", "colors": ["blue", "green"]}

        session_id = await session_middleware.create_session(
            response=mock_response,
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role="fashion_expert",
            permissions=["read"],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            fashion_preferences=fashion_prefs,
        )

        assert session_id is not None
        # Verify fashion preferences were passed
        call_args = mock_redis_manager.create_session.call_args[0]
        session_data = call_args[1]
        assert session_data.fashion_preferences == fashion_prefs

    @pytest.mark.asyncio
    async def test_create_session_sets_cookie(self, session_middleware, mock_response, mock_redis_manager):
        """Test session creation sets secure cookie."""
        await session_middleware.create_session(
            response=mock_response,
            user_id="user123",
            username="testuser",
            email="test@example.com",
            role="admin",
            permissions=["read"],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        # Verify cookie settings
        call_kwargs = mock_response.set_cookie.call_args[1]
        assert call_kwargs["key"] == "test_session"
        assert call_kwargs["secure"] is True
        assert call_kwargs["httponly"] is True
        assert call_kwargs["samesite"] == "lax"

    @pytest.mark.asyncio
    async def test_create_session_failure(self, session_middleware, mock_response, mock_redis_manager):
        """Test session creation handles Redis failure."""
        mock_redis_manager.create_session = AsyncMock(return_value=False)

        with pytest.raises(HTTPException) as exc_info:
            await session_middleware.create_session(
                response=mock_response,
                user_id="user123",
                username="testuser",
                email="test@example.com",
                role="admin",
                permissions=["read"],
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

        assert exc_info.value.status_code == 500


# ============================================================================
# TEST Session Destruction
# ============================================================================


class TestSessionDestruction:
    """Test session destruction."""

    @pytest.mark.asyncio
    async def test_destroy_session_success(self, session_middleware, mock_request, mock_response, mock_redis_manager):
        """Test successful session destruction."""
        mock_request.state.session_id = "sess123"

        result = await session_middleware.destroy_session(mock_request, mock_response)

        assert result is True
        mock_redis_manager.delete_session.assert_called_once_with("sess123")
        mock_response.delete_cookie.assert_called_once()

    @pytest.mark.asyncio
    async def test_destroy_session_no_session(self, session_middleware, mock_request, mock_response, mock_redis_manager):
        """Test destroying session when no session exists."""
        mock_request.state.session_id = None

        result = await session_middleware.destroy_session(mock_request, mock_response)

        assert result is False
        mock_redis_manager.delete_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_destroy_session_clears_cookie(self, session_middleware, mock_request, mock_response, mock_redis_manager):
        """Test session destruction clears cookie."""
        mock_request.state.session_id = "sess123"

        await session_middleware.destroy_session(mock_request, mock_response)

        # Verify cookie is deleted with correct settings
        call_kwargs = mock_response.delete_cookie.call_args[1]
        assert call_kwargs["key"] == "test_session"
        assert call_kwargs["secure"] is True
        assert call_kwargs["httponly"] is True


# ============================================================================
# TEST Fashion Preferences Update
# ============================================================================


class TestFashionPreferencesUpdate:
    """Test updating fashion preferences."""

    @pytest.mark.asyncio
    async def test_update_fashion_preferences_success(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test successful fashion preferences update."""
        mock_request.state.session_id = "sess123"
        mock_request.state.session_data = sample_session_data

        new_prefs = {"style": "elegant", "colors": ["black", "white"]}

        result = await session_middleware.update_fashion_preferences(mock_request, new_prefs)

        assert result is True
        mock_redis_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_fashion_preferences_no_session(self, session_middleware, mock_request, mock_redis_manager):
        """Test updating preferences with no session."""
        mock_request.state.session_id = None
        mock_request.state.session_data = None

        result = await session_middleware.update_fashion_preferences(mock_request, {})

        assert result is False

    @pytest.mark.asyncio
    async def test_update_fashion_preferences_updates_request_state(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test preferences update modifies request state."""
        mock_request.state.session_id = "sess123"
        mock_request.state.session_data = sample_session_data

        new_prefs = {"style": "vintage"}

        await session_middleware.update_fashion_preferences(mock_request, new_prefs)

        assert hasattr(mock_request.state, "fashion_preferences")
        assert mock_request.state.fashion_preferences == new_prefs


# ============================================================================
# TEST SessionManager Utilities
# ============================================================================


class TestSessionManagerUtilities:
    """Test SessionManager utility methods."""

    def test_get_session_data(self, session_manager, mock_request, sample_session_data):
        """Test getting session data from request."""
        mock_request.state.session_data = sample_session_data

        result = SessionManager.get_session_data(mock_request)

        assert result == sample_session_data

    def test_get_session_data_none(self, session_manager, mock_request):
        """Test getting session data when none exists."""
        result = SessionManager.get_session_data(mock_request)

        assert result is None

    def test_get_user_id(self, session_manager, mock_request):
        """Test getting user ID from session."""
        mock_request.state.user_id = "user123"

        result = SessionManager.get_user_id(mock_request)

        assert result == "user123"

    def test_get_user_role(self, session_manager, mock_request):
        """Test getting user role from session."""
        mock_request.state.user_role = "admin"

        result = SessionManager.get_user_role(mock_request)

        assert result == "admin"

    def test_get_user_permissions(self, session_manager, mock_request):
        """Test getting user permissions from session."""
        mock_request.state.user_permissions = ["read", "write"]

        result = SessionManager.get_user_permissions(mock_request)

        assert result == ["read", "write"]

    def test_get_fashion_preferences(self, session_manager, mock_request):
        """Test getting fashion preferences from session."""
        mock_request.state.fashion_preferences = {"style": "modern"}

        result = SessionManager.get_fashion_preferences(mock_request)

        assert result == {"style": "modern"}

    def test_is_authenticated(self, session_manager, mock_request, sample_session_data):
        """Test checking if user is authenticated."""
        mock_request.state.session_data = sample_session_data

        result = SessionManager.is_authenticated(mock_request)

        assert result is True

    def test_is_authenticated_false(self, session_manager, mock_request):
        """Test checking authentication when no session."""
        result = SessionManager.is_authenticated(mock_request)

        assert result is False

    def test_has_permission_true(self, session_manager, mock_request):
        """Test checking permission when user has it."""
        mock_request.state.user_permissions = ["read", "write", "delete"]

        result = SessionManager.has_permission(mock_request, "write")

        assert result is True

    def test_has_permission_false(self, session_manager, mock_request):
        """Test checking permission when user doesn't have it."""
        mock_request.state.user_permissions = ["read"]

        result = SessionManager.has_permission(mock_request, "delete")

        assert result is False

    def test_has_role_true(self, session_manager, mock_request):
        """Test checking role when user has it."""
        mock_request.state.user_role = "admin"

        result = SessionManager.has_role(mock_request, "admin")

        assert result is True

    def test_has_role_false(self, session_manager, mock_request):
        """Test checking role when user doesn't have it."""
        mock_request.state.user_role = "user"

        result = SessionManager.has_role(mock_request, "admin")

        assert result is False

    def test_is_fashion_expert_true(self, session_manager, mock_request):
        """Test checking fashion expert role."""
        mock_request.state.user_role = "fashion_expert"

        result = SessionManager.is_fashion_expert(mock_request)

        assert result is True

    def test_is_fashion_expert_false(self, session_manager, mock_request):
        """Test checking fashion expert when user is not."""
        mock_request.state.user_role = "admin"

        result = SessionManager.is_fashion_expert(mock_request)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_metrics(self, session_manager, mock_redis_manager):
        """Test getting session management metrics."""
        mock_redis_manager.get_metrics = AsyncMock(return_value={"test": "data"})
        mock_redis_manager.cleanup_expired_sessions = AsyncMock(return_value=10)

        metrics = await session_manager.get_session_metrics()

        assert "active_sessions" in metrics
        assert "redis_metrics" in metrics
        assert "session_config" in metrics
        assert "fashion_tracking" in metrics


# ============================================================================
# TEST FastAPI Dependencies
# ============================================================================


class TestFastAPIDependencies:
    """Test FastAPI dependency functions."""

    @pytest.mark.asyncio
    async def test_get_current_session(self, mock_request, sample_session_data):
        """Test get_current_session dependency."""
        mock_request.state.session_data = sample_session_data

        result = await get_current_session(mock_request)

        assert result == sample_session_data

    @pytest.mark.asyncio
    async def test_get_current_session_none(self, mock_request):
        """Test get_current_session with no session."""
        result = await get_current_session(mock_request)

        assert result is None

    @pytest.mark.asyncio
    async def test_require_authentication_success(self, mock_request, sample_session_data):
        """Test require_authentication with valid session."""
        mock_request.state.session_data = sample_session_data

        result = await require_authentication(mock_request)

        assert result == sample_session_data

    @pytest.mark.asyncio
    async def test_require_authentication_failure(self, mock_request):
        """Test require_authentication with no session."""
        with pytest.raises(HTTPException) as exc_info:
            await require_authentication(mock_request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_fashion_expert_success(self, mock_request, sample_session_data):
        """Test require_fashion_expert with fashion expert role."""
        mock_request.state.session_data = sample_session_data
        mock_request.state.user_role = "fashion_expert"

        result = await require_fashion_expert(mock_request)

        assert result == sample_session_data

    @pytest.mark.asyncio
    async def test_require_fashion_expert_wrong_role(self, mock_request, sample_session_data):
        """Test require_fashion_expert with non-expert role."""
        mock_request.state.session_data = sample_session_data
        mock_request.state.user_role = "admin"

        with pytest.raises(HTTPException) as exc_info:
            await require_fashion_expert(mock_request)

        assert exc_info.value.status_code == 403


# ============================================================================
# TEST Response Headers
# ============================================================================


class TestResponseHeaders:
    """Test response header additions."""

    @pytest.mark.asyncio
    async def test_dispatch_adds_performance_header(self, session_middleware, mock_request, mock_redis_manager):
        """Test dispatch adds processing time header."""
        # Mock call_next
        async def call_next(request):
            response = MagicMock()
            response.headers = {}
            return response

        response = await session_middleware.dispatch(mock_request, call_next)

        assert "X-Session-Processing-Time" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_adds_user_headers(self, session_middleware, mock_request, mock_redis_manager, sample_session_data):
        """Test dispatch adds user info headers."""
        mock_request.cookies = {"test_session": "sess123"}
        mock_redis_manager.get_session = AsyncMock(return_value=sample_session_data)

        # Mock call_next
        async def call_next(request):
            response = MagicMock()
            response.headers = {}
            return response

        response = await session_middleware.dispatch(mock_request, call_next)

        assert "X-Session-User" in response.headers
        assert "X-Session-Role" in response.headers
        assert response.headers["X-Session-User"] == "testuser"
        assert response.headers["X-Session-Role"] == "admin"


# ============================================================================
# TEST Global Instances
# ============================================================================


def test_global_session_middleware():
    """Test global session_middleware instance exists."""
    from infrastructure.session_middleware import session_middleware

    assert session_middleware is not None
    assert isinstance(session_middleware, SessionMiddleware)


def test_global_session_manager():
    """Test global session_manager instance exists."""
    from infrastructure.session_middleware import session_manager

    assert session_manager is not None
    assert isinstance(session_manager, SessionManager)
