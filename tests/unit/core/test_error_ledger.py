"""
Unit Tests for Error Ledger System

Tests the ErrorLedger class including error logging, persistence,
statistics, filtering, and report generation.

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All
- Rule #10: No-Skip Rule - testing the error logging system itself
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.error_ledger import (
    ErrorCategory,
    ErrorEntry,
    ErrorLedger,
    ErrorSeverity,
    get_error_ledger,
    log_error,
)


# =============================================================================
# ErrorSeverity Enum Tests
# =============================================================================


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.INFO.value == "info"

    def test_severity_count(self):
        """Test that enum has 5 severity levels."""
        assert len(ErrorSeverity) == 5


# =============================================================================
# ErrorCategory Enum Tests
# =============================================================================


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.SECURITY.value == "security"
        assert ErrorCategory.UNKNOWN.value == "unknown"

    def test_category_count(self):
        """Test that enum has expected categories."""
        assert len(ErrorCategory) >= 10


# =============================================================================
# ErrorEntry Dataclass Tests
# =============================================================================


class TestErrorEntry:
    """Tests for ErrorEntry dataclass."""

    def test_create_error_entry(self):
        """Test creating an error entry."""
        entry = ErrorEntry(
            error_id="err-123",
            timestamp="2025-01-01T00:00:00Z",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            error_type="ConnectionError",
            error_message="Failed to connect to database"
        )

        assert entry.error_id == "err-123"
        assert entry.severity == ErrorSeverity.HIGH
        assert entry.category == ErrorCategory.DATABASE
        assert entry.error_type == "ConnectionError"
        assert entry.resolved is False

    def test_error_entry_with_context(self):
        """Test error entry with context."""
        entry = ErrorEntry(
            error_id="err-456",
            timestamp="2025-01-01T00:00:00Z",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            error_type="ValidationError",
            error_message="Invalid input",
            context={"field": "email", "value": "invalid"},
            correlation_id="req-123",
            user_id="user-001"
        )

        assert entry.context == {"field": "email", "value": "invalid"}
        assert entry.correlation_id == "req-123"
        assert entry.user_id == "user-001"

    def test_to_dict(self):
        """Test converting entry to dict."""
        entry = ErrorEntry(
            error_id="err-789",
            timestamp="2025-01-01T00:00:00Z",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.AGENT,
            error_type="AgentError",
            error_message="Agent failed"
        )

        result = entry.to_dict()

        assert result["error_id"] == "err-789"
        assert result["severity"] == "low"
        assert result["category"] == "agent"


# =============================================================================
# ErrorLedger Initialization Tests
# =============================================================================


class TestErrorLedgerInit:
    """Tests for ErrorLedger initialization."""

    def test_init_creates_artifacts_dir(self):
        """Test that init creates artifacts directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_path = os.path.join(tmpdir, "test_artifacts")
            ledger = ErrorLedger(artifacts_dir=artifacts_path)

            assert os.path.exists(artifacts_path)
            ledger.close()

    def test_init_creates_ledger_file(self):
        """Test that init creates ledger file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            assert ledger.ledger_file.exists()
            ledger.close()

    def test_init_with_custom_run_id(self):
        """Test init with custom run ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(run_id="custom-run-123", artifacts_dir=tmpdir)

            assert ledger.run_id == "custom-run-123"
            assert "custom-run-123" in str(ledger.ledger_file)
            ledger.close()

    def test_init_generates_run_id(self):
        """Test that init generates run ID if not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            assert ledger.run_id is not None
            assert len(ledger.run_id) > 0
            ledger.close()

    def test_init_captures_metadata(self):
        """Test that init captures metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            assert "run_id" in ledger.metadata
            assert "started_at" in ledger.metadata
            assert "platform" in ledger.metadata
            assert "python_version" in ledger.metadata
            ledger.close()


# =============================================================================
# Error Logging Tests
# =============================================================================


