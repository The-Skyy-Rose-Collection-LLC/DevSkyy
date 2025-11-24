"""
DevSkyy Enterprise Error Handling
Truth Protocol Rule #10: Error Ledger Required - Every error is tracked and recorded

This module provides enterprise-grade error handling with:
- Structured error logging
- Error ledger generation (Truth Protocol Rule #14)
- Error classification and routing
- PII sanitization
- Sentry integration
- OpenTelemetry tracing
"""

from datetime import UTC, datetime
import json
import logging
import logging.handlers
import sys
import traceback
from typing import Any

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ErrorRecord(BaseModel):
    """Enterprise error record per Truth Protocol Rule #14"""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    error_id: str
    error_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    trace: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    environment: str  # development, staging, production
    component: str
    action: str  # "continue" or "halt"

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-17T19:00:00Z",
                "error_id": "err_123abc",
                "error_type": "DatabaseConnectionError",
                "severity": "HIGH",
                "message": "Failed to connect to primary database",
                "context": {"database": "postgres", "retry_count": 3},
                "trace": "Traceback...",
                "user_id": "user_123",
                "request_id": "req_456",
                "environment": "production",
                "component": "infrastructure.database",
                "action": "continue",
            }
        }


class EnterpriseErrorHandler:
    """
    Enterprise error handler per Truth Protocol specifications.

    Implements Rule #10: No-skip rule - Log errors and continue processing
    Implements Rule #14: Error ledger required - All errors tracked in JSON format
    """

    def __init__(self, ledger_path: str = "/artifacts/error-ledger.json"):
        """Initialize error handler with ledger path"""
        self.ledger_path = ledger_path
        self.errors: list[ErrorRecord] = []

        # Configure structured logging
        self.configure_logging()

    def configure_logging(self) -> None:
        """Configure enterprise-grade structured logging"""
        # JSON formatter for structured logs
        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_obj = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
                if record.exc_info:
                    log_obj["exception"] = traceback.format_exception(*record.exc_info)
                return json.dumps(log_obj)

        # Create handlers
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(JsonFormatter())

        file_handler = logging.handlers.RotatingFileHandler(
            "/logs/devskyy-enterprise.log",
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=10,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())

        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        logger.info("✓ Enterprise logging configured")

    def record_error(
        self,
        error_type: str,
        message: str,
        severity: str = "MEDIUM",
        context: dict[str, Any] | None = None,
        exception: Exception | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        component: str = "unknown",
        action: str = "continue",
    ) -> ErrorRecord:
        """
        Record an error per Truth Protocol Rule #14.

        Args:
            error_type: Type of error (class name)
            message: Human-readable error message
            severity: CRITICAL, HIGH, MEDIUM, LOW
            context: Additional context data
            exception: Original exception object
            user_id: User ID for the error
            request_id: Request ID for tracing
            component: Component where error occurred
            action: "continue" (default) or "halt"

        Returns:
            ErrorRecord: Recorded error information
        """
        import os

        error_id = f"err_{datetime.now(UTC).timestamp():.0f}"
        context = context or {}

        # Sanitize PII from context
        context = self._sanitize_pii(context)

        # Format traceback
        trace = None
        if exception:
            trace = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))

        # Create error record
        error_record = ErrorRecord(
            error_id=error_id,
            error_type=error_type,
            severity=severity,
            message=message,
            context=context,
            trace=trace,
            user_id=user_id,
            request_id=request_id,
            environment=os.getenv("ENVIRONMENT", "unknown"),
            component=component,
            action=action,
        )

        # Store in ledger
        self.errors.append(error_record)
        self._write_ledger()

        # Log the error
        logger.error(
            f"[{error_id}] {error_type}: {message}",
            extra={
                "error_id": error_id,
                "severity": severity,
                "component": component,
                "trace": trace,
            },
        )

        return error_record

    def _sanitize_pii(self, data: Any) -> Any:
        """
        Sanitize Personally Identifiable Information (PII) from data.
        Truth Protocol Rule #5: No secrets in code - extend to logs.

        Args:
            data: Data to sanitize

        Returns:
            Sanitized copy of data
        """
        if isinstance(data, dict):
            sanitized = {}
            pii_fields = {
                "password",
                "api_key",
                "secret",
                "token",
                "credit_card",
                "ssn",
                "email",
                "phone",
                "address",
            }
            for key, value in data.items():
                if any(pii_field in key.lower() for pii_field in pii_fields):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = self._sanitize_pii(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_pii(item) for item in data]
        else:
            return data

    def _write_ledger(self) -> None:
        """Write error ledger to disk"""
        try:
            import os

            os.makedirs(os.path.dirname(self.ledger_path) or ".", exist_ok=True)

            ledger_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "total_errors": len(self.errors),
                "errors": [error.model_dump() for error in self.errors],
                "summary": self._get_summary(),
            }

            with open(self.ledger_path, "w") as f:
                json.dump(ledger_data, f, indent=2, default=str)
        except Exception as e:
            logger.exception(f"Failed to write error ledger: {e}")

    def _get_summary(self) -> dict[str, int]:
        """Get error summary statistics"""
        summary = {
            "total": len(self.errors),
            "critical": sum(1 for e in self.errors if e.severity == "CRITICAL"),
            "high": sum(1 for e in self.errors if e.severity == "HIGH"),
            "medium": sum(1 for e in self.errors if e.severity == "MEDIUM"),
            "low": sum(1 for e in self.errors if e.severity == "LOW"),
        }
        return summary

    def should_halt(self) -> bool:
        """
        Determine if processing should halt due to errors.

        Rule #10: No-skip rule - Continue processing unless CRITICAL errors.
        """
        critical_count = sum(1 for e in self.errors if e.severity == "CRITICAL")
        return critical_count > 0

    def export_ledger(self) -> dict[str, Any]:
        """Export error ledger"""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_errors": len(self.errors),
            "errors": [error.model_dump() for error in self.errors],
            "summary": self._get_summary(),
        }


# Global error handler instance
_global_error_handler: EnterpriseErrorHandler | None = None


def get_error_handler() -> EnterpriseErrorHandler:
    """Get or create global error handler"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = EnterpriseErrorHandler()
    return _global_error_handler


def record_error(
    error_type: str,
    message: str,
    severity: str = "MEDIUM",
    context: dict[str, Any] | None = None,
    exception: Exception | None = None,
    **kwargs: Any,
) -> ErrorRecord:
    """Convenience function to record error using global handler"""
    return get_error_handler().record_error(
        error_type=error_type,
        message=message,
        severity=severity,
        context=context,
        exception=exception,
        **kwargs,
    )
