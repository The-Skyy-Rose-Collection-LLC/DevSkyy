"""
Structured Logging with Correlation IDs
========================================

Provides structured logging with request correlation IDs for distributed tracing.

Features:
- Correlation IDs (X-Request-ID) for request tracking
- Structured log output with JSON support
- Context managers for operation tracking
- Automatic context cleanup
- Performance metrics logging

Usage:
    from security.structured_logging import get_logger, set_correlation_id

    logger = get_logger(__name__)
    set_correlation_id(request_id)
    logger.info("request_started", user_id=123, endpoint="/api/v1/users")
"""

from __future__ import annotations

import contextvars
import logging
import secrets
import time
from contextlib import contextmanager
from typing import Any, Optional

# Request correlation ID context variable for async compatibility
_correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)

_user_id: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")

_operation_start: contextvars.ContextVar[float] = contextvars.ContextVar(
    "operation_start", default=0.0
)


def generate_correlation_id() -> str:
    """Generate a cryptographically secure correlation ID."""
    return f"req_{secrets.token_hex(12)}"


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get the correlation ID from the current context."""
    correlation_id = _correlation_id.get()
    if not correlation_id:
        correlation_id = generate_correlation_id()
        _correlation_id.set(correlation_id)
    return correlation_id


def set_user_id(user_id: str) -> None:
    """Set the user ID for the current context."""
    _user_id.set(user_id)


def get_user_id() -> str:
    """Get the user ID from the current context."""
    return _user_id.get()


class StructuredFormatter(logging.Formatter):
    """Structured logging formatter that includes correlation IDs and context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured information."""
        # Add correlation ID and user ID to record
        record.correlation_id = get_correlation_id()
        record.user_id = get_user_id()

        # Add operation timing if available
        operation_start = _operation_start.get()
        if operation_start > 0:
            record.elapsed_ms = int((time.time() - operation_start) * 1000)
        else:
            record.elapsed_ms = 0

        # Use parent formatter
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with structured logging configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Skip if already configured
    if logger.handlers:
        return logger

    # Configure handler with structured formatting
    handler = logging.StreamHandler()
    formatter = StructuredFormatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | %(correlation_id)s | "
            "%(user_id)s | %(name)s:%(lineno)d | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation: str,
    **context: Any,
) -> Any:
    """
    Context manager for logging operation timing and success/failure.

    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context fields to log

    Example:
        with log_operation(logger, "process_payment", order_id="12345"):
            # do work
            pass
    """
    correlation_id = get_correlation_id()
    start_time = time.time()
    _operation_start.set(start_time)

    try:
        logger.info(
            f"operation_started: {operation}",
            **{
                **context,
                "operation": operation,
                "correlation_id": correlation_id,
            },
        )
        yield
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"operation_completed: {operation}",
            **{
                **context,
                "operation": operation,
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms,
                "status": "success",
            },
        )
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"operation_failed: {operation}",
            **{
                **context,
                "operation": operation,
                "correlation_id": correlation_id,
                "elapsed_ms": elapsed_ms,
                "status": "failure",
                "error": str(exc),
                "error_type": type(exc).__name__,
            },
            exc_info=True,
        )
        raise
    finally:
        _operation_start.set(0.0)


@contextmanager
def log_security_event(
    logger: logging.Logger,
    event: str,
    severity: str = "warning",
    **context: Any,
) -> Any:
    """
    Context manager for logging security events.

    Args:
        logger: Logger instance
        event: Security event type
        severity: Event severity (info, warning, error, critical)
        **context: Additional context fields

    Example:
        with log_security_event(logger, "auth_failure", severity="warning", user_id=123):
            # handle auth failure
            pass
    """
    correlation_id = get_correlation_id()
    logger.log(
        getattr(logging, severity.upper(), logging.WARNING),
        f"security_event: {event}",
        **{
            **context,
            "event": event,
            "severity": severity,
            "correlation_id": correlation_id,
        },
    )
    yield


def log_auth_attempt(
    logger: logging.Logger,
    username: str,
    success: bool,
    reason: Optional[str] = None,
    **context: Any,
) -> None:
    """
    Log authentication attempt.

    Args:
        logger: Logger instance
        username: Username or email
        success: Whether authentication succeeded
        reason: Failure reason if unsuccessful
        **context: Additional context
    """
    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"auth_attempt: {'success' if success else 'failure'}",
        **{
            **context,
            "username": username,
            "success": success,
            "reason": reason,
            "correlation_id": get_correlation_id(),
        },
    )


def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    elapsed_ms: int,
    user_id: Optional[str] = None,
    **context: Any,
) -> None:
    """
    Log API request with performance metrics.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        elapsed_ms: Elapsed time in milliseconds
        user_id: User ID if authenticated
        **context: Additional context
    """
    level = logging.INFO if status_code < 400 else logging.WARNING
    logger.log(
        level,
        "api_request",
        **{
            **context,
            "method": method,
            "path": path,
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "user_id": user_id or get_user_id(),
            "correlation_id": get_correlation_id(),
        },
    )
