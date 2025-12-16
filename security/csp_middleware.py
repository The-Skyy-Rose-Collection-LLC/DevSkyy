"""
Content Security Policy (CSP) Middleware with Nonce Support
Provides comprehensive CSP protection with dynamic nonce generation
"""

import logging
import secrets
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Content Security Policy middleware with nonce support for DevSkyy Enterprise Platform.

    Features:
    - Dynamic nonce generation for inline scripts and styles
    - Configurable CSP policies
    - Report-only mode for testing
    - Violation reporting endpoint
    - Environment-specific policies
    """

    def __init__(
        self,
        app: ASGIApp,
        policy: dict[str, list[str]] | None = None,
        report_only: bool = False,
        report_uri: str | None = None,
        nonce_length: int = 32,
        enable_nonce: bool = True,
    ):
        super().__init__(app)
        self.policy = policy or self._get_default_policy()
        self.report_only = report_only
        self.report_uri = report_uri
        self.nonce_length = nonce_length
        self.enable_nonce = enable_nonce

    def _get_default_policy(self) -> dict[str, list[str]]:
        """Get default CSP policy for DevSkyy platform"""
        return {
            "default-src": ["'self'"],
            "script-src": [
                "'self'",
                "'unsafe-inline'",  # Will be replaced with nonce
                "https://cdn.jsdelivr.net",
                "https://unpkg.com",
                "https://cdnjs.cloudflare.com",
            ],
            "style-src": [
                "'self'",
                "'unsafe-inline'",  # Will be replaced with nonce
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net",
            ],
            "img-src": ["'self'", "data:", "https:", "blob:"],
            "font-src": ["'self'", "https://fonts.gstatic.com", "data:"],
            "connect-src": [
                "'self'",
                "https://api.openai.com",
                "https://api.anthropic.com",
                "wss:",
            ],
            "media-src": ["'self'", "data:", "blob:"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": [],
        }

    def _generate_nonce(self) -> str:
        """Generate cryptographically secure nonce"""
        return secrets.token_urlsafe(self.nonce_length)

    def _build_csp_header(self, nonce: str | None = None) -> str:
        """Build CSP header string from policy"""
        policy_parts = []

        for directive, sources in self.policy.items():
            if not sources:
                # Directives without sources (like upgrade-insecure-requests)
                policy_parts.append(directive)
                continue

            # Replace 'unsafe-inline' with nonce for script-src and style-src
            if nonce and self.enable_nonce and directive in ["script-src", "style-src"]:
                sources = [
                    f"'nonce-{nonce}'" if source == "'unsafe-inline'" else source
                    for source in sources
                ]

            sources_str = " ".join(sources)
            policy_parts.append(f"{directive} {sources_str}")

        # Add report-uri if specified
        if self.report_uri:
            policy_parts.append(f"report-uri {self.report_uri}")

        return "; ".join(policy_parts)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add CSP headers"""

        # Generate nonce for this request
        nonce = self._generate_nonce() if self.enable_nonce else None

        # Store nonce in request state for template access
        if nonce:
            request.state.csp_nonce = nonce

        # Process request
        response = await call_next(request)

        # Skip CSP for non-HTML responses
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("text/html"):
            return response

        # Build and add CSP header
        csp_header = self._build_csp_header(nonce)
        header_name = (
            "Content-Security-Policy-Report-Only" if self.report_only else "Content-Security-Policy"
        )

        response.headers[header_name] = csp_header

        # Add additional security headers
        self._add_security_headers(response)

        logger.debug(f"CSP header added: {header_name}: {csp_header}")

        return response

    def _add_security_headers(self, response: Response) -> None:
        """Add additional security headers"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value


class CSPViolationReporter:
    """Handle CSP violation reports"""

    def __init__(self, log_violations: bool = True, store_violations: bool = False):
        self.log_violations = log_violations
        self.store_violations = store_violations
        self.violations: list[dict] = []

    async def handle_violation(self, request: Request) -> dict:
        """Handle CSP violation report"""
        try:
            violation_data = await request.json()

            # Extract violation details
            csp_report = violation_data.get("csp-report", {})
            violation_info = {
                "timestamp": uuid.uuid4().hex,
                "document_uri": csp_report.get("document-uri"),
                "violated_directive": csp_report.get("violated-directive"),
                "blocked_uri": csp_report.get("blocked-uri"),
                "source_file": csp_report.get("source-file"),
                "line_number": csp_report.get("line-number"),
                "column_number": csp_report.get("column-number"),
                "user_agent": request.headers.get("user-agent"),
                "ip_address": request.client.host if request.client else None,
            }

            if self.log_violations:
                logger.warning(f"CSP Violation: {violation_info}")

            if self.store_violations:
                self.violations.append(violation_info)

            return {"status": "received", "violation_id": violation_info["timestamp"]}

        except Exception as e:
            logger.error(f"Error processing CSP violation report: {e}")
            return {"status": "error", "message": str(e)}

    def get_violations(self, limit: int = 100) -> list[dict]:
        """Get stored violations"""
        return self.violations[-limit:]

    def clear_violations(self) -> None:
        """Clear stored violations"""
        self.violations.clear()


# Utility functions for template integration
def get_csp_nonce(request: Request) -> str | None:
    """Get CSP nonce from request state for use in templates"""
    return getattr(request.state, "csp_nonce", None)


def csp_script_tag(request: Request, content: str) -> str:
    """Generate script tag with CSP nonce"""
    nonce = get_csp_nonce(request)
    nonce_attr = f' nonce="{nonce}"' if nonce else ""
    return f"<script{nonce_attr}>{content}</script>"


def csp_style_tag(request: Request, content: str) -> str:
    """Generate style tag with CSP nonce"""
    nonce = get_csp_nonce(request)
    nonce_attr = f' nonce="{nonce}"' if nonce else ""
    return f"<style{nonce_attr}>{content}</style>"


# Environment-specific CSP policies
DEVELOPMENT_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "http://localhost:*"],
    "style-src": ["'self'", "'unsafe-inline'", "http://localhost:*"],
    "img-src": ["'self'", "data:", "http:", "https:"],
    "connect-src": ["'self'", "ws:", "wss:", "http:", "https:"],
    "font-src": ["'self'", "data:", "http:", "https:"],
}

PRODUCTION_POLICY = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://unpkg.com"],
    "style-src": ["'self'", "https://fonts.googleapis.com"],
    "img-src": ["'self'", "data:", "https:"],
    "connect-src": ["'self'", "https://api.openai.com", "https://api.anthropic.com"],
    "font-src": ["'self'", "https://fonts.gstatic.com"],
    "object-src": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
    "frame-ancestors": ["'none'"],
    "upgrade-insecure-requests": [],
}
