from datetime import datetime
from enum import Enum
import re
from typing import Any

from pydantic import BaseModel, EmailStr, Field, validator
from pydantic.types import confloat, conint, constr


"""
Enhanced Pydantic Validation Models for DevSkyy Enterprise Platform
Comprehensive input validation, sanitization, and security enforcement
"""

# ============================================================================
# SECURITY VALIDATORS
# ============================================================================


class SecurityLevel(str, Enum):
    """Security level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def validate_no_sql_injection(value: str) -> str:
    """Validate against SQL injection patterns"""
    if not isinstance(value, str):
        return value

    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bOR\s+\d+\s*=\s*\d+)",
        r"(\';|\"\;)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value.upper()):
            raise ValueError(f"Potential SQL injection detected: {pattern}")

    return value


def validate_no_xss(value: str) -> str:
    """Validate against XSS patterns"""
    if not isinstance(value, str):
        return value

    # Common XSS patterns
    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    for pattern in xss_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"Potential XSS detected: {pattern}")

    return value


def sanitize_html_input(value: str) -> str:
    """Sanitize HTML input by removing dangerous tags"""
    if not isinstance(value, str):
        return value

    # Remove dangerous HTML tags
    dangerous_tags = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"<form[^>]*>.*?</form>",
    ]

    for tag_pattern in dangerous_tags:
        value = re.sub(tag_pattern, "", value, flags=re.IGNORECASE | re.DOTALL)

    return value.strip()


# ============================================================================
# ENHANCED USER MODELS
# ============================================================================


class EnhancedRegisterRequest(BaseModel):
    """Enhanced registration request with comprehensive validation"""

    email: EmailStr = Field(..., description="Valid email address")
    username: constr(min_length=3, max_length=50) = Field(..., description="Username (3-50 chars, alphanumeric, _, -)")
    password: constr(min_length=8, max_length=128) = Field(..., description="Password (8-128 chars)")
    role: str = Field(default="api_user", description="User role")
    full_name: constr(max_length=100) | None = Field(None, description="Full name (max 100 chars)")
    company: constr(max_length=100) | None = Field(None, description="Company name (max 100 chars)")

    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase, lowercase, digit, and special char
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @validator("username")
    def validate_username_security(cls, v):
        """Validate username for security"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        return v

    @validator("full_name", "company")
    def validate_text_fields(cls, v):
        """Validate text fields for security"""
        if v:
            v = validate_no_sql_injection(v)
            v = validate_no_xss(v)
            v = sanitize_html_input(v)
        return v


class EnhancedLoginRequest(BaseModel):
    """Enhanced login request with validation"""

    email: EmailStr = Field(..., description="Valid email address")
    password: constr(min_length=1, max_length=128) = Field(..., description="Password")
    remember_me: bool = Field(default=False, description="Remember login")

    @validator("password")
    def validate_password_input(cls, v):
        """Basic password input validation"""
        v = validate_no_sql_injection(v)
        return v


# ============================================================================
# API REQUEST MODELS
# ============================================================================


