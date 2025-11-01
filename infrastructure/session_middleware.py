from datetime import datetime
from infrastructure.redis_manager import redis_manager, SessionData
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import secrets
import time

from fastapi import HTTPException, Request, Response, status

from typing import Any, Dict, Optional
import logging
import uuid

"""
Enterprise Session Middleware - FastAPI Integration
Implements secure session management with Redis backend and fashion industry features
"""

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Enterprise session middleware with Redis backend"""

    def __init__(
        self,
        app,
        session_cookie_name: str = "devskyy_session",
        session_cookie_max_age: int = 86400,  # 24 hours
        session_cookie_secure: bool = True,
        session_cookie_httponly: bool = True,
        session_cookie_samesite: str = "lax",
        require_session_for_paths: list = None,
    ):
        super().__init__(app)
        self.session_cookie_name = session_cookie_name
        self.session_cookie_max_age = session_cookie_max_age
        self.session_cookie_secure = session_cookie_secure
        self.session_cookie_httponly = session_cookie_httponly
        self.session_cookie_samesite = session_cookie_samesite
        self.require_session_for_paths = require_session_for_paths or [
            "/api/v1/agents/",
            "/api/v1/ml/",
            "/api/v1/analytics/",
            "/api/v1/fashion/",
        ]

        # Fashion industry specific session tracking
        self.fashion_tracking_enabled = True

        logger.info("Session middleware initialized with Redis backend")

    async def dispatch(self, request: Request, call_next):
        """Process request with session management"""
        start_time = time.time()

        # Get session ID from cookie
        session_id = request.cookies.get(self.session_cookie_name)
        session_data = None

        # Load existing session
        if session_id:
            session_data = await redis_manager.get_session(session_id)

            if session_data:
                # Update last accessed time
                await redis_manager.update_session_access(session_id)

                # Add session data to request state
                request.state.session_id = session_id
                request.state.session_data = session_data
                request.state.user_id = session_data.user_id
                request.state.user_role = session_data.role
                request.state.user_permissions = session_data.permissions

                # Fashion industry specific data
                if self.fashion_tracking_enabled and session_data.fashion_preferences:
                    request.state.fashion_preferences = session_data.fashion_preferences

                logger.debug(f"Session loaded: {session_id} for user {session_data.user_id}")
            else:
                # Invalid session ID
                logger.warning(f"Invalid session ID: {session_id}")
                request.state.session_id = None
                request.state.session_data = None
        else:
            # No session cookie
            request.state.session_id = None
            request.state.session_data = None

        # Check if session is required for this path
        path = request.url.path
        requires_session = any(path.startswith(protected_path) for protected_path in self.require_session_for_paths)

        if requires_session and not session_data:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "session_required",
                    "message": "Valid session required for this endpoint",
                    "path": path,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        # Process request
        response = await call_next(request)

        # Add session performance metrics to response headers
        processing_time = (time.time() - start_time) * 1000
        response.headers["X-Session-Processing-Time"] = f"{processing_time:.2f}ms"

        if session_data:
            response.headers["X-Session-User"] = session_data.username
            response.headers["X-Session-Role"] = session_data.role

        return response

    async def create_session(
        self,
        response: Response,
        user_id: str,
        username: str,
        email: str,
        role: str,
        permissions: list,
        ip_address: str,
        user_agent: str,
        fashion_preferences: Dict[str, Any] = None,
    ) -> str:
        """Create new session and set cookie"""

        # Generate secure session ID
        session_id = f"sess_{uuid.uuid4().hex}_{secrets.token_urlsafe(16)}"

        # Create session data
        session_data = SessionData(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            fashion_preferences=fashion_preferences or {},
        )

        # Store session in Redis
        success = await redis_manager.create_session(session_id, session_data)

        if success:
            # Set secure session cookie
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_id,
                max_age=self.session_cookie_max_age,
                secure=self.session_cookie_secure,
                httponly=self.session_cookie_httponly,
                samesite=self.session_cookie_samesite,
            )

            logger.info(f"Session created: {session_id} for user {username}")
            return session_id
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session",
            )

    async def destroy_session(self, request: Request, response: Response) -> bool:
        """Destroy session and clear cookie"""
        session_id = getattr(request.state, "session_id", None)

        if session_id:
            # Delete session from Redis
            success = await redis_manager.delete_session(session_id)

            # Clear cookie
            response.delete_cookie(
                key=self.session_cookie_name,
                secure=self.session_cookie_secure,
                httponly=self.session_cookie_httponly,
                samesite=self.session_cookie_samesite,
            )

            logger.info(f"Session destroyed: {session_id}")
            return success

        return False

    async def update_fashion_preferences(self, request: Request, fashion_preferences: Dict[str, Any]) -> bool:
        """Update fashion preferences in session"""
        session_id = getattr(request.state, "session_id", None)
        session_data = getattr(request.state, "session_data", None)

        if session_id and session_data:
            # Update fashion preferences
            session_data.fashion_preferences = fashion_preferences
            session_data.last_accessed = datetime.now()

            # Save updated session
            success = await redis_manager.create_session(session_id, session_data)

            if success:
                # Update request state
                request.state.fashion_preferences = fashion_preferences
                logger.debug(f"Fashion preferences updated for session {session_id}")

            return success

        return False


class SessionManager:
    """Session management utilities"""

    def __init__(self, middleware: SessionMiddleware):
        self.middleware = middleware

    @staticmethod
    def get_session_data(request: Request) -> Optional[SessionData]:
        """Get session data from request"""
        return getattr(request.state, "session_data", None)

    @staticmethod
    def get_user_id(request: Request) -> Optional[str]:
        """Get user ID from session"""
        return getattr(request.state, "user_id", None)

    @staticmethod
    def get_user_role(request: Request) -> Optional[str]:
        """Get user role from session"""
        return getattr(request.state, "user_role", None)

    @staticmethod
    def get_user_permissions(request: Request) -> list:
        """Get user permissions from session"""
        return getattr(request.state, "user_permissions", [])

    @staticmethod
    def get_fashion_preferences(request: Request) -> Dict[str, Any]:
        """Get fashion preferences from session"""
        return getattr(request.state, "fashion_preferences", {})

    @staticmethod
    def is_authenticated(request: Request) -> bool:
        """Check if user is authenticated"""
        return getattr(request.state, "session_data", None) is not None

    @staticmethod
    def has_permission(request: Request, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = getattr(request.state, "user_permissions", [])
        return permission in permissions

    @staticmethod
    def has_role(request: Request, role: str) -> bool:
        """Check if user has specific role"""
        user_role = getattr(request.state, "user_role", None)
        return user_role == role

    @staticmethod
    def is_fashion_expert(request: Request) -> bool:
        """Check if user is a fashion industry expert"""
        user_role = getattr(request.state, "user_role", None)
        fashion_roles = ["fashion_expert", "trend_analyst", "buyer", "merchandiser"]
        return user_role in fashion_roles

    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session management metrics"""
        redis_metrics = await redis_manager.get_metrics()
        active_sessions = await redis_manager.cleanup_expired_sessions()

        return {
            "active_sessions": active_sessions,
            "redis_metrics": redis_metrics,
            "session_config": {
                "cookie_name": self.middleware.session_cookie_name,
                "max_age": self.middleware.session_cookie_max_age,
                "secure": self.middleware.session_cookie_secure,
                "httponly": self.middleware.session_cookie_httponly,
                "samesite": self.middleware.session_cookie_samesite,
            },
            "fashion_tracking": self.middleware.fashion_tracking_enabled,
        }


# Dependency for FastAPI routes
async def get_current_session(request: Request) -> Optional[SessionData]:
    """FastAPI dependency to get current session"""
    return SessionManager.get_session_data(request)


async def require_authentication(request: Request) -> SessionData:
    """FastAPI dependency that requires authentication"""
    session_data = SessionManager.get_session_data(request)

    if not session_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    return session_data


async def require_fashion_expert(request: Request) -> SessionData:
    """FastAPI dependency that requires fashion expert role"""
    session_data = await require_authentication(request)

    if not SessionManager.is_fashion_expert(request):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fashion expert role required")

    return session_data


# Global session manager instance
session_middleware = SessionMiddleware(None)  # App will be set during initialization
session_manager = SessionManager(session_middleware)
