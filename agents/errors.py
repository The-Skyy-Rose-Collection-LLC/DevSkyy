"""
Agent Error Handling
====================

Standardized error handling for all DevSkyy agents.

Provides:
- Exception hierarchy for agent errors
- Error context preservation
- Retry recommendations
- User-friendly error messages
"""

from __future__ import annotations

from enum import Enum
from typing import Any

# =============================================================================
# Error Categories
# =============================================================================


class ErrorCategory(str, Enum):
    """Categories of agent errors for handling."""

    CONFIGURATION = "configuration"  # Missing/invalid config
    AUTHENTICATION = "authentication"  # API key/auth issues
    VALIDATION = "validation"  # Input/output validation
    EXECUTION = "execution"  # Tool execution failures
    TIMEOUT = "timeout"  # Operation timeouts
    RESOURCE = "resource"  # Resource limits (quota, disk, memory)
    NETWORK = "network"  # Network/connectivity issues
    DEPENDENCY = "dependency"  # Missing dependencies
    DATA = "data"  # Data format/integrity issues
    PERMISSION = "permission"  # Permission/access issues
    UNKNOWN = "unknown"  # Unexpected errors


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""

    LOW = "low"  # Warnings, non-critical
    MEDIUM = "medium"  # Degraded functionality
    HIGH = "high"  # Operation failed but recoverable
    CRITICAL = "critical"  # System-level failure


# =============================================================================
# Base Agent Exception
# =============================================================================


class AgentError(Exception):
    """
    Base exception for all agent errors.

    Provides:
    - Error categorization
    - Severity levels
    - Retry recommendations
    - User-friendly messages
    - Context preservation
    """

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retryable: bool = False,
        retry_after_seconds: float | None = None,
        user_message: str | None = None,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds
        self.user_message = user_message or message
        self.context = context or {}
        self.original_error = original_error

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "user_message": self.user_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "retry_after_seconds": self.retry_after_seconds,
            "context": self.context,
            "original_error": str(self.original_error) if self.original_error else None,
        }

    def __str__(self) -> str:
        return self.user_message


# =============================================================================
# Specific Error Types
# =============================================================================


class ConfigurationError(AgentError):
    """Configuration or setup error."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if config_key:
            context["config_key"] = config_key

        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            context=context,
            **kwargs,
        )


class AuthenticationError(AgentError):
    """Authentication or authorization error."""

    def __init__(
        self,
        message: str,
        service: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if service:
            context["service"] = service

        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            context=context,
            **kwargs,
        )


class ValidationError(AgentError):
    """Input or output validation error."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if field:
            context["field"] = field
        if value is not None:
            context["value"] = str(value)[:100]  # Truncate for safety

        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            context=context,
            **kwargs,
        )


class ExecutionError(AgentError):
    """Tool or step execution error."""

    def __init__(
        self,
        message: str,
        tool_name: str | None = None,
        step_id: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if tool_name:
            context["tool_name"] = tool_name
        if step_id:
            context["step_id"] = step_id

        super().__init__(
            message=message,
            category=ErrorCategory.EXECUTION,
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Execution errors are often retryable
            context=context,
            **kwargs,
        )


class TimeoutError(AgentError):
    """Operation timeout error."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if timeout_seconds:
            context["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after_seconds=5.0,  # Wait before retry
            context=context,
            **kwargs,
        )


class ResourceError(AgentError):
    """Resource limit or quota error."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        limit: Any = None,
        current: Any = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if resource_type:
            context["resource_type"] = resource_type
        if limit is not None:
            context["limit"] = limit
        if current is not None:
            context["current"] = current

        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            retryable=True,
            retry_after_seconds=60.0,  # Wait for quota reset
            context=context,
            **kwargs,
        )


class NetworkError(AgentError):
    """Network or connectivity error."""

    def __init__(
        self,
        message: str,
        service: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if service:
            context["service"] = service

        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            retry_after_seconds=2.0,
            context=context,
            **kwargs,
        )


