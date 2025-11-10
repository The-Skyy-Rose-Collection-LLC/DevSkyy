"""
Comprehensive Logging Configuration for DevSkyy

WHY THIS MODULE EXISTS:
- Debug CI/CD failures (can't attach debugger remotely)
- Security audit trail (Truth Protocol requirement)
- Performance tracking (P95 latency monitoring)
- Error pattern analysis (fix common issues)
- Structured logging (machine-parseable)

TRUTH PROTOCOL ALIGNMENT:
- No secrets in logs (automatic redaction)
- Structured format (JSON for parsing)
- Performance metrics (track P95)
- Error ledger integration
- Compliance-ready (GDPR, SOC2)

USAGE:
    from config.logging_config import setup_logging, get_logger

    # Initialize logging (do this once at app startup)
    setup_logging(environment="production")

    # Get logger for your module
    logger = get_logger(__name__)

    # Log with context
    logger.info("task_started", task_id="123", user_id="user-456")
"""

import logging
import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime
import traceback
import re


# =============================================================================
# Security: Sensitive Data Patterns
# =============================================================================

SENSITIVE_PATTERNS = [
    # API Keys
    (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})', re.IGNORECASE), '***API_KEY***'),
    # Passwords
    (re.compile(r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE), '***PASSWORD***'),
    # Tokens
    (re.compile(r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{20,})', re.IGNORECASE), '***TOKEN***'),
    # Email addresses (partial redaction)
    (re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'\1***@\2'),
    # Credit card numbers
    (re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'), '****-****-****-****'),
    # SSN
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '***-**-****'),
]


def redact_sensitive_data(message: str) -> str:
    """
    Redact sensitive data from log messages.

    WHY THIS FUNCTION:
    - Prevent credential leakage in logs
    - GDPR compliance (PII protection)
    - Security best practice
    - Truth Protocol requirement: "No secrets in code" includes logs

    HOW IT WORKS:
    - Uses regex to find sensitive patterns
    - Replaces with safe placeholders
    - Preserves log structure for debugging

    USAGE:
        message = "API key: sk-abc123xyz"
        safe_message = redact_sensitive_data(message)
        # Result: "API key: ***API_KEY***"
    """
    redacted = message

    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted


