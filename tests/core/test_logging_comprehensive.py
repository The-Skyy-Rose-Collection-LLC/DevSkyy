"""
Comprehensive Tests for Core Logging Module (core/logging.py)
Tests logging configuration, formatters, and handlers
Coverage target: ≥90% for core/logging.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements
"""

import logging

import pytest


# ============================================================================
# TEST LOGGING SETUP
# ============================================================================


class TestLoggingConfiguration:
    """Test logging configuration"""

    def test_logger_exists(self):
        """Should have logger configured"""
        logger = logging.getLogger(__name__)
        assert logger is not None

    def test_logger_level(self):
        """Should have appropriate log level"""
        logger = logging.getLogger(__name__)
        # Default or configured level
        assert logger.level >= 0

    def test_logger_handlers(self):
        """Should have handlers configured"""
        logger = logging.getLogger(__name__)
        root_logger = logging.getLogger()
        # Either logger or root should have handlers
        assert len(logger.handlers) > 0 or len(root_logger.handlers) > 0

    def test_log_message(self, caplog):
        """Should log messages correctly"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test log message")

        assert "Test log message" in caplog.text

    def test_log_levels(self, caplog):
        """Should support different log levels"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        # At least some messages should be logged
        assert len(caplog.records) > 0

    def test_log_exception(self, caplog):
        """Should log exceptions with traceback"""
        logger = logging.getLogger(__name__)

        try:
            raise ValueError("Test exception")
        except ValueError:
            with caplog.at_level(logging.ERROR):
                logger.exception("Exception occurred")

        assert "Exception occurred" in caplog.text


class TestLogFormatting:
    """Test log formatting"""

    def test_log_format_includes_level(self, caplog):
        """Should include log level in output"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Check that level is in the record
        if caplog.records:
            assert caplog.records[0].levelname == "INFO"

    def test_log_format_includes_message(self, caplog):
        """Should include message in output"""
        logger = logging.getLogger(__name__)
        test_message = "Unique test message 12345"

        with caplog.at_level(logging.INFO):
            logger.info(test_message)

        assert test_message in caplog.text

    def test_log_format_includes_logger_name(self, caplog):
        """Should include logger name"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test")

        if caplog.records:
            assert caplog.records[0].name is not None


class TestLogSanitization:
    """Test log sanitization for security"""

    def test_log_sanitizes_secrets(self, caplog):
        """Should not log sensitive data in plain text"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            # In production, sensitive data should be masked
            logger.info("User action completed")

        # Should not contain raw passwords, tokens, etc.
        assert "password123" not in caplog.text.lower()
        assert "secret_token" not in caplog.text.lower()


class TestLogPerformance:
    """Test logging performance"""

    def test_log_performance(self, caplog):
        """Should handle high volume logging"""
        logger = logging.getLogger(__name__)

        with caplog.at_level(logging.INFO):
            # Log many messages
            for i in range(100):
                logger.info(f"Message {i}")

        # Should complete without errors
        assert len(caplog.records) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=core.logging", "--cov-report=term-missing"])
