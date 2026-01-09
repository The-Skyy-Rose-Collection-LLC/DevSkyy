"""
DevSkyy Structured Logging Module
===================================

Production-grade structured logging with:
- JSON output for machine parsing (production)
- Pretty console output for development
- Correlation ID support for distributed tracing
- Context variables (contextvars) for request tracking
- Automatic timestamp injection
- Thread-safe operation

Usage:
    from core.structured_logging import configure_logging, bind_contextvars, unbind_contextvars
    import structlog

    # Configure once at application startup
    configure_logging()

    # Get logger
    logger = structlog.get_logger()

    # Log with context
    logger.info("user_action", action="login", user_id="123")

    # Bind request-scoped variables
    bind_contextvars(correlation_id="abc-123", user_id="user-456")
    logger.info("processing_request")  # Automatically includes correlation_id and user_id
    unbind_contextvars("correlation_id", "user_id")
"""

import logging
import sys
from contextvars import ContextVar
from typing import Any, cast

import structlog
from structlog.stdlib import BoundLogger
from structlog.types import EventDict, WrappedLogger

# Context variables for request-scoped logging
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
agent_id_var: ContextVar[str | None] = ContextVar("agent_id", default=None)


def add_context_vars(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    """Add context variables to log event."""
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id

    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id

    agent_id = agent_id_var.get()
    if agent_id:
        event_dict["agent_id"] = agent_id

    return event_dict


def bind_contextvars(**kwargs: str) -> None:
    """Bind context variables for the current context.

    Args:
        **kwargs: Key-value pairs to bind. Supported keys:
            - correlation_id: Request/transaction ID
            - user_id: User identifier
            - agent_id: Agent identifier

    Example:
        bind_contextvars(correlation_id="abc-123", user_id="user-456")
    """
    if "correlation_id" in kwargs:
        correlation_id_var.set(kwargs["correlation_id"])
    if "user_id" in kwargs:
        user_id_var.set(kwargs["user_id"])
    if "agent_id" in kwargs:
        agent_id_var.set(kwargs["agent_id"])


def unbind_contextvars(*keys: str) -> None:
    """Unbind context variables.

    Args:
        *keys: Variable names to unbind. If empty, unbinds all.

    Example:
        unbind_contextvars("correlation_id", "user_id")
        unbind_contextvars()  # Clear all
    """
    if not keys or "correlation_id" in keys:
        correlation_id_var.set(None)
    if not keys or "user_id" in keys:
        user_id_var.set(None)
    if not keys or "agent_id" in keys:
        agent_id_var.set(None)


def clear_contextvars() -> None:
    """Clear all context variables (alias for unbind_contextvars with no args)."""
    unbind_contextvars()


def configure_logging(
    *,
    json_output: bool | None = None,
    log_level: str = "INFO",
    include_timestamp: bool = True,
) -> None:
    """Configure structured logging for the application.

    Auto-detects whether to use JSON or console output based on:
    - json_output parameter (if provided)
    - Environment: JSON in production, pretty console in development
    - TTY detection: JSON if not a TTY, pretty console if TTY

    Args:
        json_output: If True, force JSON output. If False, force console output.
                    If None (default), auto-detect based on environment.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        include_timestamp: Whether to include timestamps in output

    Example:
        # Auto-detect (JSON in prod, console in dev)
        configure_logging()

        # Force JSON output
        configure_logging(json_output=True)

        # Debug mode with pretty console
        configure_logging(json_output=False, log_level="DEBUG")
    """
    # Auto-detect JSON vs console output
    if json_output is None:
        # Use JSON if not connected to a TTY (e.g., systemd, Docker logs)
        json_output = not sys.stdout.isatty()

    # Build processor chain
    processors: list[Any] = [
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Add context variables (correlation_id, user_id, agent_id)
        add_context_vars,
        # Add timestamp
        (
            structlog.processors.TimeStamper(fmt="iso", utc=True)
            if include_timestamp
            else lambda _, __, ed: ed
        ),
        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
    ]

    # Add renderer based on output format
    if json_output:
        # JSON renderer for production (machine parsing)
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console renderer for development (human-readable)
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=sys.stdout.isatty(),  # Colorize if TTY
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


# Pre-configured logger instance for convenience
def get_logger(name: str | None = None) -> BoundLogger:
    """Get a configured structlog logger.

    Args:
        name: Logger name (defaults to calling module name)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("operation_completed", duration_ms=150)
    """
    return cast(BoundLogger, structlog.get_logger(name))
