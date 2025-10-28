"""
Enterprise Structured Logging Configuration for DevSkyy Platform
Correlation IDs, centralized error handling, and security event logging
"""

import json
import logging
import logging.config
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

import structlog
from structlog.stdlib import LoggerFactory


# ============================================================================
# CORRELATION ID MANAGEMENT
# ============================================================================

# Context variable for correlation ID (thread-safe)
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    """Get current correlation ID or generate new one"""
    current_id = correlation_id.get()
    if not current_id:
        current_id = str(uuid.uuid4())
        correlation_id.set(current_id)
    return current_id


def set_correlation_id(request_id: str):
    """Set correlation ID for current context"""
    correlation_id.set(request_id)


def clear_correlation_id():
    """Clear correlation ID from current context"""
    correlation_id.set(None)


# ============================================================================
# CUSTOM PROCESSORS
# ============================================================================


def add_correlation_id(logger, method_name, event_dict):
    """Add correlation ID to log entries"""
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Add ISO timestamp to log entries"""
    event_dict["timestamp"] = datetime.utcnow().isoformat() + "Z"
    return event_dict


def add_service_info(logger, method_name, event_dict):
    """Add service information to log entries"""
    event_dict["service"] = "devskyy-enterprise"
    event_dict["version"] = os.getenv("APP_VERSION", "5.1.0")
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    return event_dict


def add_security_context(logger, method_name, event_dict):
    """Add security context to log entries"""
    # Add security-related fields if available
    if hasattr(event_dict.get("request"), "state"):
        request = event_dict["request"]
        if hasattr(request.state, "user_id"):
            event_dict["user_id"] = request.state.user_id
        if hasattr(request.state, "client_ip"):
            event_dict["client_ip"] = request.state.client_ip

    return event_dict


def sanitize_sensitive_data(logger, method_name, event_dict):
    """Sanitize sensitive data from log entries"""
    sensitive_fields = ["password", "token", "secret", "key", "authorization"]

    def sanitize_dict(data):
        if isinstance(data, dict):
            return {
                k: (
                    "***REDACTED***"
                    if any(field in k.lower() for field in sensitive_fields)
                    else sanitize_dict(v) if isinstance(v, (dict, list)) else v
                )
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [sanitize_dict(item) for item in data]
        return data

    # Sanitize the entire event dict
    for key, value in event_dict.items():
        if isinstance(value, (dict, list)):
            event_dict[key] = sanitize_dict(value)
        elif isinstance(value, str) and any(field in key.lower() for field in sensitive_fields):
            event_dict[key] = "***REDACTED***"

    return event_dict


# ============================================================================
# CUSTOM FORMATTERS
# ============================================================================


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
            "service": "devskyy-enterprise",
            "version": os.getenv("APP_VERSION", "5.1.0"),
            "environment": os.getenv("ENVIRONMENT", "development"),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class SecurityFormatter(logging.Formatter):
    """Special formatter for security events"""

    def format(self, record):
        """Format security log record"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "security",
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": get_correlation_id(),
            "service": "devskyy-enterprise",
            "security_category": getattr(record, "security_category", "general"),
            "threat_level": getattr(record, "threat_level", "low"),
            "user_id": getattr(record, "user_id", None),
            "client_ip": getattr(record, "client_ip", None),
            "user_agent": getattr(record, "user_agent", None),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================


def setup_logging():
    """Setup enterprise structured logging"""

    # Determine log level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_correlation_id,
            add_timestamp,
            add_service_info,
            add_security_context,
            sanitize_sensitive_data,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "security": {
                "()": SecurityFormatter,
                exc_info=(type(error), error, error.__traceback__),
            "console": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console" if os.getenv("ENVIRONMENT") == "development" else "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/devskyy.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                    exc_info=(type(error), error, error.__traceback__),
            },
            "error": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "json",
                "level": "ERROR",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "devskyy.security": {
                "handlers": ["security", "console"],
                "level": "INFO",
                "propagate": False,
            },
            "devskyy.error": {
                "handlers": ["error", "console"],
                "level": "ERROR",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Get structured logger
    logger = structlog.get_logger()
    logger.info(
        "🚀 Structured logging initialized", log_level=log_level, environment=os.getenv("ENVIRONMENT", "development")
    )


# ============================================================================
# SPECIALIZED LOGGERS
# ============================================================================


class SecurityLogger:
    """Specialized logger for security events"""

    def __init__(self):
        self.logger = logging.getLogger("devskyy.security")

    def log_authentication_event(self, event_type: str, user_id: str, client_ip: str, success: bool, **kwargs):
        """Log authentication events"""
        self.logger.info(
            f"Authentication {event_type}: {'SUCCESS' if success else 'FAILED'}",
            extra={
                "security_category": "authentication",
                "event_type": event_type,
                "user_id": user_id,
                "client_ip": client_ip,
                "success": success,
                "threat_level": "low" if success else "medium",
                **kwargs,
            },
        )

    def log_authorization_event(self, user_id: str, resource: str, action: str, allowed: bool, **kwargs):
        """Log authorization events"""
        self.logger.info(
            f"Authorization: {action} on {resource} {'ALLOWED' if allowed else 'DENIED'}",
            extra={
                "security_category": "authorization",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "allowed": allowed,
                "threat_level": "low" if allowed else "medium",
                **kwargs,
            },
        )

    def log_security_violation(
        self, violation_type: str, client_ip: str, details: str, threat_level: str = "high", **kwargs
    ):
        """Log security violations"""
        self.logger.warning(
            f"Security violation: {violation_type}",
            extra={
                "security_category": "violation",
                "violation_type": violation_type,
                "client_ip": client_ip,
                "details": details,
                "threat_level": threat_level,
                **kwargs,
            },
        )

    def log_data_access(self, user_id: str, table: str, operation: str, record_count: int = None, **kwargs):
        """Log data access events"""
        self.logger.info(
            f"Data access: {operation} on {table}",
            extra={
                "security_category": "data_access",
                "user_id": user_id,
                "table": table,
                "operation": operation,
                "record_count": record_count,
                "threat_level": "low",
                **kwargs,
            },
        )


class ErrorLogger:
    """Specialized logger for error tracking"""

    def __init__(self):
        self.logger = logging.getLogger("devskyy.error")

    def log_application_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log application errors with context"""
        self.logger.error(
            f"Application error: {str(error)}",
            exc_info=error,
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "correlation_id": get_correlation_id(),
            },
        )

    def log_api_error(self, endpoint: str, method: str, status_code: int, error: Exception, user_id: str = None):
        """Log API errors"""
        self.logger.error(
            f"API error: {method} {endpoint} - {status_code}",
            exc_info=error,
            extra={
                "error_category": "api",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "user_id": user_id,
                "error_type": type(error).__name__,
            },
        )

    def log_database_error(self, operation: str, error: Exception, query: str = None, user_id: str = None):
        """Log database errors"""
        self.logger.error(
            f"Database error: {operation}",
            exc_info=error,
            extra={
                "error_category": "database",
                "operation": operation,
                "query": query[:200] if query else None,  # Truncate long queries
                "user_id": user_id,
                "error_type": type(error).__name__,
            },
        )


# ============================================================================
# GLOBAL LOGGER INSTANCES
# ============================================================================

# Initialize specialized loggers
security_logger = SecurityLogger()
error_logger = ErrorLogger()

# Get structured logger
structured_logger = structlog.get_logger()
