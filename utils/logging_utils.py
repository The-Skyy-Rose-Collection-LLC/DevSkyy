"""
Structured Logging Utilities for DevSkyy MCP Server
====================================================

Correlation ID tracking, async logging, JSON output for production.
Following Context7 best practices for structlog.
"""

import logging
import uuid
from contextvars import ContextVar

import structlog

# Context variables for async-safe logging context
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


def get_correlation_id() -> str:
    """Get current correlation ID from context."""
    return correlation_id_var.get() or generate_correlation_id()


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return f"corr-{uuid.uuid4().hex[:16]}"


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in async context."""
    correlation_id_var.set(correlation_id)


def set_request_context(request_id: str | None = None, user_id: str | None = None) -> None:
    """
    Set request context for correlation tracking.

    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
    """
    if request_id:
        request_id_var.set(request_id)

    if user_id:
        user_id_var.set(user_id)

    # Generate correlation ID if not set
    if not correlation_id_var.get():
        set_correlation_id(generate_correlation_id())


def clear_request_context() -> None:
    """Clear request context variables."""
    correlation_id_var.set("")
    request_id_var.set("")
    user_id_var.set("")


def configure_logging(json_output: bool = True) -> None:
    """
    Configure structlog for the MCP server.

    Args:
        json_output: If True, use JSON renderer for production
    """
    processors = [
        # Add correlation context from contextvars
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.processors.add_log_level,
        # Add timestamps
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add caller information (file, line, function)
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.FUNC_NAME,
            ]
        ),
    ]

    if json_output:
        # JSON output for production (machine-readable)
        processors.append(structlog.processors.JSONRenderer(indent=None, sort_keys=True))
    else:
        # Console output for development (human-readable)
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structlog logger with correlation context.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for scoped logging context."""

    def __init__(self, **kwargs):
        """
        Initialize logging context.

        Args:
            **kwargs: Context key-value pairs to bind
        """
        self.context = kwargs
        self.logger = get_logger(__name__)

    def __enter__(self):
        """Bind context on entry."""
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clear context on exit."""
        for key in self.context:
            structlog.contextvars.unbind_contextvars(key)


async def log_api_request(
    endpoint: str,
    method: str,
    params: dict | None = None,
    correlation_id: str | None = None,
) -> None:
    """
    Log API request with correlation tracking.

    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        params: Request parameters
        correlation_id: Optional correlation ID
    """
    logger = get_logger(__name__)

    if correlation_id:
        set_correlation_id(correlation_id)

    with LogContext(
        endpoint=endpoint,
        method=method,
        correlation_id=get_correlation_id(),
    ):
        await logger.ainfo(
            "api_request",
            params=params or {},
        )


async def log_api_response(
    endpoint: str,
    status_code: int,
    duration_ms: float,
    error: str | None = None,
) -> None:
    """
    Log API response with performance metrics.

    Args:
        endpoint: API endpoint path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        error: Optional error message
    """
    logger = get_logger(__name__)

    with LogContext(
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
        correlation_id=get_correlation_id(),
    ):
        if error:
            await logger.aerror(
                "api_response_error",
                error=error,
            )
        else:
            await logger.ainfo(
                "api_response_success",
            )


async def log_error(
    error: Exception,
    context: dict | None = None,
    stack_trace: str | None = None,
) -> None:
    """
    Log error with full context and stack trace.

    Args:
        error: Exception object
        context: Additional error context
        stack_trace: Optional stack trace string
    """
    logger = get_logger(__name__)

    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "correlation_id": get_correlation_id(),
    }

    if context:
        error_context.update(context)

    if stack_trace:
        error_context["stack_trace"] = stack_trace

    with LogContext(**error_context):
        await logger.aerror("exception_occurred")
