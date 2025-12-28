"""
Comprehensive Input Validation & Sanitization
=============================================

Advanced input validation and sanitization for DevSkyy Enterprise Platform:
- SQL injection prevention
- XSS protection
- CSRF protection
- Request size limits
- Content type validation
- File upload security
- Parameter pollution protection
"""

import hashlib
import hmac
import html
import os
import re
import secrets
import time
import urllib.parse
from typing import Any

from fastapi import Request, UploadFile
from pydantic import BaseModel, Field

# Optional bleach import for HTML sanitization
try:
    import bleach

    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    bleach = None


class ValidationRule(BaseModel):
    """Input validation rule"""

    field_name: str
    required: bool = False
    min_length: int = 0
    max_length: int = 1000
    pattern: str | None = None
    allowed_chars: str | None = None
    forbidden_chars: str | None = None
    sanitize_html: bool = True
    allow_html_tags: list[str] = Field(default_factory=list)


class SecurityValidator:
    """
    Comprehensive security validator for all input types.

    Features:
    - SQL injection detection and prevention
    - XSS attack prevention with HTML sanitization
    - CSRF token validation
    - File upload security validation
    - Request size limiting
    - Parameter pollution detection
    - Content type validation
    """

    def __init__(self):
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
            r"(--|#|/\*|\*/)",
            r"(\bxp_cmdshell\b|\bsp_executesql\b)",
            r"(\bINTO\s+OUTFILE\b|\bLOAD_FILE\b)",
            r"(\bSCRIPT\b|\bJAVASCRIPT\b|\bVBSCRIPT\b)",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
        ]

        # Allowed HTML tags for content (very restrictive)
        self.safe_html_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "ol",
            "ul",
            "li",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
        ]

        # Allowed HTML attributes
        self.safe_html_attributes = {
            "*": ["class", "id"],
            "a": ["href", "title"],
            "img": ["src", "alt", "width", "height"],
        }

        # File upload restrictions
        self.allowed_file_extensions = {
            "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
            "document": {".pdf", ".doc", ".docx", ".txt", ".rtf"},
            "archive": {".zip", ".tar", ".gz"},
        }

        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.dangerous_file_extensions = {
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".pif",
            ".scr",
            ".vbs",
            ".js",
            ".jar",
            ".php",
            ".asp",
            ".aspx",
            ".jsp",
            ".py",
            ".rb",
            ".pl",
        }

    def detect_sql_injection(self, input_text: str) -> bool:
        """Detect potential SQL injection attempts"""
        if not input_text:
            return False

        # Convert to lowercase for pattern matching
        text_lower = input_text.lower()

        for pattern in self.sql_injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def detect_xss(self, input_text: str) -> bool:
        """Detect potential XSS attempts"""
        if not input_text:
            return False

        # Convert to lowercase for pattern matching
        text_lower = input_text.lower()

        for pattern in self.xss_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def sanitize_html(self, input_text: str, allowed_tags: list[str] = None) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not input_text:
            return ""

        # Use provided tags or default safe tags
        tags = allowed_tags or self.safe_html_tags

        if BLEACH_AVAILABLE:
            # Clean HTML using bleach
            cleaned = bleach.clean(
                input_text,
                tags=tags,
                attributes=self.safe_html_attributes,
                strip=True,
                strip_comments=True,
            )
        else:
            # Fallback: escape all HTML
            cleaned = html.escape(input_text)

        return cleaned

    def sanitize_sql_input(self, input_text: str) -> str:
        """Sanitize input to prevent SQL injection"""
        if not input_text:
            return ""

        # Remove dangerous SQL characters and keywords
        sanitized = input_text

        # Remove SQL comments
        sanitized = re.sub(r"--.*$", "", sanitized, flags=re.MULTILINE)
        sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.DOTALL)

        # Escape single quotes
        sanitized = sanitized.replace("'", "''")

        # Remove or escape other dangerous characters
        dangerous_chars = [";", "\\", "\x00", "\n", "\r", "\x1a"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False

        # Basic email regex (more comprehensive than simple checks)
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, email):
            return False

        # Additional security checks
        if len(email) > 254:  # RFC 5321 limit
            return False

        # Check for dangerous characters
        dangerous_chars = ["<", ">", '"', "\\", "\x00", "\n", "\r"]
        return not any(char in email for char in dangerous_chars)

    def validate_url(self, url: str, allowed_schemes: set[str] = None) -> bool:
        """Validate URL format and scheme"""
        if not url:
            return False

        allowed_schemes = allowed_schemes or {"http", "https"}

        try:
            parsed = urllib.parse.urlparse(url)

            # Check scheme
            if parsed.scheme.lower() not in allowed_schemes:
                return False

            # Check for dangerous protocols
            dangerous_schemes = {"javascript", "vbscript", "data", "file"}
            if parsed.scheme.lower() in dangerous_schemes:
                return False

            # Basic hostname validation
            return parsed.netloc

        except Exception:
            return False

    def validate_file_upload(self, file: UploadFile, file_type: str = "image") -> dict[str, Any]:
        """Validate uploaded file for security"""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # Check file size
        if hasattr(file, "size") and file.size > self.max_file_size:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"File size exceeds limit of {self.max_file_size} bytes"
            )

        # Check file extension
        if file.filename:
            file_ext = "." + file.filename.split(".")[-1].lower()

            # Check for dangerous extensions
            if file_ext in self.dangerous_file_extensions:
                validation_result["valid"] = False
                validation_result["errors"].append(f"File extension {file_ext} is not allowed")

            # Check against allowed extensions for file type
            allowed_exts = self.allowed_file_extensions.get(file_type, set())
            if allowed_exts and file_ext not in allowed_exts:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"File extension {file_ext} not allowed for {file_type} files"
                )

        # Check content type
        if file.content_type:
            # Basic content type validation
            if file_type == "image" and not file.content_type.startswith("image/"):
                validation_result["warnings"].append(
                    "Content type doesn't match expected image type"
                )
            elif file_type == "document" and not any(
                file.content_type.startswith(ct) for ct in ["application/", "text/"]
            ):
                validation_result["warnings"].append(
                    "Content type doesn't match expected document type"
                )

        return validation_result

    def validate_request_size(self, request: Request, max_size: int = 1024 * 1024) -> bool:
        """Validate request content length"""
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                size = int(content_length)
                return size <= max_size
            except ValueError:
                return False

        return True

    def detect_parameter_pollution(self, params: dict[str, Any]) -> list[str]:
        """Detect HTTP parameter pollution attempts"""
        pollution_indicators = []

        for key, value in params.items():
            # Check for duplicate parameters (if value is a list)
            if isinstance(value, list) and len(value) > 1:
                pollution_indicators.append(f"Multiple values for parameter '{key}'")

            # Check for suspicious parameter names
            if isinstance(key, str):
                suspicious_patterns = [
                    r"__.*__",  # Python special methods
                    r"\.\./",  # Directory traversal
                    r'[<>"\']',  # HTML/script injection
                ]

                for pattern in suspicious_patterns:
                    if re.search(pattern, key):
                        pollution_indicators.append(f"Suspicious parameter name: '{key}'")

        return pollution_indicators

    def validate_json_input(self, data: dict[str, Any], max_depth: int = 10) -> dict[str, Any]:
        """Validate JSON input for security issues"""
        validation_result = {"valid": True, "errors": [], "sanitized_data": {}}

        def validate_recursive(obj: Any, depth: int = 0) -> Any:
            if depth > max_depth:
                validation_result["errors"].append("JSON nesting too deep")
                return None

            if isinstance(obj, dict):
                sanitized_dict = {}
                for key, value in obj.items():
                    # Validate key
                    if not isinstance(key, str) or len(key) > 100:
                        validation_result["errors"].append(f"Invalid key: {key}")
                        continue

                    # Sanitize key
                    clean_key = self.sanitize_html(key, [])

                    # Recursively validate value
                    clean_value = validate_recursive(value, depth + 1)
                    sanitized_dict[clean_key] = clean_value

                return sanitized_dict

            elif isinstance(obj, list):
                if len(obj) > 1000:  # Prevent large arrays
                    validation_result["errors"].append("Array too large")
                    return obj[:1000]

                return [validate_recursive(item, depth + 1) for item in obj]

            elif isinstance(obj, str):
                # Check for malicious content
                if self.detect_sql_injection(obj) or self.detect_xss(obj):
                    validation_result["errors"].append(
                        f"Malicious content detected in: {obj[:50]}..."
                    )
                    return self.sanitize_html(obj, [])

                # Limit string length
                if len(obj) > 10000:
                    validation_result["errors"].append("String too long")
                    return obj[:10000]

                return self.sanitize_html(obj, [])

            else:
                return obj

        validation_result["sanitized_data"] = validate_recursive(data)

        if validation_result["errors"]:
            validation_result["valid"] = False

        return validation_result

    # CSRF secret key - should be set via environment variable in production
    _csrf_secret: str = os.environ.get("CSRF_SECRET_KEY", secrets.token_urlsafe(32))
    _csrf_token_expiry: int = 3600  # 1 hour in seconds

    def generate_csrf_token(self, session_id: str) -> str:
        """
        Generate CSRF token bound to session ID using HMAC.

        Token format: {timestamp}.{hmac_signature}
        The HMAC is computed over session_id + timestamp using the CSRF secret.
        """
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self._csrf_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}.{signature}"

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """
        Validate CSRF token is bound to session and not expired.

        Verifies:
        - Token format is valid
        - Token is not expired (within expiry window)
        - HMAC signature matches for given session_id
        """
        if not token or "." not in token:
            return False

        try:
            parts = token.split(".", 1)
            if len(parts) != 2:
                return False

            timestamp_str, provided_signature = parts
            timestamp = int(timestamp_str)

            # Check expiry
            current_time = int(time.time())
            if current_time - timestamp > self._csrf_token_expiry:
                return False

            # Verify signature using constant-time comparison
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self._csrf_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, provided_signature)
        except (ValueError, TypeError):
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            return "unnamed_file"

        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
            sanitized = name[:250] + ("." + ext if ext else "")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "unnamed_file"

        return sanitized

    def validate_and_sanitize_input(
        self, input_data: Any, rules: list[ValidationRule]
    ) -> dict[str, Any]:
        """Comprehensive input validation and sanitization"""
        result = {"valid": True, "errors": [], "warnings": [], "sanitized_data": {}}

        if isinstance(input_data, dict):
            for rule in rules:
                field_value = input_data.get(rule.field_name)

                # Check required fields
                if rule.required and (field_value is None or field_value == ""):
                    result["valid"] = False
                    result["errors"].append(f"Field '{rule.field_name}' is required")
                    continue

                if field_value is None:
                    continue

                # Convert to string for validation
                str_value = str(field_value)

                # Length validation
                if len(str_value) < rule.min_length:
                    result["valid"] = False
                    result["errors"].append(
                        f"Field '{rule.field_name}' is too short (min: {rule.min_length})"
                    )

                if len(str_value) > rule.max_length:
                    result["valid"] = False
                    result["errors"].append(
                        f"Field '{rule.field_name}' is too long (max: {rule.max_length})"
                    )
                    str_value = str_value[: rule.max_length]

                # Pattern validation
                if rule.pattern and not re.match(rule.pattern, str_value):
                    result["valid"] = False
                    result["errors"].append(
                        f"Field '{rule.field_name}' doesn't match required pattern"
                    )

                # Character validation
                if rule.allowed_chars:
                    if not all(c in rule.allowed_chars for c in str_value):
                        result["valid"] = False
                        result["errors"].append(
                            f"Field '{rule.field_name}' contains invalid characters"
                        )

                if rule.forbidden_chars:
                    if any(c in rule.forbidden_chars for c in str_value):
                        result["valid"] = False
                        result["errors"].append(
                            f"Field '{rule.field_name}' contains forbidden characters"
                        )

                # Security validation
                if self.detect_sql_injection(str_value):
                    result["valid"] = False
                    result["errors"].append(
                        f"Field '{rule.field_name}' contains potential SQL injection"
                    )

                if self.detect_xss(str_value):
                    result["valid"] = False
                    result["errors"].append(f"Field '{rule.field_name}' contains potential XSS")

                # Sanitization
                sanitized_value = str_value
                if rule.sanitize_html:
                    sanitized_value = self.sanitize_html(sanitized_value, rule.allow_html_tags)

                result["sanitized_data"][rule.field_name] = sanitized_value

        return result


# Global instance
security_validator = SecurityValidator()
