# errors/production_errors.py
"""
Production-Grade Error Handling for DevSkyy Enterprise Platform.

This module implements a comprehensive error hierarchy with:
- Severity classification for alerting
- Error codes for API responses
- Correlation ID support for distributed tracing
- Context preservation for debugging
- Retry guidance for transient failures

Design: Correctness > Elegance > Performance
"""

from __future__ import annotations

import traceback
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum, IntEnum
from functools import wraps
from typing import Any, TypeVar

from pydantic import BaseModel, Field

# Module-level constants
MINIMUM_FIDELITY_SCORE = 95.0  # 95% minimum fidelity threshold for 3D models


class DevSkyErrorSeverity(IntEnum):
    """Error severity levels for alerting and logging."""

    DEBUG = 10  # Development only
    INFO = 20  # Informational, no action needed
    WARNING = 30  # Potential issue, monitor
    ERROR = 40  # Error occurred, needs attention
    CRITICAL = 50  # System failure, immediate action required


class DevSkyErrorCode(str, Enum):
    """Standardized error codes for API responses."""

    # General (1xxx)
    UNKNOWN_ERROR = "DEVSKYY-1000"
    VALIDATION_ERROR = "DEVSKYY-1001"
    CONFIGURATION_ERROR = "DEVSKYY-1002"
    INTERNAL_ERROR = "DEVSKYY-1003"

    # Authentication/Authorization (2xxx)
    AUTHENTICATION_FAILED = "DEVSKYY-2001"
    AUTHORIZATION_DENIED = "DEVSKYY-2002"
    TOKEN_EXPIRED = "DEVSKYY-2003"
    RATE_LIMITED = "DEVSKYY-2004"
    INVALID_API_KEY = "DEVSKYY-2005"

    # External Services (3xxx)
    EXTERNAL_SERVICE_ERROR = "DEVSKYY-3001"
    EXTERNAL_SERVICE_TIMEOUT = "DEVSKYY-3002"
    EXTERNAL_SERVICE_UNAVAILABLE = "DEVSKYY-3003"
    DATABASE_ERROR = "DEVSKYY-3004"
    CACHE_ERROR = "DEVSKYY-3005"

    # Resources (4xxx)
    RESOURCE_NOT_FOUND = "DEVSKYY-4001"
    RESOURCE_CONFLICT = "DEVSKYY-4002"
    RESOURCE_EXHAUSTED = "DEVSKYY-4003"

    # 3D/Imagery (5xxx)
    THREE_D_GENERATION_FAILED = "DEVSKYY-5001"
    IMAGE_PROCESSING_FAILED = "DEVSKYY-5002"
    MODEL_FIDELITY_BELOW_THRESHOLD = "DEVSKYY-5003"
    TEXTURE_GENERATION_FAILED = "DEVSKYY-5004"
    MESH_VALIDATION_FAILED = "DEVSKYY-5005"

    # WordPress/Integration (6xxx)
    WORDPRESS_CONNECTION_FAILED = "DEVSKYY-6001"
    WORDPRESS_API_ERROR = "DEVSKYY-6002"
    WOOCOMMERCE_SYNC_FAILED = "DEVSKYY-6003"
    ELEMENTOR_RENDER_FAILED = "DEVSKYY-6004"

    # MCP/LLM (7xxx)
    MCP_SERVER_ERROR = "DEVSKYY-7001"
    LLM_PROVIDER_ERROR = "DEVSKYY-7002"
    TOOL_EXECUTION_FAILED = "DEVSKYY-7003"
    AGENT_EXECUTION_FAILED = "DEVSKYY-7004"
    ROUND_TABLE_FAILED = "DEVSKYY-7005"

    # Security (8xxx)
    SECURITY_VIOLATION = "DEVSKYY-8001"
    ENCRYPTION_FAILED = "DEVSKYY-8002"
    DECRYPTION_FAILED = "DEVSKYY-8003"
    PII_EXPOSURE_BLOCKED = "DEVSKYY-8004"
    SSRF_BLOCKED = "DEVSKYY-8005"

    # Pipeline (9xxx)
    PIPELINE_FAILED = "DEVSKYY-9001"
    PIPELINE_STEP_FAILED = "DEVSKYY-9002"
    PIPELINE_TIMEOUT = "DEVSKYY-9003"
    SYNC_FAILED = "DEVSKYY-9004"


