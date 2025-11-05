"""
DevSkyy Custom Exceptions
Enterprise-grade exception hierarchy for specific error handling

Per Truth Protocol Rule #6: Replace broad 'except Exception' with specific types
Per Truth Protocol Rule #10: No-skip rule - Log all errors

This module provides a comprehensive exception hierarchy for the DevSkyy Platform,
enabling precise error handling and better debugging.
"""

from typing import Any, Dict, Optional


# ============================================================================
# BASE EXCEPTIONS
# ============================================================================


class DevSkyyError(Exception):
    """Base exception for all DevSkyy errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# ============================================================================


class AuthenticationError(DevSkyyError):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid or malformed"""
    pass


class TokenMissingError(AuthenticationError):
    """JWT token is missing from request"""
    pass


class AuthorizationError(DevSkyyError):
    """Base authorization error"""
    pass


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""
    pass


class RoleRequiredError(AuthorizationError):
    """Specific role required but not assigned"""
    pass


# ============================================================================
# DATABASE EXCEPTIONS
# ============================================================================


class DatabaseError(DevSkyyError):
    """Base database error"""
    pass


class ConnectionError(DatabaseError):
    """Database connection failed"""
    pass


class QueryError(DatabaseError):
    """Database query failed"""
    pass


class TransactionError(DatabaseError):
    """Database transaction failed"""
    pass


class RecordNotFoundError(DatabaseError):
    """Database record not found"""
    pass


class DuplicateRecordError(DatabaseError):
    """Duplicate record constraint violation"""
    pass


class IntegrityError(DatabaseError):
    """Database integrity constraint violation"""
    pass


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================


class ValidationError(DevSkyyError):
    """Base validation error"""
    pass


class InvalidInputError(ValidationError):
    """Input data is invalid"""
    pass


class MissingFieldError(ValidationError):
    """Required field is missing"""
    pass


class InvalidFormatError(ValidationError):
    """Data format is invalid"""
    pass


class SchemaValidationError(ValidationError):
    """Schema validation failed"""
    pass


# ============================================================================
# NETWORK EXCEPTIONS
# ============================================================================


class NetworkError(DevSkyyError):
    """Base network error"""
    pass


class RequestTimeoutError(NetworkError):
    """Request timed out"""
    pass


class RequestFailedError(NetworkError):
    """HTTP request failed"""
    pass


class ConnectionTimeoutError(NetworkError):
    """Connection timed out"""
    pass


class ServiceUnavailableError(NetworkError):
    """External service unavailable"""
    pass


# ============================================================================
# BUSINESS LOGIC EXCEPTIONS
# ============================================================================


class BusinessLogicError(DevSkyyError):
    """Base business logic error"""
    pass


class InvalidStateError(BusinessLogicError):
    """Invalid state for operation"""
    pass


class OperationNotAllowedError(BusinessLogicError):
    """Operation not allowed in current context"""
    pass


class QuotaExceededError(BusinessLogicError):
    """Quota or limit exceeded"""
    pass


class ResourceConflictError(BusinessLogicError):
    """Resource conflict detected"""
    pass


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================


