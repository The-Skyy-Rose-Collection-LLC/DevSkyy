"""
DevSkyy Core Module
Central utilities and infrastructure components
"""

from .error_ledger import (
    ErrorCategory,
    ErrorEntry,
    ErrorLedger,
    ErrorSeverity,
    get_error_ledger,
    log_error,
)

__all__ = [
    "ErrorLedger",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorEntry",
    "get_error_ledger",
    "log_error",
]

__version__ = "1.0.0"
