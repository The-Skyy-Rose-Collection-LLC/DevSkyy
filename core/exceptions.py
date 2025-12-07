"""
DevSkyy Custom Exceptions
Enterprise-grade exception hierarchy for specific error handling

Per Truth Protocol Rule #6: Replace broad 'except Exception' with specific types
Per Truth Protocol Rule #10: No-skip rule - Log all errors

This module provides a comprehensive exception hierarchy for the DevSkyy Platform,
enabling precise error handling and better debugging.
"""

from typing import Any


# ============================================================================
# BASE EXCEPTIONS
# ============================================================================


class DevSkyyError(Exception):
    """Base exception for all DevSkyy errors"""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ):
        """
        Initialize the exception with a human-readable message and optional metadata.

        Parameters:
            message (str): Human-readable description of the error.
            error_code (str | None): Unique machine-friendly error code; defaults to the exception class name when omitted.
            details (Optional[dict[str, Any]]): Additional structured metadata about the error; defaults to an empty dict when omitted.
            original_error (Exception | None): An underlying exception instance that caused this error, if any.
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a dictionary representation of the exception suitable for serialization.

        The returned dictionary includes:
        - `error_type`: the exception class name,
        - `error_code`: an optional machine-readable error code,
        - `message`: the human-readable error message,
        - `details`: additional context or metadata.

        Returns:
            mapping (dict[str, Any]): A dictionary with keys `error_type`, `error_code`, `message`, and `details`.
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# ============================================================================


class AuthenticationError(DevSkyyError):
    """Base authentication error"""


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid or malformed"""


class TokenMissingError(AuthenticationError):
    """JWT token is missing from request"""


class AuthorizationError(DevSkyyError):
    """Base authorization error"""


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""


class RoleRequiredError(AuthorizationError):
    """Specific role required but not assigned"""


# ============================================================================
# DATABASE EXCEPTIONS
# ============================================================================


class DatabaseError(DevSkyyError):
    """Base database error"""


class ConnectionError(DatabaseError):
    """Database connection failed"""


class QueryError(DatabaseError):
    """Database query failed"""


class TransactionError(DatabaseError):
    """Database transaction failed"""


class RecordNotFoundError(DatabaseError):
    """Database record not found"""


class DuplicateRecordError(DatabaseError):
    """Duplicate record constraint violation"""


class IntegrityError(DatabaseError):
    """Database integrity constraint violation"""


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================


class ValidationError(DevSkyyError):
    """Base validation error"""


class InvalidInputError(ValidationError):
    """Input data is invalid"""


class MissingFieldError(ValidationError):
    """Required field is missing"""


class InvalidFormatError(ValidationError):
    """Data format is invalid"""


class SchemaValidationError(ValidationError):
    """Schema validation failed"""


# ============================================================================
# NETWORK EXCEPTIONS
# ============================================================================


class NetworkError(DevSkyyError):
    """Base network error"""


class RequestTimeoutError(NetworkError):
    """Request timed out"""


class RequestFailedError(NetworkError):
    """HTTP request failed"""


class ConnectionTimeoutError(NetworkError):
    """Connection timed out"""


class ServiceUnavailableError(NetworkError):
    """External service unavailable"""


# ============================================================================
# BUSINESS LOGIC EXCEPTIONS
# ============================================================================


class BusinessLogicError(DevSkyyError):
    """Base business logic error"""


class InvalidStateError(BusinessLogicError):
    """Invalid state for operation"""


class OperationNotAllowedError(BusinessLogicError):
    """Operation not allowed in current context"""


class QuotaExceededError(BusinessLogicError):
    """Quota or limit exceeded"""


class ResourceConflictError(BusinessLogicError):
    """Resource conflict detected"""


# ============================================================================
# CONFIGURATION EXCEPTIONS
# ============================================================================


class ConfigurationError(DevSkyyError):
    """Base configuration error"""


class MissingConfigurationError(ConfigurationError):
    """Required configuration missing"""


class InvalidConfigurationError(ConfigurationError):
    """Configuration value is invalid"""


class EnvironmentError(ConfigurationError):
    """Environment variable error"""


# ============================================================================
# EXTERNAL API EXCEPTIONS
# ============================================================================


class ExternalAPIError(DevSkyyError):
    """Base external API error"""


class APIKeyMissingError(ExternalAPIError):
    """API key is missing"""


class APIKeyInvalidError(ExternalAPIError):
    """API key is invalid"""


class APIRateLimitError(ExternalAPIError):
    """API rate limit exceeded"""


class APIResponseError(ExternalAPIError):
    """API returned error response"""


# ============================================================================
# FILE SYSTEM EXCEPTIONS
# ============================================================================


class FileSystemError(DevSkyyError):
    """Base file system error"""


class FileNotFoundError(FileSystemError):
    """File not found"""


class FilePermissionError(FileSystemError):
    """Insufficient file permissions"""


class DiskSpaceError(FileSystemError):
    """Insufficient disk space"""


class FileCorruptedError(FileSystemError):
    """File is corrupted"""


# ============================================================================
# AGENT EXCEPTIONS
# ============================================================================


class AgentError(DevSkyyError):
    """Base agent error"""


class AgentNotFoundError(AgentError):
    """Agent not found"""


class AgentNotAvailableError(AgentError):
    """Agent not available"""


class AgentExecutionError(AgentError):
    """Agent execution failed"""


class AgentTimeoutError(AgentError):
    """Agent execution timed out"""


class AgentCircuitBreakerError(AgentError):
    """Agent circuit breaker is open"""


