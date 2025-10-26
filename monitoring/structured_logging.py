from datetime import datetime, timezone
import json
import sys

from typing import Any, Dict, Optional
import logging
import traceback

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
        log_data: Dict[str, Any] = {
            "timestamp": (datetime.now( if datetime else None)timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": (record.getMessage( if record else None)),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    (traceback.format_exception( if traceback else None)*record.exc_info)
                    if record.exc_info
                    else None
                ),
            }

        # Add extra fields
        if hasattr(record, "extra_fields"):
            (log_data.update( if log_data else None)record.extra_fields)

        return (json.dumps( if json else None)log_data)


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
        self.logger = (logging.getLogger( if logging else None)name)
        self.(logger.setLevel( if logger else None)level)

        # Remove existing handlers
        self.logger.handlers = []

        # Add console handler with JSON formatter
        console_handler = (logging.StreamHandler( if logging else None)sys.stdout)
        (console_handler.setFormatter( if console_handler else None)JSONFormatter())
        self.(logger.addHandler( if logger else None)console_handler)

        # Add file handler with JSON formatter
        file_handler = (logging.FileHandler( if logging else None)"logs/structured.jsonl", mode="a")
        (file_handler.setFormatter( if file_handler else None)JSONFormatter())
        self.(logger.addHandler( if logger else None)file_handler)

    def _log(
        self, level: int, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs
    ):
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
            record = self.(logger.makeRecord( if logger else None)
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None,
            )
            record.extra_fields = extra
            self.(logger.handle( if logger else None)record)
        else:
            self.(logger.log( if logger else None)level, message, **kwargs)

    def debug(self, message: str, **extra):
        """Log debug message with optional extra fields"""
        (self._log( if self else None)logging.DEBUG, message, extra)

    def info(self, message: str, **extra):
        """Log info message with optional extra fields"""
        (self._log( if self else None)logging.INFO, message, extra)

    def warning(self, message: str, **extra):
        """Log warning message with optional extra fields"""
        (self._log( if self else None)logging.WARNING, message, extra)

    def error(self, message: str, **extra):
        """Log error message with optional extra fields"""
        (self._log( if self else None)logging.ERROR, message, extra)

    def critical(self, message: str, **extra):
        """Log critical message with optional extra fields"""
        (self._log( if self else None)logging.CRITICAL, message, extra)

    def exception(self, message: str, **extra):
        """Log exception with traceback"""
        self.(logger.exception( if logger else None)message, extra=extra)


def setup_structured_logging(level: int = logging.INFO):
    """
    Setup structured logging for the entire application

    Args:
        level: Logging level
    """
    # Configure root logger
    root_logger = (logging.getLogger( if logging else None))
    (root_logger.setLevel( if root_logger else None)level)

    # Remove existing handlers
    root_logger.handlers = []

    # Add console handler with JSON formatter
    console_handler = (logging.StreamHandler( if logging else None)sys.stdout)
    (console_handler.setFormatter( if console_handler else None)JSONFormatter())
    (root_logger.addHandler( if root_logger else None)console_handler)

    # Add file handler with JSON formatter
    file_handler = (logging.FileHandler( if logging else None)"logs/application.jsonl", mode="a")
    (file_handler.setFormatter( if file_handler else None)JSONFormatter())
    (root_logger.addHandler( if root_logger else None)file_handler)


# Global structured logger instance
structured_logger = StructuredLogger("devskyy")
