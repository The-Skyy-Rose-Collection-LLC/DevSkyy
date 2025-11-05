"""
Error Ledger System - Truth Protocol Compliance
Per Truth Protocol Rule #10: No-skip rule - Log all errors

Implements centralized error tracking and reporting for the DevSkyy Platform.
All errors are logged to /artifacts/error-ledger-<run_id>.json

Features:
- Persistent error logging across application lifetime
- Error categorization and severity levels
- Stack trace capture
- Context capture for debugging
- Error metrics and statistics
- JSON format for machine readability
"""

import json
import logging
import sys
import traceback
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"  # System failure, immediate action required
    HIGH = "high"          # Major functionality broken
    MEDIUM = "medium"      # Partial functionality affected
    LOW = "low"            # Minor issue, workaround available
    INFO = "info"          # Informational, not actually an error


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    AGENT = "agent"
    ML_MODEL = "ml_model"
    SECURITY = "security"
    PERFORMANCE = "performance"
    UNKNOWN = "unknown"


@dataclass
class ErrorEntry:
    """Single error entry in the ledger"""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            **asdict(self),
            "severity": self.severity.value,
            "category": self.category.value
        }


class ErrorLedger:
    """
    Centralized error ledger for the DevSkyy Platform

    Thread-safe error logging with automatic persistence
    """

    def __init__(self, run_id: Optional[str] = None, artifacts_dir: str = "artifacts"):
        """
        Initialize error ledger

        Args:
            run_id: Unique run identifier (auto-generated if not provided)
            artifacts_dir: Directory to store error ledger files
        """
        self.run_id = run_id or self._generate_run_id()
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        self.ledger_file = self.artifacts_dir / f"error-ledger-{self.run_id}.json"
        self.errors: List[ErrorEntry] = []

        # Metadata
        self.metadata = {
            "run_id": self.run_id,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "platform": sys.platform,
            "python_version": sys.version,
            "environment": self._get_environment()
        }

        # Initialize ledger file
        self._initialize_ledger()

        logger.info(f"✅ Error ledger initialized - Run ID: {self.run_id}")

    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}"

    def _get_environment(self) -> str:
        """Get current environment"""
        import os
        return os.getenv("ENVIRONMENT", "development")

    def _initialize_ledger(self):
        """Initialize ledger file with metadata"""
        initial_data = {
            "metadata": self.metadata,
            "errors": [],
            "statistics": {
                "total_errors": 0,
                "by_severity": {},
                "by_category": {},
                "resolved_count": 0
            }
        }

        with open(self.ledger_file, "w") as f:
            json.dump(initial_data, f, indent=2)

    def log_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None
    ) -> str:
        """
        Log an error to the ledger

        Args:
            error: Exception instance
            severity: Error severity level
            category: Error category
            context: Additional context information
            correlation_id: Request correlation ID
            user_id: User ID if applicable
            endpoint: API endpoint if applicable
            method: HTTP method if applicable

        Returns:
            Error ID
        """
        # Extract error information
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        # Get source information
        tb = error.__traceback__
        source_file = None
        source_line = None

        if tb:
            # Get the deepest frame in our code (not in libraries)
            while tb.tb_next:
                tb = tb.tb_next
            source_file = tb.tb_frame.f_code.co_filename
            source_line = tb.tb_lineno

        # Create error entry
        error_entry = ErrorEntry(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            severity=severity,
            category=category,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            context=context or {},
            correlation_id=correlation_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            source_file=source_file,
            source_line=source_line
        )

        # Add to in-memory list
        self.errors.append(error_entry)

        # Persist to file
        self._persist_error(error_entry)

        # Log to standard logger
        log_message = f"Error logged [{error_entry.error_id}] - {severity.value.upper()}: {error_type} - {error_message}"

        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return error_entry.error_id

    def _persist_error(self, error_entry: ErrorEntry):
        """Persist error to ledger file"""
        try:
            # Read current ledger
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)

            # Add new error
            ledger_data["errors"].append(error_entry.to_dict())

            # Update statistics
            ledger_data["statistics"]["total_errors"] = len(ledger_data["errors"])

            # By severity
            severity_key = error_entry.severity.value
            ledger_data["statistics"]["by_severity"][severity_key] = \
                ledger_data["statistics"]["by_severity"].get(severity_key, 0) + 1

            # By category
            category_key = error_entry.category.value
            ledger_data["statistics"]["by_category"][category_key] = \
                ledger_data["statistics"]["by_category"].get(category_key, 0) + 1

            # Resolved count
            ledger_data["statistics"]["resolved_count"] = sum(
                1 for e in ledger_data["errors"] if e.get("resolved", False)
            )

            # Write back to file
            with open(self.ledger_file, "w") as f:
                json.dump(ledger_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to persist error to ledger: {e}")

    def mark_resolved(self, error_id: str, resolution_notes: str):
        """
        Mark an error as resolved

        Args:
            error_id: Error ID to mark as resolved
            resolution_notes: Notes about the resolution
        """
        try:
            # Update in-memory
            for error in self.errors:
                if error.error_id == error_id:
                    error.resolved = True
                    error.resolution_notes = resolution_notes
                    break

            # Update in file
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)

            for error in ledger_data["errors"]:
                if error["error_id"] == error_id:
                    error["resolved"] = True
                    error["resolution_notes"] = resolution_notes
                    break

            # Update resolved count
            ledger_data["statistics"]["resolved_count"] = sum(
                1 for e in ledger_data["errors"] if e.get("resolved", False)
            )

            with open(self.ledger_file, "w") as f:
                json.dump(ledger_data, f, indent=2)

            logger.info(f"✅ Error {error_id} marked as resolved: {resolution_notes}")

        except Exception as e:
            logger.error(f"Failed to mark error as resolved: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        try:
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)
            return ledger_data["statistics"]
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def get_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        resolved: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get errors with optional filters

        Args:
            severity: Filter by severity
            category: Filter by category
            resolved: Filter by resolution status
            limit: Maximum number of errors to return

        Returns:
            List of error dictionaries
        """
        try:
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)

            errors = ledger_data["errors"]

            # Apply filters
            if severity:
                errors = [e for e in errors if e["severity"] == severity.value]
            if category:
                errors = [e for e in errors if e["category"] == category.value]
            if resolved is not None:
                errors = [e for e in errors if e.get("resolved", False) == resolved]

            # Apply limit
            if limit:
                errors = errors[-limit:]

            return errors

        except Exception as e:
            logger.error(f"Failed to get errors: {e}")
            return []

    def export_report(self, output_file: Optional[str] = None) -> str:
        """
        Export error ledger as a formatted report

        Args:
            output_file: Optional output file path

        Returns:
            Report text
        """
        try:
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)

            # Generate report
            report_lines = [
                "=" * 80,
                "ERROR LEDGER REPORT",
                "=" * 80,
                "",
                f"Run ID: {self.run_id}",
                f"Started: {self.metadata['started_at']}",
                f"Environment: {self.metadata['environment']}",
                "",
                "=" * 80,
                "STATISTICS",
                "=" * 80,
                "",
                f"Total Errors: {ledger_data['statistics']['total_errors']}",
                f"Resolved: {ledger_data['statistics']['resolved_count']}",
                f"Unresolved: {ledger_data['statistics']['total_errors'] - ledger_data['statistics']['resolved_count']}",
                "",
                "By Severity:",
            ]

            for severity, count in ledger_data['statistics']['by_severity'].items():
                report_lines.append(f"  {severity.upper()}: {count}")

            report_lines.extend([
                "",
                "By Category:",
            ])

            for category, count in ledger_data['statistics']['by_category'].items():
                report_lines.append(f"  {category}: {count}")

            report_lines.extend([
                "",
                "=" * 80,
                "ERROR DETAILS",
                "=" * 80,
                ""
            ])

            # Add error details
            for error in ledger_data['errors']:
                report_lines.extend([
                    f"Error ID: {error['error_id']}",
                    f"Timestamp: {error['timestamp']}",
                    f"Severity: {error['severity'].upper()}",
                    f"Category: {error['category']}",
                    f"Type: {error['error_type']}",
                    f"Message: {error['error_message']}",
                    f"Resolved: {'✅ Yes' if error.get('resolved') else '❌ No'}",
                    ""
                ])

                if error.get('resolution_notes'):
                    report_lines.append(f"Resolution: {error['resolution_notes']}")
                    report_lines.append("")

                if error.get('source_file'):
                    report_lines.append(f"Source: {error['source_file']}:{error.get('source_line', '?')}")
                    report_lines.append("")

                report_lines.append("-" * 80)
                report_lines.append("")

            report_text = "\n".join(report_lines)

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(report_text)
                logger.info(f"✅ Error report exported to {output_file}")

            return report_text

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return f"Error generating report: {e}"

    def close(self):
        """Close the ledger (finalize)"""
        try:
            with open(self.ledger_file, "r") as f:
                ledger_data = json.load(f)

            ledger_data["metadata"]["completed_at"] = datetime.utcnow().isoformat() + "Z"

            with open(self.ledger_file, "w") as f:
                json.dump(ledger_data, f, indent=2)

            logger.info(f"✅ Error ledger closed - Run ID: {self.run_id}")

        except Exception as e:
            logger.error(f"Failed to close ledger: {e}")


# ============================================================================
# GLOBAL ERROR LEDGER INSTANCE
# ============================================================================

_error_ledger: Optional[ErrorLedger] = None


def get_error_ledger(run_id: Optional[str] = None) -> ErrorLedger:
    """
    Get or create global error ledger instance

    Args:
        run_id: Optional run ID (auto-generated if not provided)

    Returns:
        ErrorLedger instance
    """
    global _error_ledger

    if _error_ledger is None:
        _error_ledger = ErrorLedger(run_id=run_id)

    return _error_ledger


def log_error(
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs
) -> str:
    """
    Convenience function to log error to global ledger

    Args:
        error: Exception instance
        severity: Error severity level
        category: Error category
        **kwargs: Additional context

    Returns:
        Error ID
    """
    ledger = get_error_ledger()
    return ledger.log_error(error, severity, category, **kwargs)


# Export main components
__all__ = [
    "ErrorLedger",
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorEntry",
    "get_error_ledger",
    "log_error"
]