# ============================================================================
# ML/AI EXCEPTIONS
# ============================================================================


class MLError(DevSkyyError):
    """Base ML/AI error"""


class ModelNotFoundError(MLError):
    """ML model not found"""


class ModelLoadError(MLError):
    """Failed to load ML model"""


class PredictionError(MLError):
    """Prediction failed"""


class TrainingError(MLError):
    """Model training failed"""


class InvalidModelError(MLError):
    """Model is invalid or corrupted"""


# ============================================================================
# SECURITY EXCEPTIONS
# ============================================================================


class SecurityError(DevSkyyError):
    """Base security error"""


class EncryptionError(SecurityError):
    """Encryption operation failed"""


class DecryptionError(SecurityError):
    """Decryption operation failed"""


class HashingError(SecurityError):
    """Hashing operation failed"""


class SignatureError(SecurityError):
    """Signature verification failed"""


class SQLInjectionAttemptError(SecurityError):
    """SQL injection attempt detected"""


class XSSAttemptError(SecurityError):
    """XSS attempt detected"""


# ============================================================================
# PERFORMANCE EXCEPTIONS
# ============================================================================


class PerformanceError(DevSkyyError):
    """Base performance error"""


class PerformanceThresholdError(PerformanceError):
    """Performance threshold exceeded"""


class MemoryError(PerformanceError):
    """Memory limit exceeded"""


class CPUError(PerformanceError):
    """CPU limit exceeded"""


# ============================================================================
# GDPR/COMPLIANCE EXCEPTIONS
# ============================================================================


class ComplianceError(DevSkyyError):
    """Base compliance error"""


class GDPRViolationError(ComplianceError):
    """GDPR compliance violation"""


class DataRetentionError(ComplianceError):
    """Data retention policy violation"""


class ConsentError(ComplianceError):
    """User consent required but not given"""


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


def exception_from_status_code(status_code: int, message: str, **kwargs) -> DevSkyyError:
    """
    Map an HTTP status code to a corresponding DevSkyyError subclass and instantiate it.

    Selects the exception type associated with the provided HTTP status code and returns a new exception instance constructed with the given message and any additional keyword arguments. If the status code is not mapped, a DevSkyyError instance is returned.

    Parameters:
        status_code (int): HTTP status code to map to an exception class.
        message (str): Human-readable error message for the exception.
        **kwargs: Additional initialization parameters forwarded to the exception (e.g., `error_code`, `details`, `original_error`).

    Returns:
        DevSkyyError: An instance of the mapped DevSkyyError subclass; `DevSkyyError` if no mapping exists.
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


def map_database_error(error_type: str, message: str, original_error: Exception | None = None) -> DatabaseError:
    """
    Create an exception instance that represents a database error for a given error type.

    Parameters:
        error_type (str): Key identifying the database error category (used to select a specific DatabaseError subclass).
        message (str): Human-readable error message for the created exception.
        original_error (Exception | None): Original low-level exception to attach as context on the returned exception.

    Returns:
        DatabaseError: An instance of the DatabaseError subclass mapped from `error_type`, initialized with `message` and `original_error`.
    """
    exception_class = DATABASE_ERROR_MAPPING.get(error_type, DatabaseError)
    return exception_class(message, original_error=original_error)


# Export all exceptions
__all__ = [
    "APIKeyInvalidError",
    "APIKeyMissingError",
    "APIRateLimitError",
    "APIResponseError",
    "AgentCircuitBreakerError",
    # Agent
    "AgentError",
    "AgentExecutionError",
    "AgentNotAvailableError",
    "AgentNotFoundError",
    "AgentTimeoutError",
    # Authentication & Authorization
    "AuthenticationError",
    "AuthorizationError",
    # Business Logic
    "BusinessLogicError",
    "CPUError",
    # GDPR/Compliance
    "ComplianceError",
    # Configuration
    "ConfigurationError",
    "ConnectionError",
    "ConnectionTimeoutError",
    "ConsentError",
    "DataRetentionError",
    # Database
    "DatabaseError",
    "DecryptionError",
    # Base
    "DevSkyyError",
    "DiskSpaceError",
    "DuplicateRecordError",
    "EncryptionError",
    "EnvironmentError",
    # External API
    "ExternalAPIError",
    "FileCorruptedError",
    "FileNotFoundError",
    "FilePermissionError",
    # File System
    "FileSystemError",
    "GDPRViolationError",
    "HashingError",
    "InsufficientPermissionsError",
    "IntegrityError",
    "InvalidConfigurationError",
    "InvalidCredentialsError",
    "InvalidFormatError",
    "InvalidInputError",
    "InvalidModelError",
    "InvalidStateError",
    # ML/AI
    "MLError",
    "MemoryError",
    "MissingConfigurationError",
    "MissingFieldError",
    "ModelLoadError",
    "ModelNotFoundError",
    # Network
    "NetworkError",
    "OperationNotAllowedError",
    # Performance
    "PerformanceError",
    "PerformanceThresholdError",
    "PredictionError",
    "QueryError",
    "QuotaExceededError",
    "RecordNotFoundError",
    "RequestFailedError",
    "RequestTimeoutError",
    "ResourceConflictError",
    "RoleRequiredError",
    "SQLInjectionAttemptError",
    "SchemaValidationError",
    # Security
    "SecurityError",
    "ServiceUnavailableError",
    "SignatureError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenMissingError",
    "TrainingError",
    "TransactionError",
    # Validation
    "ValidationError",
    "XSSAttemptError",
    # Utilities
    "exception_from_status_code",
    "map_database_error",
]