class TestErrorLogging:
    """Tests for error logging functionality."""

    @pytest.fixture
    def ledger(self):
        """Create a ledger for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)
            yield ledger
            ledger.close()

    def test_log_error_returns_id(self, ledger):
        """Test that log_error returns an error ID."""
        error = ValueError("Test error")

        error_id = ledger.log_error(error)

        assert error_id is not None
        assert len(error_id) > 0

    def test_log_error_adds_to_list(self, ledger):
        """Test that log_error adds to in-memory list."""
        error = ValueError("Test error")

        ledger.log_error(error)

        assert len(ledger.errors) == 1
        assert ledger.errors[0].error_message == "Test error"

    def test_log_error_with_severity(self, ledger):
        """Test logging error with custom severity."""
        error = ConnectionError("Connection failed")

        ledger.log_error(
            error,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.NETWORK
        )

        assert ledger.errors[0].severity == ErrorSeverity.CRITICAL
        assert ledger.errors[0].category == ErrorCategory.NETWORK

    def test_log_error_with_context(self, ledger):
        """Test logging error with context."""
        error = ValueError("Validation failed")

        ledger.log_error(
            error,
            context={"field": "email", "value": "bad@email"},
            correlation_id="req-123",
            user_id="user-001",
            endpoint="/api/users",
            method="POST"
        )

        entry = ledger.errors[0]
        assert entry.context == {"field": "email", "value": "bad@email"}
        assert entry.correlation_id == "req-123"
        assert entry.user_id == "user-001"
        assert entry.endpoint == "/api/users"
        assert entry.method == "POST"

    def test_log_error_captures_stack_trace(self, ledger):
        """Test that log_error captures stack trace."""
        try:
            raise ValueError("Test error with trace")
        except ValueError as e:
            ledger.log_error(e)

        assert ledger.errors[0].stack_trace is not None
        assert "ValueError" in ledger.errors[0].stack_trace

    def test_log_error_captures_source_info(self, ledger):
        """Test that log_error captures source file and line."""
        try:
            raise ValueError("Source info test")
        except ValueError as e:
            ledger.log_error(e)

        entry = ledger.errors[0]
        assert entry.source_file is not None
        assert entry.source_line is not None


# =============================================================================
# Error Persistence Tests
# =============================================================================


class TestErrorPersistence:
    """Tests for error persistence to file."""

    def test_error_persisted_to_file(self):
        """Test that errors are persisted to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)
            error = ValueError("Persistence test")

            ledger.log_error(error)

            with open(ledger.ledger_file) as f:
                data = json.load(f)

            assert len(data["errors"]) == 1
            assert data["errors"][0]["error_message"] == "Persistence test"
            ledger.close()

    def test_statistics_updated_on_persist(self):
        """Test that statistics are updated when persisting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("Error 1"), severity=ErrorSeverity.HIGH)
            ledger.log_error(ValueError("Error 2"), severity=ErrorSeverity.MEDIUM)

            with open(ledger.ledger_file) as f:
                data = json.load(f)

            assert data["statistics"]["total_errors"] == 2
            assert data["statistics"]["by_severity"]["high"] == 1
            assert data["statistics"]["by_severity"]["medium"] == 1
            ledger.close()


# =============================================================================
# Error Resolution Tests
# =============================================================================


class TestErrorResolution:
    """Tests for marking errors as resolved."""

    def test_mark_resolved(self):
        """Test marking an error as resolved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)
            error = ValueError("Resolvable error")
            error_id = ledger.log_error(error)

            ledger.mark_resolved(error_id, "Fixed by updating config")

            # Check in-memory
            assert ledger.errors[0].resolved is True
            assert ledger.errors[0].resolution_notes == "Fixed by updating config"

            # Check in file
            with open(ledger.ledger_file) as f:
                data = json.load(f)
            assert data["errors"][0]["resolved"] is True
            ledger.close()

    def test_resolved_count_updated(self):
        """Test that resolved count is updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            id1 = ledger.log_error(ValueError("Error 1"))
            ledger.log_error(ValueError("Error 2"))

            ledger.mark_resolved(id1, "Fixed")

            with open(ledger.ledger_file) as f:
                data = json.load(f)

            assert data["statistics"]["resolved_count"] == 1
            ledger.close()


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for error statistics."""

    def test_get_statistics(self):
        """Test getting statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("E1"), severity=ErrorSeverity.HIGH)
            ledger.log_error(ValueError("E2"), severity=ErrorSeverity.MEDIUM)
            ledger.log_error(ValueError("E3"), severity=ErrorSeverity.HIGH)

            stats = ledger.get_statistics()

            assert stats["total_errors"] == 3
            assert stats["by_severity"]["high"] == 2
            assert stats["by_severity"]["medium"] == 1
            ledger.close()

    def test_statistics_by_category(self):
        """Test statistics by category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("E1"), category=ErrorCategory.DATABASE)
            ledger.log_error(ValueError("E2"), category=ErrorCategory.NETWORK)
            ledger.log_error(ValueError("E3"), category=ErrorCategory.DATABASE)

            stats = ledger.get_statistics()

            assert stats["by_category"]["database"] == 2
            assert stats["by_category"]["network"] == 1
            ledger.close()


# =============================================================================
# Error Retrieval Tests
# =============================================================================


