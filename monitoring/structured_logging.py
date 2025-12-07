from datetime import UTC, datetime
import json
import logging
import sys
import traceback
from typing import Any


"""
Structured Logging for Grade A+ Infrastructure Score
JSON-formatted logs for easy parsing and analysis
"""


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    Outputs logs in JSON format for easy parsing by log aggregation systems
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (traceback.format_exception(*record.exc_info) if record.exc_info else None),
            }

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger wrapper for enterprise-grade logging
    """

    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger

        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Remove existing handlers
        self.logger.handlers = []

        # Add console handler with JSON formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)

        # Add file handler with JSON formatter
        file_handler = logging.FileHandler("logs/structured.jsonl", mode="a")
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)

    def _log(self, level: int, message: str, extra: dict[str, Any] | None = None, **kwargs):
        """
        Internal log method with extra fields

        Args:
            level: Log level
            message: Log message
            extra: Extra fields to include
            **kwargs: Additional keyword arguments
        """
        if extra:
            # Create a log record with extra fields
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None,
            )
            record.extra_fields = extra
            self.logger.handle(record)
        else:
            self.logger.log(level, message, **kwargs)

    def debug(self, message: str, **extra):
        """Log debug message with optional extra fields"""
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, **extra):
        """Log info message with optional extra fields"""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, **extra):
        """Log warning message with optional extra fields"""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, **extra):
        """Log error message with optional extra fields"""
        self._log(logging.ERROR, message, extra)

    def critical(self, message: str, **extra):
        """Log critical message with optional extra fields"""
        self._log(logging.CRITICAL, message, extra)

    def exception(self, message: str, **extra):
        """Log exception with traceback"""
        self.logger.exception(message, extra=extra)


def setup_structured_logging(level: int = logging.INFO):
    """
    Setup structured logging for the entire application

    Args:
        level: Logging level
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Add console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Add file handler with JSON formatter
    file_handler = logging.FileHandler("logs/application.jsonl", mode="a")
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)


# Global structured logger instance
structured_logger = StructuredLogger("devskyy")
