"""
Server-Side Request Forgery (SSRF) Protection Module
Prevents malicious requests to internal resources and sensitive endpoints
"""

import ipaddress
import logging
import re
import socket
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class SSRFProtection:
    """
    SSRF Protection for DevSkyy Enterprise Platform.

    Features:
    - IP address validation (blocks private/internal IPs)
    - Domain whitelist/blacklist
    - Port restrictions
    - Protocol validation
    - DNS resolution protection
    - Request timeout enforcement
    """

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        blocked_domains: list[str] | None = None,
        allowed_ports: list[int] | None = None,
        blocked_ports: list[int] | None = None,
        allowed_protocols: list[str] | None = None,
        max_redirects: int = 3,
        timeout: int = 10,
        block_private_ips: bool = True,
        block_localhost: bool = True,
        block_metadata_services: bool = True,
    ):
        self.allowed_domains = set(allowed_domains or [])
        self.blocked_domains = set(blocked_domains or self._get_default_blocked_domains())
        self.allowed_ports = set(allowed_ports or [80, 443])
        self.blocked_ports = set(blocked_ports or self._get_default_blocked_ports())
        self.allowed_protocols = set(allowed_protocols or ["http", "https"])
        self.max_redirects = max_redirects
        self.timeout = timeout
        self.block_private_ips = block_private_ips
        self.block_localhost = block_localhost
        self.block_metadata_services = block_metadata_services

        # Compile regex patterns for performance
        self._private_ip_patterns = self._compile_private_ip_patterns()
        self._metadata_service_patterns = self._compile_metadata_patterns()

    def _get_default_blocked_domains(self) -> list[str]:
        """Get default blocked domains"""
        return [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "metadata.google.internal",
            "169.254.169.254",  # AWS metadata service
            "fd00:ec2::254",  # AWS metadata service IPv6
            "metadata.azure.com",
            "metadata.packet.net",
        ]

    def _get_default_blocked_ports(self) -> list[int]:
        """Get default blocked ports"""
        return [
            22,  # SSH
            23,  # Telnet
            25,  # SMTP
            53,  # DNS
            110,  # POP3
            143,  # IMAP
            993,  # IMAPS
            995,  # POP3S
            1433,  # SQL Server
            3306,  # MySQL
            5432,  # PostgreSQL
            6379,  # Redis
            27017,  # MongoDB
            9200,  # Elasticsearch
            11211,  # Memcached
        ]

    def _compile_private_ip_patterns(self) -> list[re.Pattern]:
        """Compile regex patterns for private IP detection"""
        patterns = [
            r"^127\.",  # 127.0.0.0/8
            r"^10\.",  # 10.0.0.0/8
            r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # 172.16.0.0/12
            r"^192\.168\.",  # 192.168.0.0/16
            r"^169\.254\.",  # 169.254.0.0/16 (link-local)
            r"^::1$",  # IPv6 localhost
            r"^fe80:",  # IPv6 link-local
            r"^fc00:",  # IPv6 unique local
            r"^fd00:",  # IPv6 unique local
        ]
        return [re.compile(pattern) for pattern in patterns]

    def _compile_metadata_patterns(self) -> list[re.Pattern]:
        """Compile regex patterns for metadata service detection"""
        patterns = [
            r"metadata\.google\.internal",
            r"169\.254\.169\.254",
            r"fd00:ec2::254",
            r"metadata\.azure\.com",
            r"metadata\.packet\.net",
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private/internal"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except ValueError:
            # If not a valid IP, check with regex patterns
            for pattern in self._private_ip_patterns:
                if pattern.match(ip):
                    return True
            return False

    def _is_metadata_service(self, host: str) -> bool:
        """Check if host is a cloud metadata service"""
        for pattern in self._metadata_service_patterns:
            if pattern.search(host):
                return True
        return False

    def _resolve_hostname(self, hostname: str) -> list[str]:
        """Resolve hostname to IP addresses"""
        try:
            result = socket.getaddrinfo(hostname, None)
            return [addr[4][0] for addr in result]
        except socket.gaierror as e:
            logger.warning(f"DNS resolution failed for {hostname}: {e}")
            raise ValueError(f"Cannot resolve hostname: {hostname}")

    def validate_url(self, url: str) -> bool:
        """
        Validate URL against SSRF protection rules.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is safe, False otherwise

        Raises:
            ValueError: If URL is malicious or blocked
        """
        try:
            parsed = urlparse(url)

            # Validate protocol
            if parsed.scheme not in self.allowed_protocols:
                raise ValueError(f"Protocol '{parsed.scheme}' not allowed")

            # Extract host and port
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)

            if not host:
                raise ValueError("No hostname found in URL")

            # Check domain whitelist/blacklist
            if self.allowed_domains and host not in self.allowed_domains:
                raise ValueError(f"Domain '{host}' not in allowed list")

            if host in self.blocked_domains:
                raise ValueError(f"Domain '{host}' is blocked")

            # Check port restrictions
            if self.allowed_ports and port not in self.allowed_ports:
                raise ValueError(f"Port {port} not allowed")

            if port in self.blocked_ports:
                raise ValueError(f"Port {port} is blocked")

            # Check for metadata services
            if self.block_metadata_services and self._is_metadata_service(host):
                raise ValueError(f"Access to metadata service '{host}' is blocked")

            # Resolve hostname and check IPs
            try:
                ip_addresses = self._resolve_hostname(host)
            except ValueError:
                # If resolution fails, block the request
                raise ValueError(f"Cannot resolve hostname: {host}")

            for ip in ip_addresses:
                # Check for private/internal IPs
                if self.block_private_ips and self._is_private_ip(ip):
                    raise ValueError(f"Access to private IP '{ip}' is blocked")

                # Check for localhost
                if self.block_localhost and ip in ["127.0.0.1", "::1"]:
                    raise ValueError(f"Access to localhost '{ip}' is blocked")

            logger.debug(f"URL validation passed: {url}")
            return True

        except Exception as e:
            logger.warning(f"URL validation failed for '{url}': {e}")
            raise

    async def safe_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make a safe HTTP request with SSRF protection.

        Args:
            method: HTTP method
            url: Target URL
            **kwargs: Additional arguments for httpx.request

        Returns:
            httpx.Response: HTTP response

        Raises:
            ValueError: If URL is blocked by SSRF protection
            httpx.RequestError: If request fails
        """
        # Validate URL first
        self.validate_url(url)

        # Set safe defaults
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("follow_redirects", True)
        kwargs.setdefault("max_redirects", self.max_redirects)

        # Create custom transport with additional validation
        transport = httpx.HTTPTransport(
            verify=True,  # Always verify SSL certificates
            http2=True,  # Enable HTTP/2 for better performance
        )

        async with httpx.AsyncClient(transport=transport) as client:
            # Add custom redirect handler to validate redirect URLs
            original_build_request = client._build_request

            def safe_build_request(request):
                # Validate redirect URLs
                if hasattr(request, "url"):
                    self.validate_url(str(request.url))
                return original_build_request(request)

            client._build_request = safe_build_request

            try:
                response = await client.request(method, url, **kwargs)
                logger.debug(f"Safe request completed: {method} {url} -> {response.status_code}")
                return response

            except httpx.RequestError as e:
                logger.error(f"Safe request failed: {method} {url} -> {e}")
                raise


# Utility functions
def create_ssrf_protection(environment: str = "production") -> SSRFProtection:
    """Create SSRF protection with environment-specific settings"""

    if environment == "development":
        return SSRFProtection(
            block_private_ips=False,
            block_localhost=False,
            allowed_ports=[80, 443, 3000, 8000, 8080],
            timeout=30,
        )

    elif environment == "testing":
        return SSRFProtection(
            block_private_ips=False,
            block_localhost=False,
            allowed_domains=["httpbin.org", "jsonplaceholder.typicode.com"],
            timeout=5,
        )

    else:  # production
        return SSRFProtection(
            allowed_domains=[
                "api.openai.com",
                "api.anthropic.com",
                "googleapis.com",
                "github.com",
                "api.github.com",
            ],
            block_private_ips=True,
            block_localhost=True,
            block_metadata_services=True,
            timeout=10,
        )


# Global instance for easy access
ssrf_protection = create_ssrf_protection()
