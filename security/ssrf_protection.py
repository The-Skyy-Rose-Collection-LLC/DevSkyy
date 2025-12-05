"""
Server-Side Request Forgery (SSRF) Protection

Prevents attackers from making requests to internal network resources
through the application server.

Per OWASP Top 10 2021 - A10: Server-Side Request Forgery (SSRF)
Truth Protocol Rule #7: Input validation and security

Author: DevSkyy Security Team
Date: 2025-12-05
"""

import ipaddress
import logging
from typing import Any
from urllib.parse import urlparse

from fastapi import HTTPException, status


logger = logging.getLogger(__name__)

# ============================================================================
# BLOCKED IP RANGES (Private/Internal Networks)
# ============================================================================

BLOCKED_IP_RANGES = [
    # RFC 1918 - Private IPv4 addresses
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    # Loopback
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    # Link-local
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fe80::/10"),
    # Carrier-grade NAT
    ipaddress.ip_network("100.64.0.0/10"),
    # Documentation and test networks
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    # Multicast
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("ff00::/8"),
    # AWS metadata service (common SSRF target)
    ipaddress.ip_network("169.254.169.254/32"),
    # Google Cloud metadata
    ipaddress.ip_network("169.254.169.254/32"),
    # Azure metadata
    ipaddress.ip_network("169.254.169.254/32"),
]

# ============================================================================
# BLOCKED SCHEMES
# ============================================================================

ALLOWED_SCHEMES = ["http", "https"]
BLOCKED_SCHEMES = ["file", "ftp", "gopher", "dict", "jar", "ldap", "tftp"]

# ============================================================================
# SSRF PROTECTION FUNCTIONS
# ============================================================================


def is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is in private/internal range.

    Args:
        ip_str: IP address string (IPv4 or IPv6)

    Returns:
        True if IP is private/internal, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)

        # Check against blocked ranges
        for blocked_range in BLOCKED_IP_RANGES:
            if ip in blocked_range:
                return True

        # Check if private (RFC 1918)
        if ip.is_private:
            return True

        # Check if loopback
        if ip.is_loopback:
            return True

        # Check if link-local
        if ip.is_link_local:
            return True

        return False

    except ValueError:
        # Invalid IP address
        logger.warning(f"Invalid IP address: {ip_str}")
        return True  # Fail secure - block invalid IPs


