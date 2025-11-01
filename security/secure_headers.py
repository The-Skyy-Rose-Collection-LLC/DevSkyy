from typing import Dict

"""
Enhanced Security Headers for Grade A+ Security
Implements comprehensive security headers for production deployment
"""


class SecurityHeaders:
    """
    Enhanced security headers for enterprise-grade protection
    Implements OWASP recommendations and industry best practices
    """

    @staticmethod
    def get_all_headers() -> Dict[str, str]:
        """
        Get comprehensive security headers

        Returns:
            Dictionary of security headers
        """
        return {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # XSS Protection (legacy browsers)
            "X-XSS-Protection": "1; mode=block",
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Permissions Policy (formerly Feature Policy)
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            # Server identification (hide server details)
            "Server": "DevSkyy/5.1",
            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    @staticmethod
    def get_api_headers() -> Dict[str, str]:
        """
        Get security headers specifically for API endpoints

        Returns:
            Dictionary of API-specific security headers
        """
        return {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "no-referrer",
            "Cache-Control": "no-store, max-age=0",
            "Pragma": "no-cache",
        }


# Global instance
security_headers_manager = SecurityHeaders()