class DevSkyError(Exception):
    """
    Base exception for all DevSkyy errors.

    All errors carry:
    - Unique correlation ID for tracing
    - Severity level for alerting
    - Error code for API responses
    - Context dict for debugging
    - Timestamp for logging
    - Optional retry guidance
    """

    def __init__(
        self,
        message: str,
        code: DevSkyErrorCode = DevSkyErrorCode.UNKNOWN_ERROR,
        severity: DevSkyErrorSeverity = DevSkyErrorSeverity.ERROR,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
        retryable: bool = False,
        retry_after_seconds: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.severity = severity
        self.context = context or {}
        self.cause = cause
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now(UTC)

        # Capture stack trace if cause provided
        if cause:
            self.context["cause_type"] = type(cause).__name__
            self.context["cause_message"] = str(cause)
            self.context["cause_traceback"] = traceback.format_exception(
                type(cause), cause, cause.__traceback__
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "correlation_id": self.correlation_id,
                "timestamp": self.timestamp.isoformat(),
                "retryable": self.retryable,
                "retry_after_seconds": self.retry_after_seconds,
            }
        }

    def to_log_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for structured logging."""
        return {
            "error_code": self.code.value,
            "error_message": self.message,
            "severity": self.severity.name,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "retryable": self.retryable,
        }

    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message} (correlation_id={self.correlation_id})"


# --- Validation Errors ---


class ValidationError(DevSkyError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["invalid_value"] = str(value)[:100]  # Truncate for safety
        super().__init__(
            message,
            code=DevSkyErrorCode.VALIDATION_ERROR,
            severity=DevSkyErrorSeverity.WARNING,
            context=context,
            **kwargs,
        )


# --- Authentication/Authorization Errors ---


class AuthenticationError(DevSkyError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(
            message,
            code=DevSkyErrorCode.AUTHENTICATION_FAILED,
            severity=DevSkyErrorSeverity.WARNING,
            **kwargs,
        )


class AuthorizationError(DevSkyError):
    """Raised when authorization is denied."""

    def __init__(
        self,
        message: str = "Access denied",
        resource: str | None = None,
        action: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if resource:
            context["resource"] = resource
        if action:
            context["action"] = action
        super().__init__(
            message,
            code=DevSkyErrorCode.AUTHORIZATION_DENIED,
            severity=DevSkyErrorSeverity.WARNING,
            context=context,
            **kwargs,
        )


class RateLimitError(DevSkyError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        service: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if service:
            context["service"] = service
            message = f"Rate limit exceeded for {service}"

        super().__init__(
            message,
            code=DevSkyErrorCode.RATE_LIMITED,
            severity=DevSkyErrorSeverity.WARNING,
            retryable=True,
            retry_after_seconds=retry_after,
            context=context,
            **kwargs,
        )


# --- External Service Errors ---


class ExternalServiceError(DevSkyError):
    """Raised when an external service fails."""

    def __init__(
        self,
        service_name: str,
        message: str | None = None,
        error_message: str | None = None,  # Alias for message
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["service_name"] = service_name
        if status_code:
            context["status_code"] = status_code

        # Support both message and error_message parameters
        msg = message or error_message or f"External service '{service_name}' failed"
        super().__init__(
            msg,
            code=DevSkyErrorCode.EXTERNAL_SERVICE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=5,
            **kwargs,
        )


class DatabaseError(DevSkyError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        super().__init__(
            message,
            code=DevSkyErrorCode.DATABASE_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=1,
            **kwargs,
        )


class ConfigurationError(DevSkyError):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if config_key:
            context["config_key"] = config_key
        super().__init__(
            message,
            code=DevSkyErrorCode.CONFIGURATION_ERROR,
            severity=DevSkyErrorSeverity.CRITICAL,
            context=context,
            **kwargs,
        )


# --- Resource Errors ---


class ResourceNotFoundError(DevSkyError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id

        msg = f"{resource_type} not found"
        if resource_id:
            msg = f"{resource_type} '{resource_id}' not found"

        super().__init__(
            msg,
            code=DevSkyErrorCode.RESOURCE_NOT_FOUND,
            severity=DevSkyErrorSeverity.WARNING,
            context=context,
            **kwargs,
        )


class ResourceConflictError(DevSkyError):
    """Raised when a resource conflict occurs."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if resource_type:
            context["resource_type"] = resource_type
        super().__init__(
            message,
            code=DevSkyErrorCode.RESOURCE_CONFLICT,
            severity=DevSkyErrorSeverity.WARNING,
            context=context,
            **kwargs,
        )