class TestErrorRetrieval:
    """Tests for retrieving errors with filtering."""

    def test_get_all_errors(self):
        """Test getting all errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("E1"))
            ledger.log_error(ValueError("E2"))
            ledger.log_error(ValueError("E3"))

            errors = ledger.get_errors()

            assert len(errors) == 3
            ledger.close()

    def test_filter_by_severity(self):
        """Test filtering errors by severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("E1"), severity=ErrorSeverity.HIGH)
            ledger.log_error(ValueError("E2"), severity=ErrorSeverity.MEDIUM)
            ledger.log_error(ValueError("E3"), severity=ErrorSeverity.HIGH)

            errors = ledger.get_errors(severity=ErrorSeverity.HIGH)

            assert len(errors) == 2
            ledger.close()

    def test_filter_by_category(self):
        """Test filtering errors by category."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("E1"), category=ErrorCategory.DATABASE)
            ledger.log_error(ValueError("E2"), category=ErrorCategory.NETWORK)

            errors = ledger.get_errors(category=ErrorCategory.DATABASE)

            assert len(errors) == 1
            assert errors[0]["category"] == "database"
            ledger.close()

    def test_filter_by_resolved(self):
        """Test filtering by resolution status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            id1 = ledger.log_error(ValueError("E1"))
            ledger.log_error(ValueError("E2"))

            ledger.mark_resolved(id1, "Fixed")

            resolved = ledger.get_errors(resolved=True)
            unresolved = ledger.get_errors(resolved=False)

            assert len(resolved) == 1
            assert len(unresolved) == 1
            ledger.close()

    def test_limit_results(self):
        """Test limiting results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            for i in range(10):
                ledger.log_error(ValueError(f"Error {i}"))

            errors = ledger.get_errors(limit=5)

            assert len(errors) == 5
            ledger.close()


# =============================================================================
# Report Generation Tests
# =============================================================================


class TestReportGeneration:
    """Tests for report generation."""

    def test_export_report(self):
        """Test exporting report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("Test error"), severity=ErrorSeverity.HIGH)

            report = ledger.export_report()

            assert "ERROR LEDGER REPORT" in report
            assert "STATISTICS" in report
            assert "HIGH" in report
            assert "Test error" in report
            ledger.close()

    def test_export_report_to_file(self):
        """Test exporting report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)
            output_file = os.path.join(tmpdir, "report.txt")

            ledger.log_error(ValueError("Test error"))
            ledger.export_report(output_file=output_file)

            assert os.path.exists(output_file)
            with open(output_file) as f:
                content = f.read()
            assert "ERROR LEDGER REPORT" in content
            ledger.close()


# =============================================================================
# Ledger Close Tests
# =============================================================================


class TestLedgerClose:
    """Tests for ledger close functionality."""

    def test_close_adds_completion_time(self):
        """Test that close adds completion time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.close()

            with open(ledger.ledger_file) as f:
                data = json.load(f)

            assert "completed_at" in data["metadata"]


# =============================================================================
# Global Functions Tests
# =============================================================================


class TestGlobalFunctions:
    """Tests for global helper functions."""

    def test_get_error_ledger_singleton(self):
        """Test get_error_ledger returns singleton."""
        with patch("core.error_ledger._error_ledger", None):
            ledger1 = get_error_ledger()
            ledger2 = get_error_ledger()

            # Same instance
            assert ledger1 is ledger2

    def test_log_error_global_function(self):
        """Test global log_error function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("core.error_ledger._error_ledger", None):
                with patch("core.error_ledger.ErrorLedger") as MockLedger:
                    mock_instance = MagicMock()
                    mock_instance.log_error.return_value = "error-123"
                    MockLedger.return_value = mock_instance

                    error = ValueError("Global test")
                    result = log_error(error, severity=ErrorSeverity.HIGH)

                    mock_instance.log_error.assert_called()


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_log_error_without_traceback(self):
        """Test logging error without traceback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            # Create error without raising
            error = ValueError("No traceback error")

            error_id = ledger.log_error(error)

            assert error_id is not None
            # Source info will be None since no traceback
            assert ledger.errors[0].source_file is None
            ledger.close()

    def test_empty_context(self):
        """Test logging with empty context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            ledger.log_error(ValueError("Test"), context={})

            assert ledger.errors[0].context == {}
            ledger.close()

    def test_large_error_message(self):
        """Test handling large error messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            large_message = "x" * 10000
            error = ValueError(large_message)

            error_id = ledger.log_error(error)

            assert error_id is not None
            assert len(ledger.errors[0].error_message) == 10000
            ledger.close()

    def test_special_characters_in_error(self):
        """Test handling special characters in error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            error = ValueError("Error with special chars: <script>alert('xss')</script>")

            error_id = ledger.log_error(error)

            assert error_id is not None
            ledger.close()

    def test_unicode_in_error(self):
        """Test handling unicode in error message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = ErrorLedger(artifacts_dir=tmpdir)

            error = ValueError("Unicode error: 中文 日本語 🎉")

            error_id = ledger.log_error(error)

            assert error_id is not None
            assert "中文" in ledger.errors[0].error_message
            ledger.close()
