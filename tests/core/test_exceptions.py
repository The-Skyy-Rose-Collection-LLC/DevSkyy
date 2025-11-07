"""
Unit tests for Core Exceptions

Tests custom exception classes and error mapping.
"""

import pytest

from core.exceptions import (
    DevSkyyError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    ExternalServiceError,
    RateLimitError,
    exception_from_status_code,
    map_database_error
)


class TestDevSkyyError:
    """Test base DevSkyyError class"""

    def test_error_creation(self):
        """Test creating base error"""
        error = DevSkyyError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "DevSkyyError"

    def test_error_with_custom_code(self):
        """Test error with custom error code"""
        error = DevSkyyError("Test", error_code="CUSTOM_001")
        
        assert error.error_code == "CUSTOM_001"

    def test_error_with_details(self):
        """Test error with additional details"""
        details = {"field": "username", "value": "test"}
        error = DevSkyyError("Test", details=details)
        
        assert error.details == details

    def test_error_with_original_error(self):
        """Test error wrapping original exception"""
        original = ValueError("Original error")
        error = DevSkyyError("Wrapped error", original_error=original)
        
        assert error.original_error == original

    def test_error_to_dict(self):
        """Test converting error to dictionary"""
        error = DevSkyyError(
            "Test message",
            error_code="TEST_001",
            details={"key": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "DevSkyyError"
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["message"] == "Test message"
        assert error_dict["details"]["key"] == "value"


class TestValidationError:
    """Test ValidationError class"""

    def test_validation_error(self):
        """Test validation error creation"""
        error = ValidationError("Invalid input")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "Invalid input"

    def test_validation_error_with_field(self):
        """Test validation error with field details"""
        error = ValidationError(
            "Invalid email",
            details={"field": "email", "value": "invalid"}
        )
        
        assert error.details["field"] == "email"


class TestAuthenticationError:
    """Test AuthenticationError class"""

    def test_authentication_error(self):
        """Test authentication error creation"""
        error = AuthenticationError("Invalid credentials")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "Invalid credentials"


class TestAuthorizationError:
    """Test AuthorizationError class"""

    def test_authorization_error(self):
        """Test authorization error creation"""
        error = AuthorizationError("Access denied")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "Access denied"


class TestResourceNotFoundError:
    """Test ResourceNotFoundError class"""

    def test_resource_not_found(self):
        """Test resource not found error"""
        error = ResourceNotFoundError("User not found")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "User not found"

    def test_resource_not_found_with_details(self):
        """Test resource not found with resource details"""
        error = ResourceNotFoundError(
            "Agent not found",
            details={"resource_type": "agent", "resource_id": "test_123"}
        )
        
        assert error.details["resource_type"] == "agent"
        assert error.details["resource_id"] == "test_123"


class TestDatabaseError:
    """Test DatabaseError class"""

    def test_database_error(self):
        """Test database error creation"""
        error = DatabaseError("Connection failed")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "Connection failed"

    def test_database_error_with_original(self):
        """Test database error wrapping original"""
        original = Exception("DB connection timeout")
        error = DatabaseError("Database unavailable", original_error=original)
        
        assert error.original_error == original


class TestExternalServiceError:
    """Test ExternalServiceError class"""

    def test_external_service_error(self):
        """Test external service error"""
        error = ExternalServiceError("API call failed")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "API call failed"


class TestRateLimitError:
    """Test RateLimitError class"""

    def test_rate_limit_error(self):
        """Test rate limit error"""
        error = RateLimitError("Too many requests")
        
        assert isinstance(error, DevSkyyError)
        assert str(error) == "Too many requests"

    def test_rate_limit_with_retry_after(self):
        """Test rate limit error with retry_after"""
        error = RateLimitError(
            "Rate limit exceeded",
            details={"retry_after": 60}
        )
        
        assert error.details["retry_after"] == 60


class TestExceptionMapping:
    """Test exception mapping utilities"""

    def test_exception_from_status_code_400(self):
        """Test mapping 400 to ValidationError"""
        error = exception_from_status_code(400, "Bad request")
        
        assert isinstance(error, ValidationError)
        assert str(error) == "Bad request"

    def test_exception_from_status_code_401(self):
        """Test mapping 401 to AuthenticationError"""
        error = exception_from_status_code(401, "Unauthorized")
        
        assert isinstance(error, AuthenticationError)

    def test_exception_from_status_code_403(self):
        """Test mapping 403 to AuthorizationError"""
        error = exception_from_status_code(403, "Forbidden")
        
        assert isinstance(error, AuthorizationError)

    def test_exception_from_status_code_404(self):
        """Test mapping 404 to ResourceNotFoundError"""
        error = exception_from_status_code(404, "Not found")
        
        assert isinstance(error, ResourceNotFoundError)

    def test_exception_from_status_code_429(self):
        """Test mapping 429 to RateLimitError"""
        error = exception_from_status_code(429, "Too many requests")
        
        assert isinstance(error, RateLimitError)

    def test_exception_from_status_code_500(self):
        """Test mapping 500 to DevSkyyError"""
        error = exception_from_status_code(500, "Internal error")
        
        assert isinstance(error, DevSkyyError)

    def test_exception_from_status_code_unknown(self):
        """Test mapping unknown status code"""
        error = exception_from_status_code(999, "Unknown error")
        
        assert isinstance(error, DevSkyyError)

    def test_exception_from_status_code_with_details(self):
        """Test status code mapping with details"""
        error = exception_from_status_code(
            400,
            "Invalid input",
            details={"field": "email"}
        )
        
        assert isinstance(error, ValidationError)
        assert error.details["field"] == "email"


class TestDatabaseErrorMapping:
    """Test database error mapping"""

    def test_map_database_error_connection(self):
        """Test mapping connection error"""
        error = map_database_error(
            "connection",
            "Failed to connect to database"
        )
        
        assert isinstance(error, DatabaseError)
        assert "connect" in str(error).lower()

    def test_map_database_error_with_original(self):
        """Test mapping with original exception"""
        original = Exception("Connection timeout")
        error = map_database_error(
            "timeout",
            "Database timeout",
            original_error=original
        )
        
        assert error.original_error == original


class TestErrorInheritance:
    """Test error class inheritance"""

    def test_all_errors_inherit_from_base(self):
        """Test all custom errors inherit from DevSkyyError"""
        assert issubclass(ValidationError, DevSkyyError)
        assert issubclass(AuthenticationError, DevSkyyError)
        assert issubclass(AuthorizationError, DevSkyyError)
        assert issubclass(ResourceNotFoundError, DevSkyyError)
        assert issubclass(DatabaseError, DevSkyyError)
        assert issubclass(ExternalServiceError, DevSkyyError)
        assert issubclass(RateLimitError, DevSkyyError)

    def test_all_errors_inherit_from_exception(self):
        """Test all errors are valid Python exceptions"""
        assert issubclass(DevSkyyError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(DatabaseError, Exception)