class ConfigurationError(DevSkyyError):
    """Base configuration error"""
    pass


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Configuration value is invalid"""
    pass


class EnvironmentError(ConfigurationError):
    """Environment variable error"""
    pass


# ============================================================================
# EXTERNAL API EXCEPTIONS
# ============================================================================


class ExternalAPIError(DevSkyyError):
    """Base external API error"""
    pass


class APIKeyMissingError(ExternalAPIError):
    """API key is missing"""
    pass


class APIKeyInvalidError(ExternalAPIError):
    """API key is invalid"""
    pass


class APIRateLimitError(ExternalAPIError):
    """API rate limit exceeded"""
    pass


class APIResponseError(ExternalAPIError):
    """API returned error response"""
    pass


# ============================================================================
# FILE SYSTEM EXCEPTIONS
# ============================================================================


class FileSystemError(DevSkyyError):
    """Base file system error"""
    pass


class FileNotFoundError(FileSystemError):
    """File not found"""
    pass


class FilePermissionError(FileSystemError):
    """Insufficient file permissions"""
    pass


class DiskSpaceError(FileSystemError):
    """Insufficient disk space"""
    pass


class FileCorruptedError(FileSystemError):
    """File is corrupted"""
    pass


# ============================================================================
# AGENT EXCEPTIONS
# ============================================================================


class AgentError(DevSkyyError):
    """Base agent error"""
    pass


class AgentNotFoundError(AgentError):
    """Agent not found"""
    pass


class AgentNotAvailableError(AgentError):
    """Agent not available"""
    pass


class AgentExecutionError(AgentError):
    """Agent execution failed"""
    pass


class AgentTimeoutError(AgentError):
    """Agent execution timed out"""
    pass


class AgentCircuitBreakerError(AgentError):
    """Agent circuit breaker is open"""
    pass


# ============================================================================
# ML/AI EXCEPTIONS
# ============================================================================


class MLError(DevSkyyError):
    """Base ML/AI error"""
    pass


class ModelNotFoundError(MLError):
    """ML model not found"""
    pass


class ModelLoadError(MLError):
    """Failed to load ML model"""
    pass


class PredictionError(MLError):
    """Prediction failed"""
    pass


class TrainingError(MLError):
    """Model training failed"""
    pass


class InvalidModelError(MLError):
    """Model is invalid or corrupted"""
    pass


# ============================================================================
# SECURITY EXCEPTIONS
# ============================================================================


class SecurityError(DevSkyyError):
    """Base security error"""
    pass


class EncryptionError(SecurityError):
    """Encryption operation failed"""
    pass


class DecryptionError(SecurityError):
    """Decryption operation failed"""
    pass


class HashingError(SecurityError):
    """Hashing operation failed"""
    pass


class SignatureError(SecurityError):
    """Signature verification failed"""
    pass


class SQLInjectionAttemptError(SecurityError):
    """SQL injection attempt detected"""
    pass


class XSSAttemptError(SecurityError):
    """XSS attempt detected"""
    pass


# ============================================================================
# PERFORMANCE EXCEPTIONS
# ============================================================================


class PerformanceError(DevSkyyError):
    """Base performance error"""
    pass


class PerformanceThresholdError(PerformanceError):
    """Performance threshold exceeded"""
    pass


class MemoryError(PerformanceError):
    """Memory limit exceeded"""
    pass


class CPUError(PerformanceError):
    """CPU limit exceeded"""
    pass


# ============================================================================
# GDPR/COMPLIANCE EXCEPTIONS
# ============================================================================


class ComplianceError(DevSkyyError):
    """Base compliance error"""
    pass


class GDPRViolationError(ComplianceError):
    """GDPR compliance violation"""
    pass


class DataRetentionError(ComplianceError):
    """Data retention policy violation"""
    pass


class ConsentError(ComplianceError):
    """User consent required but not given"""
    pass


# ============================================================================
# EXCEPTION MAPPING UTILITIES
# ============================================================================


# Map HTTP status codes to exception classes
HTTP_STATUS_TO_EXCEPTION = {
    400: InvalidInputError,
    401: InvalidCredentialsError,
    403: InsufficientPermissionsError,
    404: RecordNotFoundError,
    409: ResourceConflictError,
    422: ValidationError,
    429: APIRateLimitError,
    500: DevSkyyError,
    503: ServiceUnavailableError,
    504: RequestTimeoutError,
}


def exception_from_status_code(
    status_code: int,
    message: str,
    **kwargs
) -> DevSkyyError:
    """
    Create exception from HTTP status code

    Args:
        status_code: HTTP status code
        message: Error message
        **kwargs: Additional exception parameters

    Returns:
        DevSkyyError subclass instance
    """
    exception_class = HTTP_STATUS_TO_EXCEPTION.get(status_code, DevSkyyError)
    return exception_class(message, **kwargs)


# Map database error types to exception classes
DATABASE_ERROR_MAPPING = {
    "connection": ConnectionError,
    "query": QueryError,
    "transaction": TransactionError,
    "not_found": RecordNotFoundError,
    "duplicate": DuplicateRecordError,
    "integrity": IntegrityError,
}


def map_database_error(
    error_type: str,
    message: str,
    original_error: Optional[Exception] = None
) -> DatabaseError:
    """
    Map database error type to specific exception

    Args:
        error_type: Database error type
        message: Error message
        original_error: Original exception

    Returns:
        DatabaseError subclass instance
    """
    exception_class = DATABASE_ERROR_MAPPING.get(error_type, DatabaseError)
    return exception_class(message, original_error=original_error)


# Export all exceptions
__all__ = [
    # Base
    "DevSkyyError",

    # Authentication & Authorization
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenMissingError",
    "AuthorizationError",
    "InsufficientPermissionsError",
    "RoleRequiredError",

    # Database
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "TransactionError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "IntegrityError",

    # Validation
    "ValidationError",
    "InvalidInputError",
    "MissingFieldError",
    "InvalidFormatError",
    "SchemaValidationError",

    # Network
    "NetworkError",
    "RequestTimeoutError",
    "RequestFailedError",
    "ConnectionTimeoutError",
    "ServiceUnavailableError",

    # Business Logic
    "BusinessLogicError",
    "InvalidStateError",
    "OperationNotAllowedError",
    "QuotaExceededError",
    "ResourceConflictError",

    # Configuration
    "ConfigurationError",
    "MissingConfigurationError",
    "InvalidConfigurationError",
    "EnvironmentError",

    # External API
    "ExternalAPIError",
    "APIKeyMissingError",
    "APIKeyInvalidError",
    "APIRateLimitError",
    "APIResponseError",

    # File System
    "FileSystemError",
    "FileNotFoundError",
    "FilePermissionError",
    "DiskSpaceError",
    "FileCorruptedError",

    # Agent
    "AgentError",
    "AgentNotFoundError",
    "AgentNotAvailableError",
    "AgentExecutionError",
    "AgentTimeoutError",
    "AgentCircuitBreakerError",

    # ML/AI
    "MLError",
    "ModelNotFoundError",
    "ModelLoadError",
    "PredictionError",
    "TrainingError",
    "InvalidModelError",

    # Security
    "SecurityError",
    "EncryptionError",
    "DecryptionError",
    "HashingError",
    "SignatureError",
    "SQLInjectionAttemptError",
    "XSSAttemptError",

    # Performance
    "PerformanceError",
    "PerformanceThresholdError",
    "MemoryError",
    "CPUError",

    # GDPR/Compliance
    "ComplianceError",
    "GDPRViolationError",
    "DataRetentionError",
    "ConsentError",

    # Utilities
    "exception_from_status_code",
    "map_database_error",
]