class DependencyError(AgentError):
    """Missing dependency error."""

    def __init__(
        self,
        message: str,
        dependency: str | None = None,
        install_command: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if dependency:
            context["dependency"] = dependency
        if install_command:
            context["install_command"] = install_command

        super().__init__(
            message=message,
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.CRITICAL,
            retryable=False,
            context=context,
            **kwargs,
        )


class DataError(AgentError):
    """Data format or integrity error."""

    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        expected_format: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if data_type:
            context["data_type"] = data_type
        if expected_format:
            context["expected_format"] = expected_format

        super().__init__(
            message=message,
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            context=context,
            **kwargs,
        )


class PermissionError(AgentError):
    """Permission or access error."""

    def __init__(
        self,
        message: str,
        resource: str | None = None,
        required_permission: str | None = None,
        **kwargs: Any,
    ):
        context = kwargs.pop("context", {})
        if resource:
            context["resource"] = resource
        if required_permission:
            context["required_permission"] = required_permission

        super().__init__(
            message=message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            retryable=False,
            context=context,
            **kwargs,
        )


# =============================================================================
# Error Classification Helpers
# =============================================================================


def classify_exception(exc: Exception) -> ErrorCategory:
    """
    Classify a generic exception into an error category.

    Useful for wrapping third-party exceptions.
    """
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__.lower()

    # Check for known error types
    if isinstance(exc, AgentError):
        return exc.category

    # Network errors
    if any(
        keyword in exc_str or keyword in exc_type
        for keyword in ["connection", "network", "timeout", "unreachable"]
    ):
        return ErrorCategory.NETWORK

    # Authentication errors
    if any(
        keyword in exc_str or keyword in exc_type
        for keyword in ["auth", "unauthorized", "forbidden", "credential", "token"]
    ):
        return ErrorCategory.AUTHENTICATION

    # Permission errors
    if any(
        keyword in exc_str or keyword in exc_type for keyword in ["permission", "access denied"]
    ):
        return ErrorCategory.PERMISSION

    # Resource errors
    if any(
        keyword in exc_str or keyword in exc_type
        for keyword in ["quota", "limit", "rate limit", "too many requests"]
    ):
        return ErrorCategory.RESOURCE

    # Validation errors
    if any(
        keyword in exc_str or keyword in exc_type
        for keyword in ["validation", "invalid", "malformed", "schema"]
    ):
        return ErrorCategory.VALIDATION

    # Configuration errors
    if any(keyword in exc_str or keyword in exc_type for keyword in ["config", "not found"]):
        return ErrorCategory.CONFIGURATION

    # Data errors
    if any(keyword in exc_str or keyword in exc_type for keyword in ["parse", "format", "corrupt"]):
        return ErrorCategory.DATA

    return ErrorCategory.UNKNOWN


def wrap_exception(
    exc: Exception,
    message: str | None = None,
    retryable: bool | None = None,
) -> AgentError:
    """
    Wrap a generic exception in an AgentError.

    Automatically classifies the error and preserves context.
    """
    category = classify_exception(exc)

    # Determine if retryable (if not specified)
    if retryable is None:
        retryable = category in {
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.EXECUTION,
            ErrorCategory.RESOURCE,
        }

    # Use provided message or original
    error_message = message or str(exc)

    # Create appropriate error type
    if category == ErrorCategory.AUTHENTICATION:
        return AuthenticationError(
            error_message,
            original_error=exc,
            retryable=retryable,
        )
    elif category == ErrorCategory.VALIDATION:
        return ValidationError(
            error_message,
            original_error=exc,
            retryable=retryable,
        )
    elif category == ErrorCategory.NETWORK:
        return NetworkError(
            error_message,
            original_error=exc,
            retryable=retryable,
        )
    elif category == ErrorCategory.RESOURCE:
        return ResourceError(
            error_message,
            original_error=exc,
            retryable=retryable,
        )
    elif category == ErrorCategory.PERMISSION:
        return PermissionError(
            error_message,
            original_error=exc,
            retryable=retryable,
        )
    else:
        return AgentError(
            error_message,
            category=category,
            original_error=exc,
            retryable=retryable,
        )


__all__ = [
    "AgentError",
    "ConfigurationError",
    "AuthenticationError",
    "ValidationError",
    "ExecutionError",
    "TimeoutError",
    "ResourceError",
    "NetworkError",
    "DependencyError",
    "DataError",
    "PermissionError",
    "ErrorCategory",
    "ErrorSeverity",
    "classify_exception",
    "wrap_exception",
]
