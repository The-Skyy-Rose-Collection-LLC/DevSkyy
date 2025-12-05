"""
Enhanced Content Security Policy Middleware with Nonce Support

Removes 'unsafe-inline' and 'unsafe-eval' by using cryptographic nonces for inline scripts.
Per OWASP CSP recommendations and Truth Protocol Rule #13.

Author: DevSkyy Security Team
Date: 2025-12-05
"""

import secrets
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CSPNonceMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CSP middleware with nonce-based inline script support.

    This removes the need for 'unsafe-inline' and 'unsafe-eval' by generating
    unique nonces for each request.

    Usage:
        app.add_middleware(CSPNonceMiddleware,
                          allowed_image_domains=["cdn.example.com"],
                          allowed_connect_domains=["api.example.com"])
    """

    def __init__(
        self,
        app,
        allowed_image_domains: list[str] | None = None,
        allowed_connect_domains: list[str] | None = None,
        allowed_font_domains: list[str] | None = None,
        report_uri: str | None = None,
    ):
        """
        Initialize CSP middleware with domain whitelists.

        Args:
            app: FastAPI application
            allowed_image_domains: Whitelist of domains for img-src
            allowed_connect_domains: Whitelist of domains for connect-src
            allowed_font_domains: Whitelist of domains for font-src
            report_uri: CSP violation report endpoint
        """
        super().__init__(app)
        self.allowed_image_domains = allowed_image_domains or []
        self.allowed_connect_domains = allowed_connect_domains or []
        self.allowed_font_domains = allowed_font_domains or []
        self.report_uri = report_uri

    def generate_nonce(self) -> str:
        """Generate cryptographically secure nonce."""
        return secrets.token_urlsafe(16)

    def build_csp_header(self, nonce: str) -> str:
        """
        Build CSP header with nonce.

        Args:
            nonce: Cryptographic nonce for this request

        Returns:
            CSP header string
        """
        # Build image sources
        img_src = "'self' data:"
        if self.allowed_image_domains:
            img_src += " " + " ".join(self.allowed_image_domains)

        # Build connect sources
        connect_src = "'self'"
        if self.allowed_connect_domains:
            connect_src += " " + " ".join(self.allowed_connect_domains)

        # Build font sources
        font_src = "'self' data:"
        if self.allowed_font_domains:
            font_src += " " + " ".join(self.allowed_font_domains)

        # Build CSP directives
        directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",  # Nonce-based, no unsafe-inline
            f"style-src 'self' 'nonce-{nonce}'",   # Nonce-based, no unsafe-inline
            f"img-src {img_src}",
            f"font-src {font_src}",
            f"connect-src {connect_src}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",  # Block plugins
            "media-src 'self'",
            "worker-src 'self'",
            "manifest-src 'self'",
            "frame-src 'none'",  # Block iframes
        ]

        # Add report-uri if configured
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")

        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and inject CSP with nonce.

        Args:
            request: Incoming request
            call_next: Next middleware in chain

        Returns:
            Response with CSP headers
        """
        # Generate unique nonce for this request
        nonce = self.generate_nonce()

        # Store nonce in request state for template rendering
        request.state.csp_nonce = nonce

        # Process request
        response = await call_next(request)

        # Build and add CSP header
        csp_header = self.build_csp_header(nonce)
        response.headers["Content-Security-Policy"] = csp_header

        # Add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
            "magnetometer=(), gyroscope=(), accelerometer=()"
        )

        # Cross-Origin policies
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response


class CSPReportOnlyMiddleware(CSPNonceMiddleware):
    """
    CSP Report-Only mode for testing without blocking.

    Use this to test CSP policies before enforcing them.
    Violations will be reported but not blocked.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Add CSP in report-only mode."""
        nonce = self.generate_nonce()
        request.state.csp_nonce = nonce

        response = await call_next(request)

        # Use Content-Security-Policy-Report-Only instead
        csp_header = self.build_csp_header(nonce)
        response.headers["Content-Security-Policy-Report-Only"] = csp_header

        # Still add other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


# ============================================================================
# TEMPLATE HELPER
# ============================================================================

def get_csp_nonce(request: Request) -> str:
    """
    Get CSP nonce from request state for use in templates.

    Usage in Jinja2 template:
        <script nonce="{{ get_csp_nonce(request) }}">
            // Your inline script
        </script>

    Args:
        request: Current request object

    Returns:
        CSP nonce string
    """
    return getattr(request.state, "csp_nonce", "")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
Example integration in main.py:

from security.csp_nonce_middleware import CSPNonceMiddleware

# Add CSP middleware with domain whitelists
app.add_middleware(
    CSPNonceMiddleware,
    allowed_image_domains=[
        "https://cdn.example.com",
        "https://images.example.com",
    ],
    allowed_connect_domains=[
        "https://api.example.com",
    ],
    report_uri="/api/v1/csp-report",
)

# In templates, use nonce for inline scripts:
# <script nonce="{{ request.state.csp_nonce }}">
#     console.log('Allowed by CSP nonce');
# </script>
"""