class AgentExecutionRequest(BaseModel):
    """Enhanced agent execution request"""

    agent_type: constr(min_length=1, max_length=50) = Field(..., description="Agent type identifier")

    task_description: constr(min_length=1, max_length=5000) = Field(
        ..., description="Task description (max 5000 chars)"
    )

    parameters: dict[str, Any] = Field(default_factory=dict, description="Task parameters")

    priority: conint(ge=1, le=10) = Field(default=5, description="Task priority (1-10)")

    timeout_seconds: conint(ge=1, le=3600) = Field(default=300, description="Timeout in seconds (1-3600)")

    security_level: SecurityLevel = Field(
        default=SecurityLevel.MEDIUM, description="Security level for task execution"
    )

    @validator("agent_type")
    def validate_agent_type(cls, v):
        """Validate agent type format"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Agent type can only contain letters, numbers, underscores, and hyphens")
        return v

    @validator("task_description")
    def validate_task_description(cls, v):
        """Validate task description for security"""
        v = validate_no_sql_injection(v)
        v = validate_no_xss(v)
        v = sanitize_html_input(v)
        return v

    @validator("parameters")
    def validate_parameters(cls, v):
        """Validate parameters for security"""
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")

        # Validate string values in parameters
        for value in v.values():
            if isinstance(value, str):
                validate_no_sql_injection(value)
                validate_no_xss(value)

        return v


class MLModelRequest(BaseModel):
    """Enhanced ML model request"""

    model_name: constr(min_length=1, max_length=100) = Field(..., description="Model name")

    version: constr(min_length=1, max_length=20) = Field(default="latest", description="Model version")

    input_data: dict[str, Any] = Field(..., description="Input data for model")

    confidence_threshold: confloat(ge=0.0, le=1.0) = Field(default=0.5, description="Confidence threshold (0.0-1.0)")

    max_results: conint(ge=1, le=100) = Field(default=10, description="Maximum results to return (1-100)")

    @validator("model_name")
    def validate_model_name(cls, v):
        """Validate model name format"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Model name can only contain letters, numbers, underscores, and hyphens")
        return v

    @validator("version")
    def validate_version(cls, v):
        """Validate version format"""
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError("Version can only contain letters, numbers, dots, underscores, and hyphens")
        return v

    @validator("input_data")
    def validate_input_data(cls, v):
        """Validate input data for security"""
        if not isinstance(v, dict):
            raise ValueError("Input data must be a dictionary")

        # Validate string values
        for value in v.values():
            if isinstance(value, str):
                validate_no_sql_injection(value)
                validate_no_xss(value)

        return v


class ContentGenerationRequest(BaseModel):
    """Enhanced content generation request"""

    content_type: constr(min_length=1, max_length=50) = Field(..., description="Content type")

    prompt: constr(min_length=1, max_length=10000) = Field(..., description="Content generation prompt")

    target_audience: constr(max_length=200) | None = Field(None, description="Target audience description")

    tone: constr(max_length=50) | None = Field(None, description="Content tone")

    max_length: conint(ge=1, le=50000) = Field(default=1000, description="Maximum content length")

    include_metadata: bool = Field(default=True, description="Include generation metadata")

    @validator("content_type")
    def validate_content_type(cls, v):
        """Validate content type format"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Content type can only contain letters, numbers, underscores, and hyphens")
        return v

    @validator("prompt", "target_audience", "tone")
    def validate_text_content(cls, v):
        """Validate text content for security"""
        if v:
            v = validate_no_sql_injection(v)
            v = validate_no_xss(v)
            v = sanitize_html_input(v)
        return v


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class ValidationErrorResponse(BaseModel):
    """Validation error response"""

    error: str = "validation_error"
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str | None = None


class SecurityViolationResponse(BaseModel):
    """Security violation response"""

    error: str = "security_violation"
    message: str = "Request blocked due to security policy violation"
    violation_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str | None = None


class EnhancedSuccessResponse(BaseModel):
    """Enhanced success response"""

    success: bool = True
    message: str
    data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str | None = None


# ============================================================================
# GDPR COMPLIANCE MODELS
# ============================================================================


class GDPRDataRequest(BaseModel):
    """Enhanced GDPR data request"""

    request_type: str = Field(..., description="Request type: export, delete, or anonymize")

    user_email: EmailStr = Field(..., description="User email address")

    include_audit_logs: bool = Field(default=False, description="Include audit logs in export")

    include_activity_history: bool = Field(default=False, description="Include activity history")

    anonymize_instead_of_delete: bool = Field(default=False, description="Anonymize data instead of deletion")

    reason: constr(max_length=500) | None = Field(None, description="Reason for request (max 500 chars)")

    @validator("request_type")
    def validate_request_type(cls, v):
        """Validate GDPR request type"""
        valid_types = ["export", "delete", "anonymize"]
        if v not in valid_types:
            raise ValueError(f'Request type must be one of: {", ".join(valid_types)}')
        return v

    @validator("reason")
    def validate_reason(cls, v):
        """Validate reason field"""
        if v:
            v = validate_no_sql_injection(v)
            v = validate_no_xss(v)
            v = sanitize_html_input(v)
        return v
