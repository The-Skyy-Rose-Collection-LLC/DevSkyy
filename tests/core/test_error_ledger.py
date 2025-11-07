"""
Unit tests for Error Ledger

Tests error logging, tracking, and persistence.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from core.error_ledger import (
    ErrorLedger,
    ErrorEntry,
    ErrorSeverity,
    ErrorCategory
)


class TestErrorEntry:
    """Test ErrorEntry dataclass"""

    def test_error_entry_creation(self):
        """Test creating an error entry"""
        entry = ErrorEntry(
            error_id="test_001",
            error_type="ValueError",
            error_message="Test error",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION_ERROR,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        assert entry.error_id == "test_001"
        assert entry.error_type == "ValueError"
        assert entry.severity == ErrorSeverity.MEDIUM

    def test_error_entry_to_dict(self):
        """Test converting error entry to dictionary"""
        entry = ErrorEntry(
            error_id="test_001",
            error_type="ValueError",
            error_message="Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.BUSINESS_LOGIC_ERROR,
            timestamp="2024-01-01T00:00:00Z"
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["error_id"] == "test_001"
        assert entry_dict["severity"] == "HIGH"
        assert entry_dict["category"] == "BUSINESS_LOGIC_ERROR"


class TestErrorLedger:
    """Test ErrorLedger class"""

    def test_ledger_initialization(self, tmp_path):
        """Test ledger initializes correctly"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        assert ledger.run_id is not None
        assert ledger.artifacts_dir == tmp_path
        assert ledger.ledger_file.exists()

    def test_ledger_with_custom_run_id(self, tmp_path):
        """Test ledger with custom run ID"""
        custom_id = "test_run_123"
        ledger = ErrorLedger(run_id=custom_id, artifacts_dir=str(tmp_path))
        
        assert ledger.run_id == custom_id

    def test_log_error(self, tmp_path):
        """Test logging an error"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        error = ValueError("Test error message")
        error_id = ledger.log_error(
            error=error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION_ERROR
        )
        
        assert error_id is not None
        assert len(ledger.errors) == 1
        assert ledger.errors[0].error_type == "ValueError"

    def test_log_error_with_context(self, tmp_path):
        """Test logging error with context"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        error = RuntimeError("Runtime error")
        context = {"user_id": "123", "action": "test"}
        
        error_id = ledger.log_error(
            error=error,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RUNTIME_ERROR,
            context=context
        )
        
        assert error_id is not None
        assert ledger.errors[0].context == context

    def test_log_error_with_correlation_id(self, tmp_path):
        """Test logging error with correlation ID"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        error = Exception("Test")
        ledger.log_error(
            error=error,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.EXTERNAL_SERVICE_ERROR,
            correlation_id="corr_123"
        )
        
        assert ledger.errors[0].correlation_id == "corr_123"

    def test_mark_resolved(self, tmp_path):
        """Test marking error as resolved"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        error = ValueError("Test")
        error_id = ledger.log_error(
            error=error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION_ERROR
        )
        
        ledger.mark_resolved(error_id, "Fixed by updating validation")
        
        resolved_error = next(e for e in ledger.errors if e.error_id == error_id)
        assert resolved_error.resolved is True
        assert resolved_error.resolution_notes == "Fixed by updating validation"

    def test_get_statistics(self, tmp_path):
        """Test getting ledger statistics"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        # Log multiple errors
        ledger.log_error(ValueError("1"), ErrorSeverity.HIGH, ErrorCategory.VALIDATION_ERROR)
        ledger.log_error(RuntimeError("2"), ErrorSeverity.MEDIUM, ErrorCategory.RUNTIME_ERROR)
        
        stats = ledger.get_statistics()
        
        assert "total_errors" in stats
        assert stats["total_errors"] >= 2

    def test_error_persistence(self, tmp_path):
        """Test errors are persisted to disk"""
        ledger = ErrorLedger(artifacts_dir=str(tmp_path))
        
        error = ValueError("Test error")
        ledger.log_error(error, ErrorSeverity.MEDIUM, ErrorCategory.VALIDATION_ERROR)
        
        # Read ledger file
        with open(ledger.ledger_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["errors"]) == 1
        assert data["errors"][0]["error_type"] == "ValueError"


class TestErrorSeverity:
    """Test ErrorSeverity enum"""

    def test_severity_levels(self):
        """Test severity levels are defined"""
        assert ErrorSeverity.LOW.value == "LOW"
        assert ErrorSeverity.MEDIUM.value == "MEDIUM"
        assert ErrorSeverity.HIGH.value == "HIGH"
        assert ErrorSeverity.CRITICAL.value == "CRITICAL"


class TestErrorCategory:
    """Test ErrorCategory enum"""

    def test_category_types(self):
        """Test error categories are defined"""
        assert ErrorCategory.VALIDATION_ERROR.value == "VALIDATION_ERROR"
        assert ErrorCategory.DATABASE_ERROR.value == "DATABASE_ERROR"
        assert ErrorCategory.RUNTIME_ERROR.value == "RUNTIME_ERROR"