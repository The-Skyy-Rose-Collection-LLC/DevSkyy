#!/usr/bin/env python3
"""
Enterprise Logging System for DevSkyy Platform
Comprehensive logging with structured output, correlation IDs, and observability
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import os
from pathlib import Path
import threading
from contextlib import contextmanager

class LogLevel(Enum):
    """Log levels for structured logging."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log categories for better organization."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL = "external"
    USER = "user"
    AUDIT = "audit"

@dataclass
class LogContext:
    """Context information for structured logging."""
    correlation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    environment: str = "development"

@dataclass
class StructuredLogEntry:
    """Structured log entry with all required fields."""
    timestamp: str
    level: str
    category: str
    message: str
    context: LogContext
    metadata: Dict[str, Any]
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class EnterpriseLogger:
    """
    Enterprise-grade logging system with structured output,
    correlation tracking, and observability features.
    """
    
    def __init__(self, name: str = "devskyy"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._context_storage = threading.local()
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup enterprise logging configuration."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create formatters
        json_formatter = JsonFormatter()
        console_formatter = ConsoleFormatter()
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for structured logs
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(logs_dir / "devskyy.jsonl")
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(logs_dir / "errors.jsonl")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        self.logger.addHandler(error_handler)
        
        # Audit log handler
        audit_handler = logging.FileHandler(logs_dir / "audit.jsonl")
        audit_handler.setFormatter(json_formatter)
        self.audit_logger = logging.getLogger(f"{self.name}.audit")
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def set_context(self, context: LogContext):
        """Set logging context for current thread."""
        self._context_storage.context = context
    
    def get_context(self) -> Optional[LogContext]:
        """Get current logging context."""
        return getattr(self._context_storage, 'context', None)
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager for temporary logging context."""
        old_context = self.get_context()
        
        # Create new context or update existing
        if old_context:
            new_context = LogContext(
                correlation_id=kwargs.get('correlation_id', old_context.correlation_id),
                user_id=kwargs.get('user_id', old_context.user_id),
                session_id=kwargs.get('session_id', old_context.session_id),
                request_id=kwargs.get('request_id', old_context.request_id),
                trace_id=kwargs.get('trace_id', old_context.trace_id),
                span_id=kwargs.get('span_id', old_context.span_id),
                component=kwargs.get('component', old_context.component),
                operation=kwargs.get('operation', old_context.operation),
                environment=kwargs.get('environment', old_context.environment)
            )
        else:
            new_context = LogContext(
                correlation_id=kwargs.get('correlation_id', str(uuid.uuid4())),
                user_id=kwargs.get('user_id'),
                session_id=kwargs.get('session_id'),
                request_id=kwargs.get('request_id'),
                trace_id=kwargs.get('trace_id'),
                span_id=kwargs.get('span_id'),
                component=kwargs.get('component'),
                operation=kwargs.get('operation'),
                environment=kwargs.get('environment', 'development')
            )
        
        self.set_context(new_context)
        try:
            yield new_context
        finally:
            self.set_context(old_context)
    
    def _create_log_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> StructuredLogEntry:
        """Create structured log entry."""
        context = self.get_context() or LogContext(
            correlation_id=str(uuid.uuid4()),
            environment=os.getenv("ENVIRONMENT", "development")
        )
        
        error_details = None
        if error:
            error_details = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        return StructuredLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=level.value,
            category=category.value,
            message=message,
            context=context,
            metadata=metadata or {},
            error_details=error_details,
            performance_metrics=performance_metrics
        )
    
    def debug(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log debug message."""
        entry = self._create_log_entry(LogLevel.DEBUG, category, message, metadata)
        self.logger.debug(entry)
    
    def info(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ):
        """Log info message."""
        entry = self._create_log_entry(
            LogLevel.INFO, category, message, metadata, performance_metrics=performance_metrics
        )
        self.logger.info(entry)
    
    def warning(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log warning message."""
        entry = self._create_log_entry(LogLevel.WARNING, category, message, metadata)
        self.logger.warning(entry)
    
    def error(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """Log error message."""
        entry = self._create_log_entry(LogLevel.ERROR, category, message, metadata, error)
        self.logger.error(entry)
    
    def critical(
        self,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """Log critical message."""
        entry = self._create_log_entry(LogLevel.CRITICAL, category, message, metadata, error)
        self.logger.critical(entry)
    
    def audit(
        self,
        action: str,
        resource: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log audit event."""
        entry = self._create_log_entry(
            LogLevel.INFO,
            LogCategory.AUDIT,
            f"Audit: {action} on {resource}",
            metadata
        )
        self.audit_logger.info(entry)
    
    def security(
        self,
        event: str,
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security event."""
        security_metadata = {
            "severity": severity,
            "event_type": "security",
            **(metadata or {})
        }
        
        level = LogLevel.WARNING if severity in ["medium", "high"] else LogLevel.INFO
        entry = self._create_log_entry(
            level,
            LogCategory.SECURITY,
            f"Security Event: {event}",
            security_metadata
        )
        
        if severity == "high":
            self.logger.error(entry)
        elif severity == "medium":
            self.logger.warning(entry)
        else:
            self.logger.info(entry)
    
    def performance(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics."""
        performance_metrics = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        entry = self._create_log_entry(
            LogLevel.INFO,
            LogCategory.PERFORMANCE,
            f"Performance: {operation} completed in {duration:.3f}s",
            metadata,
            performance_metrics=performance_metrics
        )
        self.logger.info(entry)

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        if isinstance(record.msg, StructuredLogEntry):
            return json.dumps(asdict(record.msg), ensure_ascii=False)
        else:
            # Fallback for non-structured logs
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": str(record.msg),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }, ensure_ascii=False)

class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        if isinstance(record.msg, StructuredLogEntry):
            entry = record.msg
            color = self.COLORS.get(entry.level, '')
            reset = self.COLORS['RESET']
            
            return (
                f"{color}[{entry.timestamp}] {entry.level} "
                f"[{entry.category}] {entry.message}{reset}"
            )
        else:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            return f"{color}[{record.levelname}] {record.msg}{reset}"

# Global enterprise logger instance
enterprise_logger = EnterpriseLogger()

# Convenience functions
def debug(message: str, **kwargs):
    """Log debug message."""
    enterprise_logger.debug(message, **kwargs)

def info(message: str, **kwargs):
    """Log info message."""
    enterprise_logger.info(message, **kwargs)

def warning(message: str, **kwargs):
    """Log warning message."""
    enterprise_logger.warning(message, **kwargs)

def error(message: str, **kwargs):
    """Log error message."""
    enterprise_logger.error(message, **kwargs)

def critical(message: str, **kwargs):
    """Log critical message."""
    enterprise_logger.critical(message, **kwargs)

def audit(action: str, resource: str, **kwargs):
    """Log audit event."""
    enterprise_logger.audit(action, resource, **kwargs)

def security(event: str, **kwargs):
    """Log security event."""
    enterprise_logger.security(event, **kwargs)

def performance(operation: str, duration: float, **kwargs):
    """Log performance metrics."""
    enterprise_logger.performance(operation, duration, **kwargs)