def validate_url_scheme(url: str) -> bool:
    """
    Validate URL scheme against allowlist.

    Args:
        url: URL to validate

    Returns:
        True if scheme is allowed, False otherwise
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if not scheme:
            logger.warning(f"URL missing scheme: {url}")
            return False

        if scheme in BLOCKED_SCHEMES:
            logger.warning(f"Blocked URL scheme detected: {scheme}")
            return False

        if scheme not in ALLOWED_SCHEMES:
            logger.warning(f"Unknown URL scheme: {scheme}")
            return False

        return True

    except Exception as e:
        logger.error(f"URL scheme validation error: {e}")
        return False


def validate_url_safe(
    url: str,
    allowed_domains: list[str] | None = None,
    allow_redirects: bool = False,
) -> tuple[bool, str]:
    """
    Comprehensive URL validation against SSRF attacks.

    Args:
        url: URL to validate
        allowed_domains: Optional whitelist of allowed domains
        allow_redirects: Whether to allow URL redirects (default: False)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_url_safe("http://example.com")
        (True, "")

        >>> validate_url_safe("http://192.168.1.1")
        (False, "Private IP address not allowed")

        >>> validate_url_safe("file:///etc/passwd")
        (False, "Blocked URL scheme: file")
    """
    try:
        # Validate scheme
        if not validate_url_scheme(url):
            return False, "Blocked or invalid URL scheme"

        # Parse URL
        parsed = urlparse(url)

        # Check for empty hostname
        if not parsed.hostname:
            return False, "URL must have a hostname"

        # Check domain whitelist if provided
        if allowed_domains:
            if parsed.hostname not in allowed_domains:
                return False, f"Domain not in whitelist: {parsed.hostname}"

        # Resolve hostname to IP and check against private ranges
        try:
            import socket

            # Get IP address(es) for hostname
            ip_addresses = socket.getaddrinfo(
                parsed.hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
            )

            for ip_info in ip_addresses:
                ip_str = ip_info[4][0]

                # Check if private/internal IP
                if is_private_ip(ip_str):
                    logger.warning(
                        f"SSRF attempt blocked: {url} resolves to private IP {ip_str}"
                    )
                    return False, "Private IP address not allowed"

        except socket.gaierror:
            logger.warning(f"Unable to resolve hostname: {parsed.hostname}")
            return False, "Unable to resolve hostname"
        except Exception as e:
            logger.error(f"DNS resolution error: {e}")
            return False, "DNS resolution failed"

        # Check for redirect attempts in URL (basic check)
        if not allow_redirects:
            suspicious_patterns = ["redirect", "url=", "goto=", "return=", "redir="]
            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in url_lower:
                    logger.warning(f"Potential redirect in URL: {url}")
                    return False, "URL redirects not allowed"

        return True, ""

    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False, "URL validation failed"


def validate_webhook_url(url: str) -> None:
    """
    Validate webhook URL and raise HTTPException if invalid.

    Args:
        url: Webhook URL to validate

    Raises:
        HTTPException: If URL is invalid or potentially malicious
    """
    is_valid, error_message = validate_url_safe(url, allow_redirects=False)

    if not is_valid:
        logger.warning(f"Webhook URL validation failed: {error_message} - {url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook URL: {error_message}",
        )


def validate_redirect_url(url: str, allowed_domains: list[str]) -> None:
    """
    Validate redirect URL against domain whitelist.

    Args:
        url: Redirect target URL
        allowed_domains: List of allowed domains

    Raises:
        HTTPException: If URL is invalid or domain not whitelisted
    """
    is_valid, error_message = validate_url_safe(
        url, allowed_domains=allowed_domains, allow_redirects=True
    )

    if not is_valid:
        logger.warning(f"Redirect URL validation failed: {error_message} - {url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid redirect URL: {error_message}",
        )


# ============================================================================
# SSRF-SAFE HTTP CLIENT WRAPPER
# ============================================================================


class SSRFSafeHTTPClient:
    """
    HTTP client with built-in SSRF protection.

    Wraps httpx or requests with automatic URL validation.
    """

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        timeout: int = 10,
        max_redirects: int = 0,
    ):
        """
        Initialize SSRF-safe HTTP client.

        Args:
            allowed_domains: Optional domain whitelist
            timeout: Request timeout in seconds
            max_redirects: Maximum allowed redirects (0 = no redirects)
        """
        self.allowed_domains = allowed_domains
        self.timeout = timeout
        self.max_redirects = max_redirects

    def _validate_url(self, url: str) -> None:
        """Validate URL before making request."""
        is_valid, error_message = validate_url_safe(
            url,
            allowed_domains=self.allowed_domains,
            allow_redirects=self.max_redirects > 0,
        )

        if not is_valid:
            raise ValueError(f"SSRF protection: {error_message}")

    async def get(self, url: str, **kwargs) -> Any:
        """
        Make GET request with SSRF protection.

        Args:
            url: Target URL
            **kwargs: Additional httpx/requests arguments

        Returns:
            Response object
        """
        self._validate_url(url)

        try:
            import httpx

            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=(self.max_redirects > 0),
                max_redirects=self.max_redirects,
            ) as client:
                response = await client.get(url, **kwargs)
                return response

        except ImportError:
            # Fall back to requests (synchronous)
            import requests

            response = requests.get(
                url,
                timeout=self.timeout,
                allow_redirects=(self.max_redirects > 0),
                **kwargs,
            )
            return response

    async def post(self, url: str, **kwargs) -> Any:
        """
        Make POST request with SSRF protection.

        Args:
            url: Target URL
            **kwargs: Additional httpx/requests arguments

        Returns:
            Response object
        """
        self._validate_url(url)

        try:
            import httpx

            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=(self.max_redirects > 0),
                max_redirects=self.max_redirects,
            ) as client:
                response = await client.post(url, **kwargs)
                return response

        except ImportError:
            # Fall back to requests (synchronous)
            import requests

            response = requests.post(
                url,
                timeout=self.timeout,
                allow_redirects=(self.max_redirects > 0),
                **kwargs,
            )
            return response


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Example 1: Validate webhook URL in API endpoint

from security.ssrf_protection import validate_webhook_url

@router.post("/webhooks")
async def create_webhook(url: str):
    # Validate URL for SSRF
    validate_webhook_url(url)

    # Safe to use URL
    ...


Example 2: Validate redirect URL with domain whitelist

from security.ssrf_protection import validate_redirect_url

@router.get("/redirect")
async def redirect_user(target_url: str):
    allowed_domains = ["example.com", "trusted.com"]
    validate_redirect_url(target_url, allowed_domains)

    return RedirectResponse(url=target_url)


Example 3: Use SSRF-safe HTTP client

from security.ssrf_protection import SSRFSafeHTTPClient

client = SSRFSafeHTTPClient(
    allowed_domains=["api.example.com"],
    timeout=10,
    max_redirects=0
)

response = await client.get("https://api.example.com/data")
"""
