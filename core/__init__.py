"""
DevSkyy Core Module

Central utilities and infrastructure components including:
- Error ledger for tracking and persistence
- Application settings with Pydantic validation
- Exception hierarchy
- Logging utilities

Example:
    from core import get_settings, log_error

    settings = get_settings()
    print(f"Running in {settings.environment} mode")
"""

from .error_ledger import (
    ErrorCategory,
    ErrorEntry,
    ErrorLedger,
    ErrorSeverity,
    get_error_ledger,
    log_error,
)
from .settings import Settings, get_settings, settings


__all__ = [
    # Error Ledger
    "ErrorCategory",
    "ErrorEntry",
    "ErrorLedger",
    "ErrorSeverity",
    # Settings
    "Settings",
    "get_error_ledger",
    "get_settings",
    "log_error",
    "settings",
]

__version__ = "1.0.0"
