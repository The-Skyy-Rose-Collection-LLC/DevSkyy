import html
import logging
import re
from typing import Union

from fastapi import HTTPException, Request, status
from pydantic import BaseModel, Field


"""
Enterprise Input Validation & Sanitization
Protection against SQL injection, XSS, command injection, and other attacks
"""

logger = logging.getLogger(__name__)

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"(\bUNION\b.*\bSELECT\b)",
    r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b)",
    r"(\bINSERT\b.*\bINTO\b.*\bVALUES\b)",
    r"(\bUPDATE\b.*\bSET\b)",
    r"(\bDELETE\b.*\bFROM\b)",
    r"(\bDROP\b.*\bTABLE\b)",
    r"(\bEXEC\b|\bEXECUTE\b)",
    r"(--|\#|\/\*|\*\/)",  # SQL comments
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"onerror\s*=",
    r"onload\s*=",
    r"onclick\s*=",
    r"<iframe[^>]*>",
    r"<embed[^>]*>",
    r"<object[^>]*>",
]

# Command injection patterns
COMMAND_INJECTION_PATTERNS = [
    r"[;&|]\s*(cat|ls|rm|mv|cp|wget|curl|nc|bash|sh|python|perl)",
    r"\$\([^)]+\)",  # Command substitution
    r"`[^`]+`",  # Backtick execution
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.",
    r"%2e%2e",
    r"\.\.\\",
]

# ============================================================================
# SANITIZATION FUNCTIONS
# ============================================================================


class InputSanitizer:
    """Input sanitization utilities"""

    @staticmethod
    def sanitize_sql(value: str) -> str:
        """
        Sanitize SQL input to prevent injection

        Args:
            value: Input value

        Returns:
            Sanitized value

        Raises:
            HTTPException: If malicious pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for SQL injection patterns
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"🚨 SQL injection attempt detected: {value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential SQL injection detected",
                )

        # Escape single quotes
        sanitized = value.replace("'", "''")

        return sanitized

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize HTML to prevent XSS

        Args:
            value: Input value

        Returns:
            Sanitized HTML
        """
        if not isinstance(value, str):
            return value

        # Check for XSS patterns
        for pattern in XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"🚨 XSS attempt detected: {value[:100]}")
                # Remove the malicious content
                value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # HTML escape
        return html.escape(value)

    @staticmethod
    def sanitize_command(value: str) -> str:
        """
        Sanitize command input to prevent command injection

        Args:
            value: Input value

        Returns:
            Sanitized value

        Raises:
            HTTPException: If malicious pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for command injection patterns
        for pattern in COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"🚨 Command injection attempt detected: {value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential command injection detected",
                )

        return value

    @staticmethod
    def sanitize_path(value: str) -> str:
        """
        Sanitize file path to prevent path traversal

        Args:
            value: Path value

        Returns:
            Sanitized path

        Raises:
            HTTPException: If malicious pattern detected
        """
        if not isinstance(value, str):
            return value

        # Check for path traversal patterns
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value):
                logger.warning(f"🚨 Path traversal attempt detected: {value[:100]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid input: potential path traversal detected",
                )

        # Remove dangerous characters
        sanitized = re.sub(r"[^\w\s\-./]", "", value)

        return sanitized


# ============================================================================
# VALIDATION MODELS
# ============================================================================


class EmailValidator(BaseModel):
    """Email validation model"""

    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class URLValidator(BaseModel):
    """URL validation model"""

    url: str = Field(..., pattern=r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$")


class AlphanumericValidator(BaseModel):
    """Alphanumeric validation model"""

    value: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")


# ============================================================================
# INPUT VALIDATION MIDDLEWARE
# ============================================================================


class InputValidationMiddleware:
    """
    Middleware to validate and sanitize all incoming requests
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize validation middleware

        Args:
            strict_mode: If True, reject requests with suspicious patterns
        """
        self.strict_mode = strict_mode
        self.sanitizer = InputSanitizer()

    async def validate_request_data(self, data: Union[dict, list, str]) -> Union[dict, list, str]:
        """
        Recursively validate and sanitize request data

        Args:
            data: Request data (dict, list, or string)

        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            return {key: await self.validate_request_data(value) for key, value in data.items()}

        elif isinstance(data, list):
            return [await self.validate_request_data(item) for item in data]

        elif isinstance(data, str):
            # Apply sanitization
            try:
                # Check for SQL injection
                self.sanitizer.sanitize_sql(data)

                # Check for command injection
                self.sanitizer.sanitize_command(data)

                # Check for path traversal
                if "/" in data or "\\" in data:
                    self.sanitizer.sanitize_path(data)

                return data

            except HTTPException:
                if self.strict_mode:
                    raise
                # In non-strict mode, sanitize instead of rejecting
                return self.sanitizer.sanitize_html(data)

        else:
            return data

    async def __call__(self, request: Request, call_next):
        """Process request through validation"""
        # For POST/PUT requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Get request body
                body = await request.json()

                # Validate
                await self.validate_request_data(body)

            except ValueError:
                # Not JSON, skip validation
                pass
            except HTTPException as e:
                logger.warning(f"🚨 Malicious request blocked: {request.url.path}")
                return e

        # Continue processing
        response = await call_next(request)
        return response


# ============================================================================
# FIELD VALIDATORS
# ============================================================================


class SecureString(str):
    """String type with automatic sanitization"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")

        # Sanitize
        sanitizer = InputSanitizer()
        return sanitizer.sanitize_html(v)


# ============================================================================
# RATE LIMITING VALIDATORS
# ============================================================================


class RateLimitValidator:
    """Validate rate limiting parameters"""

    @staticmethod
    def validate_rate_limit(limit: int, window: int) -> bool:
        """
        Validate rate limit parameters

        Args:
            limit: Number of requests
            window: Time window in seconds

        Returns:
            True if valid

        Raises:
            ValueError: If parameters are invalid
        """
        if limit < 1 or limit > 10000:
            raise ValueError("Rate limit must be between 1 and 10000")

        if window < 1 or window > 3600:
            raise ValueError("Time window must be between 1 and 3600 seconds")

        return True


# ============================================================================
# CONTENT SECURITY
# ============================================================================


class ContentSecurityPolicy:
    """Content Security Policy headers"""

    @staticmethod
    def get_csp_header() -> dict[str, str]:
        """Get CSP header"""
        csp = "; ".join(
            [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
        )

        return {
            "Content-Security-Policy": csp,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        }


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

input_sanitizer = InputSanitizer()
validation_middleware = InputValidationMiddleware(strict_mode=True)
csp = ContentSecurityPolicy()

logger.info("🛡️ Enterprise Input Validation System initialized")