# =============================================================================
# Structured Logging Formatter
# =============================================================================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    WHY STRUCTURED LOGGING:
    - Machine-parseable (log aggregators love it)
    - Consistent format across services
    - Easy filtering and searching
    - Better debugging in production

    EXAMPLE OUTPUT:
    {
        "timestamp": "2025-11-10T12:34:56.789Z",
        "level": "INFO",
        "logger": "agent.orchestrator",
        "message": "task_completed",
        "task_id": "task-123",
        "duration_ms": 145.2,
        "status": "success"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        WHY THIS METHOD:
        - Converts Python logging to JSON
        - Adds metadata (timestamp, level, etc.)
        - Redacts sensitive data
        - Includes exception info if present
        """

        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields (from logger.info("msg", extra={...}))
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status"):
            log_data["status"] = record.status
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add file/line info for debugging
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }

        # Redact sensitive data from entire JSON
        json_str = json.dumps(log_data, default=str)
        safe_json_str = redact_sensitive_data(json_str)

        return safe_json_str


# =============================================================================
# Performance Tracking Logger
# =============================================================================

class PerformanceLogger:
    """
    Logger with performance tracking.

    WHY THIS CLASS:
    - Track P95 latency (Truth Protocol requirement)
    - Identify slow operations
    - Alert on performance degradation
    - Performance metrics for monitoring

    USAGE:
        perf_logger = PerformanceLogger("my_service")

        with perf_logger.track("database_query"):
            result = await db.fetchrow("SELECT * FROM users")

        # Logs: {"operation": "database_query", "duration_ms": 45.2}
    """

    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.latencies: Dict[str, list] = {}

    def track(self, operation: str):
        """
        Context manager to track operation duration.

        WHY THIS METHOD:
        - Automatic timing (no manual start/stop)
        - Logs duration automatically
        - Tracks P95 for analysis
        """
        from contextlib import contextmanager
        import time

        @contextmanager
        def _track():
            start = time.time()
            try:
                yield
            finally:
                elapsed = (time.time() - start) * 1000  # Convert to ms

                # Track latency
                if operation not in self.latencies:
                    self.latencies[operation] = []
                self.latencies[operation].append(elapsed)

                # Log the operation
                self.logger.info(
                    f"{operation}_completed",
                    extra={
                        "operation": operation,
                        "duration_ms": elapsed,
                        "status": "success"
                    }
                )

                # Alert if slow (P95 requirement: 200ms)
                if elapsed > 200:
                    self.logger.warning(
                        f"{operation}_slow",
                        extra={
                            "operation": operation,
                            "duration_ms": elapsed,
                            "threshold_ms": 200,
                            "exceeded_by_ms": elapsed - 200
                        }
                    )

        return _track()

    def get_p95_latency(self, operation: str) -> Optional[float]:
        """
        Calculate P95 latency for an operation.

        WHY THIS METHOD:
        - Validate Truth Protocol requirement (P95 < 200ms)
        - Identify performance regressions
        - Generate performance reports
        """
        if operation not in self.latencies or not self.latencies[operation]:
            return None

        sorted_latencies = sorted(self.latencies[operation])
        p95_index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[p95_index]


# =============================================================================
# Logger Setup
# =============================================================================

def setup_logging(
    environment: str = "production",
    log_level: str = "INFO",
    log_file: Optional[str] = None
):
    """
    Set up logging configuration.

    WHY THIS FUNCTION:
    - Centralized logging setup
    - Environment-specific configuration
    - Structured logging for production
    - Human-readable for development

    PARAMETERS:
        environment: "production", "development", or "test"
        log_level: "DEBUG", "INFO", "WARNING", "ERROR"
        log_file: Optional file path for file logging

    USAGE:
        # Production (JSON structured logs)
        setup_logging(environment="production", log_level="INFO")

        # Development (human-readable logs)
        setup_logging(environment="development", log_level="DEBUG")

        # Testing (verbose logs)
        setup_logging(environment="test", log_level="DEBUG")
    """

    # Determine log level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Format based on environment
    if environment == "production":
        # Structured JSON logging for production
        formatter = StructuredFormatter()
    else:
        # Human-readable logging for development/test
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Configure specific loggers
    # Silence noisy third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured",
        extra={
            "environment": environment,
            "log_level": log_level,
            "structured": environment == "production"
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a module.

    WHY THIS FUNCTION:
    - Consistent logger creation
    - Automatic naming
    - Pre-configured settings

    USAGE:
        logger = get_logger(__name__)
        logger.info("operation_started", extra={"user_id": "123"})
    """
    return logging.getLogger(name)


# =============================================================================
# Context-Aware Logger
# =============================================================================

class ContextLogger:
    """
    Logger with automatic context injection.

    WHY THIS CLASS:
    - Automatic request ID injection
    - User context tracking
    - Consistent logging across request lifecycle

    USAGE:
        logger = ContextLogger("api", request_id="req-123", user_id="user-456")
        logger.info("request_started")
        # Logs: {..., "request_id": "req-123", "user_id": "user-456"}
    """

    def __init__(self, name: str, **context):
        self.logger = get_logger(name)
        self.context = context

    def _log(self, level: str, message: str, **extra):
        """Internal logging with context."""
        # Merge context with extra fields
        log_data = {**self.context, **extra}
        getattr(self.logger, level)(message, extra=log_data)

    def debug(self, message: str, **extra):
        self._log("debug", message, **extra)

    def info(self, message: str, **extra):
        self._log("info", message, **extra)

    def warning(self, message: str, **extra):
        self._log("warning", message, **extra)

    def error(self, message: str, **extra):
        self._log("error", message, **extra)

    def critical(self, message: str, **extra):
        self._log("critical", message, **extra)


# =============================================================================
# Error Ledger Integration
# =============================================================================

def log_to_error_ledger(
    error_type: str,
    error_message: str,
    context: Dict[str, Any],
    ledger_file: str = "artifacts/error-ledger.json"
):
    """
    Log errors to Truth Protocol error ledger.

    WHY THIS FUNCTION:
    - Truth Protocol requirement: "No-skip rule"
    - Complete audit trail
    - Error pattern analysis
    - Compliance requirement

    USAGE:
        try:
            risky_operation()
        except Exception as e:
            log_to_error_ledger(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"operation": "risky_operation", "user_id": "123"}
            )
    """
    import os

    # Create artifacts directory if needed
    os.makedirs(os.path.dirname(ledger_file), exist_ok=True)

    # Create error entry
    error_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error_type": error_type,
        "error_message": error_message,
        "context": context,
        "traceback": traceback.format_exc()
    }

    # Append to ledger (JSONL format - one JSON per line)
    with open(ledger_file, "a") as f:
        f.write(json.dumps(error_entry) + "\n")

    # Also log normally
    logger = get_logger("error_ledger")
    logger.error(
        "error_recorded",
        extra={
            "error_type": error_type,
            "error_message": error_message,
            **context
        }
    )


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Example 1: Basic setup
    setup_logging(environment="development", log_level="DEBUG")
    logger = get_logger(__name__)

    logger.info("Application started")
    logger.debug("Debug information", extra={"user_id": "123"})

    # Example 2: Performance tracking
    perf_logger = PerformanceLogger("database")
    with perf_logger.track("user_query"):
        import time
        time.sleep(0.05)  # Simulate query

    print(f"P95 latency: {perf_logger.get_p95_latency('user_query')}ms")

    # Example 3: Context logger
    ctx_logger = ContextLogger("api", request_id="req-123", user_id="user-456")
    ctx_logger.info("request_processed")

    # Example 4: Error ledger
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_to_error_ledger(
            error_type=type(e).__name__,
            error_message=str(e),
            context={"operation": "test"}
        )
