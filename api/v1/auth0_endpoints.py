from datetime import timedelta
import json
import logging
import os
from typing import Any

from authlib.common.security import generate_token
from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from security.auth0_integration import (
    auth0_oauth_client,
    create_devskyy_jwt_token,
    create_devskyy_refresh_token,
    log_auth_event,
    verify_devskyy_jwt_token,
)


"""
Auth0 Authentication Endpoints for DevSkyy FastAPI Platform
Converted from Flask to FastAPI with JWT token integration
"""

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth0", tags=["auth0-authentication"])

# Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class Auth0LoginResponse(BaseModel):
    """Auth0 login response model."""

    authorization_url: str
    state: str


class Auth0TokenResponse(BaseModel):
    """Auth0 token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict[str, Any]


class Auth0LogoutResponse(BaseModel):
    """Auth0 logout response model."""

    logout_url: str
    message: str


# ============================================================================
# AUTH0 AUTHENTICATION ENDPOINTS
# ============================================================================


@router.get("/login", response_model=Auth0LoginResponse)
async def auth0_login(
    request: Request, redirect_uri: str | None = Query(None, description="Custom redirect URI after login")
):
    """
    Initiate Auth0 login flow.

    This endpoint generates an Auth0 authorization URL and redirects the user
    to Auth0 for authentication. Compatible with the original Flask implementation.
    """
    try:
        # Generate state for CSRF protection
        state = generate_token(32)

        # Determine redirect URI
        if not redirect_uri:
            redirect_uri = f"{API_BASE_URL}/api/v1/auth0/callback"

        # Generate authorization URL
        authorization_url = auth0_oauth_client.get_authorization_url(redirect_uri=redirect_uri, state=state)

        # Log authentication attempt
        await log_auth_event(
            event_type="auth0_login_initiated", request=request, details={"redirect_uri": redirect_uri, "state": state}
        )

        # For API usage, return the URL
        if request.headers.get("accept") == "application/json":
            return Auth0LoginResponse(authorization_url=authorization_url, state=state)

        # For browser usage, redirect directly
        return RedirectResponse(url=authorization_url, status_code=302)

    except Exception as e:
        logger.error(f"Auth0 login initiation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate Auth0 login")


@router.get("/callback", response_model=Auth0TokenResponse)
@router.post("/callback", response_model=Auth0TokenResponse)
async def auth0_callback(
    request: Request,
    code: str | None = Query(None, description="Authorization code from Auth0"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    error: str | None = Query(None, description="Error from Auth0"),
    error_description: str | None = Query(None, description="Error description from Auth0"),
):
    """
    Handle Auth0 callback and exchange code for tokens.

    This endpoint handles the Auth0 callback, exchanges the authorization code
    for tokens, and creates DevSkyy JWT tokens for seamless integration.
    """
    try:
        # Check for Auth0 errors
        if error:
            await log_auth_event(
                event_type="auth0_callback_error",
                request=request,
                details={"error": error, "error_description": error_description},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Auth0 authentication failed: {error_description or error}",
            )

        # Validate required parameters
        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authorization code is required")

        # Exchange code for tokens
        redirect_uri = f"{API_BASE_URL}/api/v1/auth0/callback"
        token_data = await auth0_oauth_client.exchange_code_for_token(code=code, redirect_uri=redirect_uri)

        # Get user information from Auth0
        user_info = await auth0_oauth_client.get_user_info(token_data["access_token"])

        # Create DevSkyy JWT tokens for compatibility
        access_token = create_devskyy_jwt_token(user_data=user_info, expires_delta=timedelta(minutes=30))

        refresh_token = create_devskyy_refresh_token(user_data=user_info)

        # Log successful authentication
        await log_auth_event(
            event_type="auth0_login_success",
            user_id=user_info.get("sub"),
            request=request,
            details={"email": user_info.get("email"), "name": user_info.get("name")},
        )

        # Prepare response
        response_data = Auth0TokenResponse(
            access_token=access_token, refresh_token=refresh_token, expires_in=1800, user_info=user_info  # 30 minutes
        )

        # For browser usage, redirect to frontend with tokens
        if request.headers.get("accept") != "application/json":
            frontend_redirect = f"{FRONTEND_URL}/auth/callback?token={access_token}&refresh={refresh_token}"
            return RedirectResponse(url=frontend_redirect, status_code=302)

        # For API usage, return JSON response
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth0 callback processing failed: {e}")
        await log_auth_event(event_type="auth0_callback_error", request=request, details={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process Auth0 callback"
        )


@router.post("/logout", response_model=Auth0LogoutResponse)
@router.get("/logout", response_model=Auth0LogoutResponse)
async def auth0_logout(
    request: Request, return_to: str | None = Query(None, description="URL to return to after logout")
):
    """
    Handle Auth0 logout.

    This endpoint clears the user session and redirects to Auth0 logout
    to ensure complete logout from Auth0 as well.
    """
    try:
        # Determine return URL
        if not return_to:
            return_to = FRONTEND_URL

        # Generate Auth0 logout URL
        logout_url = auth0_oauth_client.get_logout_url(return_to=return_to)

        # Log logout event
        await log_auth_event(event_type="auth0_logout", request=request, details={"return_to": return_to})

        # For API usage, return the logout URL
        if request.headers.get("accept") == "application/json":
            return Auth0LogoutResponse(
                logout_url=logout_url,
                message="Logout successful. Please visit the logout_url to complete Auth0 logout.",
            )

        # For browser usage, redirect to Auth0 logout
        return RedirectResponse(url=logout_url, status_code=302)

    except Exception as e:
        logger.error(f"Auth0 logout failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process logout")


# ============================================================================
# USER INFO ENDPOINT
# ============================================================================


@router.get("/me")
async def get_current_auth0_user(request: Request):
    """
    Get current user information from DevSkyy JWT token.

    This endpoint verifies the DevSkyy JWT token and returns user information,
    maintaining compatibility with the existing authentication system.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required")

        token = auth_header.replace("Bearer ", "")

        # Verify DevSkyy JWT token
        payload = verify_devskyy_jwt_token(token)

        # Return user information
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "email_verified": payload.get("email_verified"),
            "auth_provider": payload.get("auth_provider"),
            "token_type": payload.get("token_type"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user information")


# ============================================================================
# DEMO HOME PAGE (Optional - for testing)
# ============================================================================


@router.get("/demo", response_class=HTMLResponse)
async def auth0_demo_home(request: Request):
    """
    Demo home page for testing Auth0 integration.
    Adapted from the original Flask HTML template.
    """
    # Check if user is authenticated
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    user_info = None
    if token:
        try:
            payload = verify_devskyy_jwt_token(token)
            user_info = {
                "name": payload.get("name", "Unknown User"),
                "email": payload.get("email"),
                "picture": payload.get("picture"),
                "userinfo": payload,  # For compatibility with original template
            }
        except Exception as e:
            logger.warning(f"Handled exception: {e}")

    # HTML template adapted from Flask version
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8" />
        <title>DevSkyy Auth0 Integration Demo</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .user-info {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .button {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }}
            .logout-button {{ background: #e53e3e; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦄 DevSkyy Auth0 Integration Demo</h1>

            {f'''
            <div class="user-info">
                <h2>Welcome {user_info["name"]}!</h2>
                <p><strong>Email:</strong> {user_info.get("email", "N/A")}</p>
                <p><a href="/api/v1/auth0/logout" class="button logout-button">Logout</a></p>
                <h3>User Information:</h3>
                <pre>{json.dumps(user_info["userinfo"], indent=2)}</pre>
            </div>
            ''' if user_info else '''
            <div class="user-info">
                <h2>Welcome Guest</h2>
                <p>Please log in to access your account.</p>
                <p><a href="/api/v1/auth0/login" class="button">Login with Auth0</a></p>
            </div>
            '''}

            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee;">
                <h3>API Endpoints:</h3>
                <ul>
                    <li><code>GET /api/v1/auth0/login</code> - Initiate Auth0 login</li>
                    <li><code>GET /api/v1/auth0/callback</code> - Handle Auth0 callback</li>
                    <li><code>GET /api/v1/auth0/logout</code> - Logout from Auth0</li>
                    <li><code>GET /api/v1/auth0/me</code> - Get current user info</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)