# --- 3D/Imagery Errors ---


class ThreeDGenerationError(DevSkyError):
    """Raised when 3D model generation fails."""

    def __init__(
        self,
        message: str,
        generator: str | None = None,
        model_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if generator:
            context["generator"] = generator
        if model_type:
            context["model_type"] = model_type
        super().__init__(
            message,
            code=DevSkyErrorCode.THREE_D_GENERATION_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=10,
            **kwargs,
        )


class ImageProcessingError(DevSkyError):
    """Raised when image processing fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        super().__init__(
            message,
            code=DevSkyErrorCode.IMAGE_PROCESSING_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            **kwargs,
        )


class ModelFidelityError(DevSkyError):
    """Raised when 3D model fidelity is below threshold."""

    MINIMUM_FIDELITY_THRESHOLD = 95.0  # 95% minimum

    def __init__(
        self,
        actual_fidelity: float,
        required_fidelity: float | None = None,
        **kwargs: Any,
    ) -> None:
        required = required_fidelity or self.MINIMUM_FIDELITY_THRESHOLD
        context = kwargs.pop("context", {})
        context["actual_fidelity"] = actual_fidelity
        context["required_fidelity"] = required
        context["fidelity_gap"] = required - actual_fidelity

        message = (
            f"3D model fidelity {actual_fidelity:.1f}% is below required threshold {required:.1f}%"
        )
        super().__init__(
            message,
            code=DevSkyErrorCode.MODEL_FIDELITY_BELOW_THRESHOLD,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=30,
            **kwargs,
        )


# --- WordPress/Integration Errors ---


class WordPressIntegrationError(DevSkyError):
    """Raised when WordPress integration fails."""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        status_code: int | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if endpoint:
            context["endpoint"] = endpoint
        if status_code:
            context["status_code"] = status_code
        super().__init__(
            message,
            code=DevSkyErrorCode.WORDPRESS_API_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=5,
            **kwargs,
        )


# --- MCP/LLM Errors ---


class MCPServerError(DevSkyError):
    """Raised when MCP server communication fails."""

    def __init__(
        self,
        server_name: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["server_name"] = server_name

        msg = message or f"MCP server '{server_name}' error"
        super().__init__(
            msg,
            code=DevSkyErrorCode.MCP_SERVER_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=5,
            **kwargs,
        )


class LLMProviderError(DevSkyError):
    """Raised when LLM provider fails."""

    def __init__(
        self,
        provider: str,
        message: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["provider"] = provider
        if model:
            context["model"] = model

        msg = message or f"LLM provider '{provider}' error"
        super().__init__(
            msg,
            code=DevSkyErrorCode.LLM_PROVIDER_ERROR,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=10,
            **kwargs,
        )


class ToolExecutionError(DevSkyError):
    """Raised when tool execution fails."""

    def __init__(
        self,
        tool_name: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["tool_name"] = tool_name

        msg = message or f"Tool '{tool_name}' execution failed"
        super().__init__(
            msg,
            code=DevSkyErrorCode.TOOL_EXECUTION_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=5,
            **kwargs,
        )


class AgentExecutionError(DevSkyError):
    """Raised when agent execution fails."""

    def __init__(
        self,
        agent_name: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["agent_name"] = agent_name

        msg = message or f"Agent '{agent_name}' execution failed"
        super().__init__(
            msg,
            code=DevSkyErrorCode.AGENT_EXECUTION_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=10,
            **kwargs,
        )


class PipelineError(DevSkyError):
    """Raised when a pipeline operation fails."""

    def __init__(
        self,
        pipeline_name: str,
        stage: str | None = None,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["pipeline_name"] = pipeline_name
        if stage:
            context["stage"] = stage

        msg = message or f"Pipeline '{pipeline_name}' failed"
        if stage:
            msg += f" at stage '{stage}'"

        super().__init__(
            msg,
            code=DevSkyErrorCode.PIPELINE_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=30,
            **kwargs,
        )


class SyncError(DevSkyError):
    """Raised when a sync operation fails."""

    def __init__(
        self,
        source: str,
        target: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["source"] = source
        context["target"] = target

        msg = message or f"Sync from '{source}' to '{target}' failed"
        super().__init__(
            msg,
            code=DevSkyErrorCode.SYNC_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            retryable=True,
            retry_after_seconds=60,
            **kwargs,
        )


class AssetNotFoundError(ResourceNotFoundError):
    """Raised when a 3D asset or media file is not found."""

    def __init__(
        self,
        asset_id: str,
        asset_type: str = "asset",
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        context["asset_type"] = asset_type

        super().__init__(
            resource_type=asset_type,
            resource_id=asset_id,
            context=context,
            **kwargs,
        )


# Aliases for backwards compatibility
ErrorSeverity = DevSkyErrorSeverity


def create_correlation_id() -> str:
    """Create a unique correlation ID for request tracing."""
    import uuid
    from datetime import UTC, datetime

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"devskyy-{timestamp}-{unique_id}"


def format_error_response(
    error: DevSkyError | Exception,
    include_trace: bool = False,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Format an error into a standardized API response.

    Args:
        error: The error to format
        include_trace: Whether to include stack trace (dev only)
        correlation_id: Optional correlation ID to include

    Returns:
        Formatted error response dict
    """
    if correlation_id is None:
        correlation_id = create_correlation_id()

    if isinstance(error, DevSkyError):
        response = error.to_dict()
        response["correlation_id"] = correlation_id
    else:
        response = {
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(error),
            "correlation_id": correlation_id,
            "retryable": False,
        }

    if include_trace:
        import traceback

        response["trace"] = traceback.format_exc()

    return response


# --- Security Errors ---


class SecurityError(DevSkyError):
    """Raised when a security violation is detected."""

    def __init__(
        self,
        message: str,
        violation_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if violation_type:
            context["violation_type"] = violation_type
        super().__init__(
            message,
            code=DevSkyErrorCode.SECURITY_VIOLATION,
            severity=DevSkyErrorSeverity.CRITICAL,
            context=context,
            **kwargs,
        )


class EncryptionError(DevSkyError):
    """Raised when encryption/decryption fails."""

    def __init__(
        self,
        message: str,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs.pop("context", {})
        if operation:
            context["operation"] = operation
        super().__init__(
            message,
            code=(
                DevSkyErrorCode.ENCRYPTION_FAILED
                if operation == "encrypt"
                else DevSkyErrorCode.DECRYPTION_FAILED
            ),
            severity=DevSkyErrorSeverity.CRITICAL,
            context=context,
            **kwargs,
        )


# --- Utility Functions ---


T = TypeVar("T")


def error_handler(
    default_return: T | None = None,
    retries: int = 0,
    log_errors: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for standardized error handling.

    Args:
        default_return: Value to return on failure (None raises)
        retries: Number of retry attempts for retryable errors
        log_errors: Whether to log errors

    Usage:
        @error_handler(default_return=[], retries=3)
        async def fetch_data():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            attempts = retries + 1

            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except DevSkyError as e:
                    last_error = e
                    if log_errors:
                        import structlog

                        logger = structlog.get_logger()
                        await logger.aerror(
                            "DevSkyy error occurred",
                            **e.to_log_dict(),
                            attempt=attempt + 1,
                            max_attempts=attempts,
                        )
                    if not e.retryable or attempt == attempts - 1:
                        if default_return is not None:
                            return default_return
                        raise
                except Exception as e:
                    last_error = e
                    if log_errors:
                        import structlog

                        logger = structlog.get_logger()
                        await logger.aerror(
                            "Unexpected error occurred",
                            error=str(e),
                            error_type=type(e).__name__,
                            attempt=attempt + 1,
                            max_attempts=attempts,
                        )
                    if default_return is not None:
                        return default_return
                    raise DevSkyError(
                        message=str(e),
                        code=DevSkyErrorCode.INTERNAL_ERROR,
                        severity=DevSkyErrorSeverity.ERROR,
                        cause=e,
                    ) from e

            # Should not reach here, but for type safety
            if default_return is not None:
                return default_return
            raise last_error or DevSkyError("Unknown error")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except DevSkyError as e:
                if log_errors:
                    import structlog

                    logger = structlog.get_logger()
                    logger.error("DevSkyy error occurred", **e.to_log_dict())
                if default_return is not None:
                    return default_return
                raise
            except Exception as e:
                if log_errors:
                    import structlog

                    logger = structlog.get_logger()
                    logger.error(
                        "Unexpected error occurred",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                if default_return is not None:
                    return default_return
                raise DevSkyError(
                    message=str(e),
                    code=DevSkyErrorCode.INTERNAL_ERROR,
                    severity=DevSkyErrorSeverity.ERROR,
                    cause=e,
                ) from e

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper

    return decorator


def classify_error(exception: Exception) -> DevSkyError:
    """Classify a generic exception into a DevSkyError."""
    if isinstance(exception, DevSkyError):
        return exception

    error_type = type(exception).__name__
    message = str(exception)

    # Classify based on exception type
    if "timeout" in error_type.lower() or "timeout" in message.lower():
        return ExternalServiceError(
            "unknown",
            f"Timeout error: {message}",
            cause=exception,
        )

    if "connection" in error_type.lower() or "connection" in message.lower():
        return ExternalServiceError(
            "unknown",
            f"Connection error: {message}",
            cause=exception,
        )

    if "permission" in error_type.lower() or "permission" in message.lower():
        return AuthorizationError(
            f"Permission error: {message}",
            cause=exception,
        )

    if "not found" in message.lower():
        return ResourceNotFoundError(
            "resource",
            cause=exception,
        )

    # Default to internal error
    return DevSkyError(
        message=f"Unexpected error: {message}",
        code=DevSkyErrorCode.INTERNAL_ERROR,
        severity=DevSkyErrorSeverity.ERROR,
        cause=exception,
    )


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    correlation_id: str = Field(..., description="Unique correlation ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    retryable: bool = Field(False, description="Whether the request can be retried")
    retry_after_seconds: int | None = Field(None, description="Seconds to wait before retry")


def create_error_response(
    error: DevSkyError | Exception,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Create a standardized error response dict."""
    if isinstance(error, DevSkyError):
        return error.to_dict()

    # Classify and convert
    classified = classify_error(error)
    if correlation_id:
        classified.correlation_id = correlation_id
    return classified.to_dict()
