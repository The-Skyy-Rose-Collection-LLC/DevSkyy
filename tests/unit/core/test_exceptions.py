"""
Unit tests for core/exceptions.py
Tests all custom exception classes, inheritance hierarchy, and utility functions

Per Truth Protocol Rule #8: Test Coverage ≥90%
Per Truth Protocol Rule #9: Document All (Google-style docstrings)
"""

import pytest

from core.exceptions import (
    # Base
    DevSkyyError,
    # Authentication & Authorization
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    TokenMissingError,
    AuthorizationError,
    InsufficientPermissionsError,
    RoleRequiredError,
    # Database
    DatabaseError,
    ConnectionError,
    QueryError,
    TransactionError,
    RecordNotFoundError,
    DuplicateRecordError,
    IntegrityError,
    # Validation
    ValidationError,
    InvalidInputError,
    MissingFieldError,
    InvalidFormatError,
    SchemaValidationError,
    # Network
    NetworkError,
    RequestTimeoutError,
    RequestFailedError,
    ConnectionTimeoutError,
    ServiceUnavailableError,
    # Business Logic
    BusinessLogicError,
    InvalidStateError,
    OperationNotAllowedError,
    QuotaExceededError,
    ResourceConflictError,
    # Configuration
    ConfigurationError,
    MissingConfigurationError,
    InvalidConfigurationError,
    EnvironmentError,
    # External API
    ExternalAPIError,
    APIKeyMissingError,
    APIKeyInvalidError,
    APIRateLimitError,
    APIResponseError,
    # File System
    FileSystemError,
    FileNotFoundError,
    FilePermissionError,
    DiskSpaceError,
    FileCorruptedError,
    # Agent
    AgentError,
    AgentNotFoundError,
    AgentNotAvailableError,
    AgentExecutionError,
    AgentTimeoutError,
    AgentCircuitBreakerError,
    # ML/AI
    MLError,
    ModelNotFoundError,
    ModelLoadError,
    PredictionError,
    TrainingError,
    InvalidModelError,
    # Security
    SecurityError,
    EncryptionError,
    DecryptionError,
    HashingError,
    SignatureError,
    SQLInjectionAttemptError,
    XSSAttemptError,
    # Performance
    PerformanceError,
    PerformanceThresholdError,
    MemoryError,
    CPUError,
    # Compliance
    ComplianceError,
    GDPRViolationError,
    DataRetentionError,
    ConsentError,
    # Utilities
    exception_from_status_code,
    map_database_error,
    HTTP_STATUS_TO_EXCEPTION,
    DATABASE_ERROR_MAPPING,
)


# ============================================================================
# BASE EXCEPTION TESTS
# ============================================================================


class TestDevSkyyError:
    """Test suite for DevSkyyError base exception class"""

    def test_default_initialization(self):
        """Test DevSkyyError initialization with only message"""
        # Arrange
        message = "Test error message"

        # Act
        error = DevSkyyError(message)

        # Assert
        assert error.message == message
        assert error.error_code == "DevSkyyError"
        assert error.details == {}
        assert error.original_error is None
        assert str(error) == message

    def test_initialization_with_error_code(self):
        """Test DevSkyyError initialization with custom error code"""
        # Arrange
        message = "Test error"
        error_code = "CUSTOM_ERROR_001"

        # Act
        error = DevSkyyError(message, error_code=error_code)

        # Assert
        assert error.message == message
        assert error.error_code == error_code
        assert error.details == {}
        assert error.original_error is None

    def test_initialization_with_details(self):
        """Test DevSkyyError initialization with details dictionary"""
        # Arrange
        message = "Test error"
        details = {"key1": "value1", "key2": 42, "nested": {"inner": "data"}}

        # Act
        error = DevSkyyError(message, details=details)

        # Assert
        assert error.message == message
        assert error.error_code == "DevSkyyError"
        assert error.details == details
        assert error.original_error is None

    def test_initialization_with_original_error(self):
        """Test DevSkyyError initialization with original error"""
        # Arrange
        message = "Wrapped error"
        original = ValueError("Original error message")

        # Act
        error = DevSkyyError(message, original_error=original)

        # Assert
        assert error.message == message
        assert error.error_code == "DevSkyyError"
        assert error.details == {}
        assert error.original_error is original

    def test_initialization_with_all_parameters(self):
        """Test DevSkyyError initialization with all parameters"""
        # Arrange
        message = "Complete error"
        error_code = "TEST_001"
        details = {"component": "test", "severity": "high"}
        original = RuntimeError("Root cause")

        # Act
        error = DevSkyyError(
            message, error_code=error_code, details=details, original_error=original
        )

        # Assert
        assert error.message == message
        assert error.error_code == error_code
        assert error.details == details
        assert error.original_error is original

    def test_to_dict_minimal(self):
        """Test to_dict() method with minimal initialization"""
        # Arrange
        message = "Test error"
        error = DevSkyyError(message)

        # Act
        result = error.to_dict()

        # Assert
        assert result == {
            "error_type": "DevSkyyError",
            "error_code": "DevSkyyError",
            "message": message,
            "details": {},
        }

    def test_to_dict_complete(self):
        """Test to_dict() method with all parameters"""
        # Arrange
        message = "Complete error"
        error_code = "TEST_002"
        details = {"field": "username", "reason": "invalid format"}
        error = DevSkyyError(message, error_code=error_code, details=details)

        # Act
        result = error.to_dict()

        # Assert
        assert result == {
            "error_type": "DevSkyyError",
            "error_code": error_code,
            "message": message,
            "details": details,
        }

    def test_error_code_defaults_to_class_name(self):
        """Test that error_code defaults to exception class name"""
        # Arrange & Act
        error = DevSkyyError("Test message")

        # Assert
        assert error.error_code == "DevSkyyError"

    def test_details_defaults_to_empty_dict(self):
        """Test that details defaults to empty dictionary"""
        # Arrange & Act
        error = DevSkyyError("Test message")

        # Assert
        assert error.details == {}
        assert isinstance(error.details, dict)

    def test_inherits_from_exception(self):
        """Test DevSkyyError inherits from base Exception"""
        # Arrange & Act
        error = DevSkyyError("Test")

        # Assert
        assert isinstance(error, Exception)

    def test_can_be_raised(self):
        """Test DevSkyyError can be raised and caught"""
        # Arrange & Act & Assert
        with pytest.raises(DevSkyyError) as exc_info:
            raise DevSkyyError("Test error")

        assert exc_info.value.message == "Test error"

    def test_string_representation(self):
        """Test string representation matches message"""
        # Arrange
        message = "Error message for display"
        error = DevSkyyError(message)

        # Act
        result = str(error)

        # Assert
        assert result == message


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTION TESTS
# ============================================================================


class TestAuthenticationExceptions:
    """Test suite for authentication exception hierarchy"""

    def test_authentication_error_inherits_from_devskyy_error(self):
        """Test AuthenticationError inherits from DevSkyyError"""
        # Arrange & Act
        error = AuthenticationError("Auth failed")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, AuthenticationError)

    def test_invalid_credentials_error_inherits_from_authentication_error(self):
        """Test InvalidCredentialsError inherits from AuthenticationError"""
        # Arrange & Act
        error = InvalidCredentialsError("Bad credentials")

        # Assert
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, DevSkyyError)
        assert error.error_code == "InvalidCredentialsError"

    def test_token_expired_error_inherits_from_authentication_error(self):
        """Test TokenExpiredError inherits from AuthenticationError"""
        # Arrange & Act
        error = TokenExpiredError("Token expired")

        # Assert
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, DevSkyyError)
        assert error.error_code == "TokenExpiredError"

    def test_token_invalid_error_inherits_from_authentication_error(self):
        """Test TokenInvalidError inherits from AuthenticationError"""
        # Arrange & Act
        error = TokenInvalidError("Invalid token")

        # Assert
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, DevSkyyError)

    def test_token_missing_error_inherits_from_authentication_error(self):
        """Test TokenMissingError inherits from AuthenticationError"""
        # Arrange & Act
        error = TokenMissingError("Token missing")

        # Assert
        assert isinstance(error, AuthenticationError)
        assert isinstance(error, DevSkyyError)


class TestAuthorizationExceptions:
    """Test suite for authorization exception hierarchy"""

    def test_authorization_error_inherits_from_devskyy_error(self):
        """Test AuthorizationError inherits from DevSkyyError"""
        # Arrange & Act
        error = AuthorizationError("Not authorized")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, AuthorizationError)

    def test_insufficient_permissions_error_inherits_from_authorization_error(self):
        """Test InsufficientPermissionsError inherits from AuthorizationError"""
        # Arrange & Act
        error = InsufficientPermissionsError("Insufficient permissions")

        # Assert
        assert isinstance(error, AuthorizationError)
        assert isinstance(error, DevSkyyError)

    def test_role_required_error_inherits_from_authorization_error(self):
        """Test RoleRequiredError inherits from AuthorizationError"""
        # Arrange & Act
        error = RoleRequiredError("Admin role required")

        # Assert
        assert isinstance(error, AuthorizationError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# DATABASE EXCEPTION TESTS
# ============================================================================


class TestDatabaseExceptions:
    """Test suite for database exception hierarchy"""

    def test_database_error_inherits_from_devskyy_error(self):
        """Test DatabaseError inherits from DevSkyyError"""
        # Arrange & Act
        error = DatabaseError("Database error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, DatabaseError)

    def test_connection_error_inherits_from_database_error(self):
        """Test ConnectionError inherits from DatabaseError"""
        # Arrange & Act
        error = ConnectionError("Connection failed")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)

    def test_query_error_inherits_from_database_error(self):
        """Test QueryError inherits from DatabaseError"""
        # Arrange & Act
        error = QueryError("Query failed")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)

    def test_transaction_error_inherits_from_database_error(self):
        """Test TransactionError inherits from DatabaseError"""
        # Arrange & Act
        error = TransactionError("Transaction failed")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)

    def test_record_not_found_error_inherits_from_database_error(self):
        """Test RecordNotFoundError inherits from DatabaseError"""
        # Arrange & Act
        error = RecordNotFoundError("Record not found")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)

    def test_duplicate_record_error_inherits_from_database_error(self):
        """Test DuplicateRecordError inherits from DatabaseError"""
        # Arrange & Act
        error = DuplicateRecordError("Duplicate record")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)

    def test_integrity_error_inherits_from_database_error(self):
        """Test IntegrityError inherits from DatabaseError"""
        # Arrange & Act
        error = IntegrityError("Integrity constraint violated")

        # Assert
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# VALIDATION EXCEPTION TESTS
# ============================================================================


class TestValidationExceptions:
    """Test suite for validation exception hierarchy"""

    def test_validation_error_inherits_from_devskyy_error(self):
        """Test ValidationError inherits from DevSkyyError"""
        # Arrange & Act
        error = ValidationError("Validation failed")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, ValidationError)

    def test_invalid_input_error_inherits_from_validation_error(self):
        """Test InvalidInputError inherits from ValidationError"""
        # Arrange & Act
        error = InvalidInputError("Invalid input")

        # Assert
        assert isinstance(error, ValidationError)
        assert isinstance(error, DevSkyyError)

    def test_missing_field_error_inherits_from_validation_error(self):
        """Test MissingFieldError inherits from ValidationError"""
        # Arrange & Act
        error = MissingFieldError("Field missing")

        # Assert
        assert isinstance(error, ValidationError)
        assert isinstance(error, DevSkyyError)

    def test_invalid_format_error_inherits_from_validation_error(self):
        """Test InvalidFormatError inherits from ValidationError"""
        # Arrange & Act
        error = InvalidFormatError("Invalid format")

        # Assert
        assert isinstance(error, ValidationError)
        assert isinstance(error, DevSkyyError)

    def test_schema_validation_error_inherits_from_validation_error(self):
        """Test SchemaValidationError inherits from ValidationError"""
        # Arrange & Act
        error = SchemaValidationError("Schema validation failed")

        # Assert
        assert isinstance(error, ValidationError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# NETWORK EXCEPTION TESTS
# ============================================================================


class TestNetworkExceptions:
    """Test suite for network exception hierarchy"""

    def test_network_error_inherits_from_devskyy_error(self):
        """Test NetworkError inherits from DevSkyyError"""
        # Arrange & Act
        error = NetworkError("Network error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, NetworkError)

    def test_request_timeout_error_inherits_from_network_error(self):
        """Test RequestTimeoutError inherits from NetworkError"""
        # Arrange & Act
        error = RequestTimeoutError("Request timed out")

        # Assert
        assert isinstance(error, NetworkError)
        assert isinstance(error, DevSkyyError)

    def test_request_failed_error_inherits_from_network_error(self):
        """Test RequestFailedError inherits from NetworkError"""
        # Arrange & Act
        error = RequestFailedError("Request failed")

        # Assert
        assert isinstance(error, NetworkError)
        assert isinstance(error, DevSkyyError)

    def test_connection_timeout_error_inherits_from_network_error(self):
        """Test ConnectionTimeoutError inherits from NetworkError"""
        # Arrange & Act
        error = ConnectionTimeoutError("Connection timed out")

        # Assert
        assert isinstance(error, NetworkError)
        assert isinstance(error, DevSkyyError)

    def test_service_unavailable_error_inherits_from_network_error(self):
        """Test ServiceUnavailableError inherits from NetworkError"""
        # Arrange & Act
        error = ServiceUnavailableError("Service unavailable")

        # Assert
        assert isinstance(error, NetworkError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# BUSINESS LOGIC EXCEPTION TESTS
# ============================================================================


class TestBusinessLogicExceptions:
    """Test suite for business logic exception hierarchy"""

    def test_business_logic_error_inherits_from_devskyy_error(self):
        """Test BusinessLogicError inherits from DevSkyyError"""
        # Arrange & Act
        error = BusinessLogicError("Business logic error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, BusinessLogicError)

    def test_invalid_state_error_inherits_from_business_logic_error(self):
        """Test InvalidStateError inherits from BusinessLogicError"""
        # Arrange & Act
        error = InvalidStateError("Invalid state")

        # Assert
        assert isinstance(error, BusinessLogicError)
        assert isinstance(error, DevSkyyError)

    def test_operation_not_allowed_error_inherits_from_business_logic_error(self):
        """Test OperationNotAllowedError inherits from BusinessLogicError"""
        # Arrange & Act
        error = OperationNotAllowedError("Operation not allowed")

        # Assert
        assert isinstance(error, BusinessLogicError)
        assert isinstance(error, DevSkyyError)

    def test_quota_exceeded_error_inherits_from_business_logic_error(self):
        """Test QuotaExceededError inherits from BusinessLogicError"""
        # Arrange & Act
        error = QuotaExceededError("Quota exceeded")

        # Assert
        assert isinstance(error, BusinessLogicError)
        assert isinstance(error, DevSkyyError)

    def test_resource_conflict_error_inherits_from_business_logic_error(self):
        """Test ResourceConflictError inherits from BusinessLogicError"""
        # Arrange & Act
        error = ResourceConflictError("Resource conflict")

        # Assert
        assert isinstance(error, BusinessLogicError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# CONFIGURATION EXCEPTION TESTS
# ============================================================================


class TestConfigurationExceptions:
    """Test suite for configuration exception hierarchy"""

    def test_configuration_error_inherits_from_devskyy_error(self):
        """Test ConfigurationError inherits from DevSkyyError"""
        # Arrange & Act
        error = ConfigurationError("Configuration error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, ConfigurationError)

    def test_missing_configuration_error_inherits_from_configuration_error(self):
        """Test MissingConfigurationError inherits from ConfigurationError"""
        # Arrange & Act
        error = MissingConfigurationError("Config missing")

        # Assert
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, DevSkyyError)

    def test_invalid_configuration_error_inherits_from_configuration_error(self):
        """Test InvalidConfigurationError inherits from ConfigurationError"""
        # Arrange & Act
        error = InvalidConfigurationError("Invalid config")

        # Assert
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, DevSkyyError)

    def test_environment_error_inherits_from_configuration_error(self):
        """Test EnvironmentError inherits from ConfigurationError"""
        # Arrange & Act
        error = EnvironmentError("Environment error")

        # Assert
        assert isinstance(error, ConfigurationError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# EXTERNAL API EXCEPTION TESTS
# ============================================================================


class TestExternalAPIExceptions:
    """Test suite for external API exception hierarchy"""

    def test_external_api_error_inherits_from_devskyy_error(self):
        """Test ExternalAPIError inherits from DevSkyyError"""
        # Arrange & Act
        error = ExternalAPIError("API error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, ExternalAPIError)

    def test_api_key_missing_error_inherits_from_external_api_error(self):
        """Test APIKeyMissingError inherits from ExternalAPIError"""
        # Arrange & Act
        error = APIKeyMissingError("API key missing")

        # Assert
        assert isinstance(error, ExternalAPIError)
        assert isinstance(error, DevSkyyError)

    def test_api_key_invalid_error_inherits_from_external_api_error(self):
        """Test APIKeyInvalidError inherits from ExternalAPIError"""
        # Arrange & Act
        error = APIKeyInvalidError("API key invalid")

        # Assert
        assert isinstance(error, ExternalAPIError)
        assert isinstance(error, DevSkyyError)

    def test_api_rate_limit_error_inherits_from_external_api_error(self):
        """Test APIRateLimitError inherits from ExternalAPIError"""
        # Arrange & Act
        error = APIRateLimitError("Rate limit exceeded")

        # Assert
        assert isinstance(error, ExternalAPIError)
        assert isinstance(error, DevSkyyError)

    def test_api_response_error_inherits_from_external_api_error(self):
        """Test APIResponseError inherits from ExternalAPIError"""
        # Arrange & Act
        error = APIResponseError("API returned error")

        # Assert
        assert isinstance(error, ExternalAPIError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# FILE SYSTEM EXCEPTION TESTS
# ============================================================================


class TestFileSystemExceptions:
    """Test suite for file system exception hierarchy"""

    def test_file_system_error_inherits_from_devskyy_error(self):
        """Test FileSystemError inherits from DevSkyyError"""
        # Arrange & Act
        error = FileSystemError("File system error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, FileSystemError)

    def test_file_not_found_error_inherits_from_file_system_error(self):
        """Test FileNotFoundError inherits from FileSystemError"""
        # Arrange & Act
        error = FileNotFoundError("File not found")

        # Assert
        assert isinstance(error, FileSystemError)
        assert isinstance(error, DevSkyyError)

    def test_file_permission_error_inherits_from_file_system_error(self):
        """Test FilePermissionError inherits from FileSystemError"""
        # Arrange & Act
        error = FilePermissionError("Permission denied")

        # Assert
        assert isinstance(error, FileSystemError)
        assert isinstance(error, DevSkyyError)

    def test_disk_space_error_inherits_from_file_system_error(self):
        """Test DiskSpaceError inherits from FileSystemError"""
        # Arrange & Act
        error = DiskSpaceError("Disk space error")

        # Assert
        assert isinstance(error, FileSystemError)
        assert isinstance(error, DevSkyyError)

    def test_file_corrupted_error_inherits_from_file_system_error(self):
        """Test FileCorruptedError inherits from FileSystemError"""
        # Arrange & Act
        error = FileCorruptedError("File corrupted")

        # Assert
        assert isinstance(error, FileSystemError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# AGENT EXCEPTION TESTS
# ============================================================================


class TestAgentExceptions:
    """Test suite for agent exception hierarchy"""

    def test_agent_error_inherits_from_devskyy_error(self):
        """Test AgentError inherits from DevSkyyError"""
        # Arrange & Act
        error = AgentError("Agent error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, AgentError)

    def test_agent_not_found_error_inherits_from_agent_error(self):
        """Test AgentNotFoundError inherits from AgentError"""
        # Arrange & Act
        error = AgentNotFoundError("Agent not found")

        # Assert
        assert isinstance(error, AgentError)
        assert isinstance(error, DevSkyyError)

    def test_agent_not_available_error_inherits_from_agent_error(self):
        """Test AgentNotAvailableError inherits from AgentError"""
        # Arrange & Act
        error = AgentNotAvailableError("Agent not available")

        # Assert
        assert isinstance(error, AgentError)
        assert isinstance(error, DevSkyyError)

    def test_agent_execution_error_inherits_from_agent_error(self):
        """Test AgentExecutionError inherits from AgentError"""
        # Arrange & Act
        error = AgentExecutionError("Execution failed")

        # Assert
        assert isinstance(error, AgentError)
        assert isinstance(error, DevSkyyError)

    def test_agent_timeout_error_inherits_from_agent_error(self):
        """Test AgentTimeoutError inherits from AgentError"""
        # Arrange & Act
        error = AgentTimeoutError("Agent timed out")

        # Assert
        assert isinstance(error, AgentError)
        assert isinstance(error, DevSkyyError)

    def test_agent_circuit_breaker_error_inherits_from_agent_error(self):
        """Test AgentCircuitBreakerError inherits from AgentError"""
        # Arrange & Act
        error = AgentCircuitBreakerError("Circuit breaker open")

        # Assert
        assert isinstance(error, AgentError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# ML/AI EXCEPTION TESTS
# ============================================================================


class TestMLExceptions:
    """Test suite for ML/AI exception hierarchy"""

    def test_ml_error_inherits_from_devskyy_error(self):
        """Test MLError inherits from DevSkyyError"""
        # Arrange & Act
        error = MLError("ML error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, MLError)

    def test_model_not_found_error_inherits_from_ml_error(self):
        """Test ModelNotFoundError inherits from MLError"""
        # Arrange & Act
        error = ModelNotFoundError("Model not found")

        # Assert
        assert isinstance(error, MLError)
        assert isinstance(error, DevSkyyError)

    def test_model_load_error_inherits_from_ml_error(self):
        """Test ModelLoadError inherits from MLError"""
        # Arrange & Act
        error = ModelLoadError("Failed to load model")

        # Assert
        assert isinstance(error, MLError)
        assert isinstance(error, DevSkyyError)

    def test_prediction_error_inherits_from_ml_error(self):
        """Test PredictionError inherits from MLError"""
        # Arrange & Act
        error = PredictionError("Prediction failed")

        # Assert
        assert isinstance(error, MLError)
        assert isinstance(error, DevSkyyError)

    def test_training_error_inherits_from_ml_error(self):
        """Test TrainingError inherits from MLError"""
        # Arrange & Act
        error = TrainingError("Training failed")

        # Assert
        assert isinstance(error, MLError)
        assert isinstance(error, DevSkyyError)

    def test_invalid_model_error_inherits_from_ml_error(self):
        """Test InvalidModelError inherits from MLError"""
        # Arrange & Act
        error = InvalidModelError("Invalid model")

        # Assert
        assert isinstance(error, MLError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# SECURITY EXCEPTION TESTS
# ============================================================================


class TestSecurityExceptions:
    """Test suite for security exception hierarchy"""

    def test_security_error_inherits_from_devskyy_error(self):
        """Test SecurityError inherits from DevSkyyError"""
        # Arrange & Act
        error = SecurityError("Security error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, SecurityError)

    def test_encryption_error_inherits_from_security_error(self):
        """Test EncryptionError inherits from SecurityError"""
        # Arrange & Act
        error = EncryptionError("Encryption failed")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)

    def test_decryption_error_inherits_from_security_error(self):
        """Test DecryptionError inherits from SecurityError"""
        # Arrange & Act
        error = DecryptionError("Decryption failed")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)

    def test_hashing_error_inherits_from_security_error(self):
        """Test HashingError inherits from SecurityError"""
        # Arrange & Act
        error = HashingError("Hashing failed")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)

    def test_signature_error_inherits_from_security_error(self):
        """Test SignatureError inherits from SecurityError"""
        # Arrange & Act
        error = SignatureError("Signature verification failed")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)

    def test_sql_injection_attempt_error_inherits_from_security_error(self):
        """Test SQLInjectionAttemptError inherits from SecurityError"""
        # Arrange & Act
        error = SQLInjectionAttemptError("SQL injection detected")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)

    def test_xss_attempt_error_inherits_from_security_error(self):
        """Test XSSAttemptError inherits from SecurityError"""
        # Arrange & Act
        error = XSSAttemptError("XSS attempt detected")

        # Assert
        assert isinstance(error, SecurityError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# PERFORMANCE EXCEPTION TESTS
# ============================================================================


class TestPerformanceExceptions:
    """Test suite for performance exception hierarchy"""

    def test_performance_error_inherits_from_devskyy_error(self):
        """Test PerformanceError inherits from DevSkyyError"""
        # Arrange & Act
        error = PerformanceError("Performance error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, PerformanceError)

    def test_performance_threshold_error_inherits_from_performance_error(self):
        """Test PerformanceThresholdError inherits from PerformanceError"""
        # Arrange & Act
        error = PerformanceThresholdError("Threshold exceeded")

        # Assert
        assert isinstance(error, PerformanceError)
        assert isinstance(error, DevSkyyError)

    def test_memory_error_inherits_from_performance_error(self):
        """Test MemoryError inherits from PerformanceError"""
        # Arrange & Act
        error = MemoryError("Memory limit exceeded")

        # Assert
        assert isinstance(error, PerformanceError)
        assert isinstance(error, DevSkyyError)

    def test_cpu_error_inherits_from_performance_error(self):
        """Test CPUError inherits from PerformanceError"""
        # Arrange & Act
        error = CPUError("CPU limit exceeded")

        # Assert
        assert isinstance(error, PerformanceError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# COMPLIANCE EXCEPTION TESTS
# ============================================================================


class TestComplianceExceptions:
    """Test suite for compliance exception hierarchy"""

    def test_compliance_error_inherits_from_devskyy_error(self):
        """Test ComplianceError inherits from DevSkyyError"""
        # Arrange & Act
        error = ComplianceError("Compliance error")

        # Assert
        assert isinstance(error, DevSkyyError)
        assert isinstance(error, ComplianceError)

    def test_gdpr_violation_error_inherits_from_compliance_error(self):
        """Test GDPRViolationError inherits from ComplianceError"""
        # Arrange & Act
        error = GDPRViolationError("GDPR violation")

        # Assert
        assert isinstance(error, ComplianceError)
        assert isinstance(error, DevSkyyError)

    def test_data_retention_error_inherits_from_compliance_error(self):
        """Test DataRetentionError inherits from ComplianceError"""
        # Arrange & Act
        error = DataRetentionError("Data retention violation")

        # Assert
        assert isinstance(error, ComplianceError)
        assert isinstance(error, DevSkyyError)

    def test_consent_error_inherits_from_compliance_error(self):
        """Test ConsentError inherits from ComplianceError"""
        # Arrange & Act
        error = ConsentError("Consent required")

        # Assert
        assert isinstance(error, ComplianceError)
        assert isinstance(error, DevSkyyError)


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================


class TestExceptionFromStatusCode:
    """Test suite for exception_from_status_code utility function"""

    def test_status_400_returns_invalid_input_error(self):
        """Test status code 400 maps to InvalidInputError"""
        # Arrange
        message = "Bad request"

        # Act
        error = exception_from_status_code(400, message)

        # Assert
        assert isinstance(error, InvalidInputError)
        assert error.message == message

    def test_status_401_returns_invalid_credentials_error(self):
        """Test status code 401 maps to InvalidCredentialsError"""
        # Arrange
        message = "Unauthorized"

        # Act
        error = exception_from_status_code(401, message)

        # Assert
        assert isinstance(error, InvalidCredentialsError)
        assert error.message == message

    def test_status_403_returns_insufficient_permissions_error(self):
        """Test status code 403 maps to InsufficientPermissionsError"""
        # Arrange
        message = "Forbidden"

        # Act
        error = exception_from_status_code(403, message)

        # Assert
        assert isinstance(error, InsufficientPermissionsError)
        assert error.message == message

    def test_status_404_returns_record_not_found_error(self):
        """Test status code 404 maps to RecordNotFoundError"""
        # Arrange
        message = "Not found"

        # Act
        error = exception_from_status_code(404, message)

        # Assert
        assert isinstance(error, RecordNotFoundError)
        assert error.message == message

    def test_status_409_returns_resource_conflict_error(self):
        """Test status code 409 maps to ResourceConflictError"""
        # Arrange
        message = "Conflict"

        # Act
        error = exception_from_status_code(409, message)

        # Assert
        assert isinstance(error, ResourceConflictError)
        assert error.message == message

    def test_status_422_returns_validation_error(self):
        """Test status code 422 maps to ValidationError"""
        # Arrange
        message = "Unprocessable entity"

        # Act
        error = exception_from_status_code(422, message)

        # Assert
        assert isinstance(error, ValidationError)
        assert error.message == message

    def test_status_429_returns_api_rate_limit_error(self):
        """Test status code 429 maps to APIRateLimitError"""
        # Arrange
        message = "Too many requests"

        # Act
        error = exception_from_status_code(429, message)

        # Assert
        assert isinstance(error, APIRateLimitError)
        assert error.message == message

    def test_status_500_returns_devskyy_error(self):
        """Test status code 500 maps to DevSkyyError"""
        # Arrange
        message = "Internal server error"

        # Act
        error = exception_from_status_code(500, message)

        # Assert
        assert isinstance(error, DevSkyyError)
        assert error.message == message

    def test_status_503_returns_service_unavailable_error(self):
        """Test status code 503 maps to ServiceUnavailableError"""
        # Arrange
        message = "Service unavailable"

        # Act
        error = exception_from_status_code(503, message)

        # Assert
        assert isinstance(error, ServiceUnavailableError)
        assert error.message == message

    def test_status_504_returns_request_timeout_error(self):
        """Test status code 504 maps to RequestTimeoutError"""
        # Arrange
        message = "Gateway timeout"

        # Act
        error = exception_from_status_code(504, message)

        # Assert
        assert isinstance(error, RequestTimeoutError)
        assert error.message == message

    def test_unmapped_status_code_returns_devskyy_error(self):
        """Test unmapped status code returns DevSkyyError"""
        # Arrange
        message = "Unknown error"

        # Act
        error = exception_from_status_code(599, message)

        # Assert
        assert isinstance(error, DevSkyyError)
        assert error.message == message

    def test_with_error_code_parameter(self):
        """Test exception_from_status_code with error_code parameter"""
        # Arrange
        message = "Bad request"
        error_code = "CUSTOM_400"

        # Act
        error = exception_from_status_code(400, message, error_code=error_code)

        # Assert
        assert isinstance(error, InvalidInputError)
        assert error.message == message
        assert error.error_code == error_code

    def test_with_details_parameter(self):
        """Test exception_from_status_code with details parameter"""
        # Arrange
        message = "Validation failed"
        details = {"field": "email", "reason": "invalid format"}

        # Act
        error = exception_from_status_code(422, message, details=details)

        # Assert
        assert isinstance(error, ValidationError)
        assert error.message == message
        assert error.details == details

    def test_with_original_error_parameter(self):
        """Test exception_from_status_code with original_error parameter"""
        # Arrange
        message = "Database error"
        original = ValueError("Connection lost")

        # Act
        error = exception_from_status_code(500, message, original_error=original)

        # Assert
        assert isinstance(error, DevSkyyError)
        assert error.message == message
        assert error.original_error is original

    def test_with_all_parameters(self):
        """Test exception_from_status_code with all parameters"""
        # Arrange
        message = "Complete error"
        error_code = "ERR_404"
        details = {"resource": "user", "id": "123"}
        original = RuntimeError("Root cause")

        # Act
        error = exception_from_status_code(
            404, message, error_code=error_code, details=details, original_error=original
        )

        # Assert
        assert isinstance(error, RecordNotFoundError)
        assert error.message == message
        assert error.error_code == error_code
        assert error.details == details
        assert error.original_error is original

    def test_http_status_to_exception_mapping_completeness(self):
        """Test HTTP_STATUS_TO_EXCEPTION contains expected mappings"""
        # Arrange & Act & Assert
        assert 400 in HTTP_STATUS_TO_EXCEPTION
        assert 401 in HTTP_STATUS_TO_EXCEPTION
        assert 403 in HTTP_STATUS_TO_EXCEPTION
        assert 404 in HTTP_STATUS_TO_EXCEPTION
        assert 409 in HTTP_STATUS_TO_EXCEPTION
        assert 422 in HTTP_STATUS_TO_EXCEPTION
        assert 429 in HTTP_STATUS_TO_EXCEPTION
        assert 500 in HTTP_STATUS_TO_EXCEPTION
        assert 503 in HTTP_STATUS_TO_EXCEPTION
        assert 504 in HTTP_STATUS_TO_EXCEPTION


class TestMapDatabaseError:
    """Test suite for map_database_error utility function"""

    def test_connection_error_type(self):
        """Test 'connection' error type maps to ConnectionError"""
        # Arrange
        message = "Failed to connect"

        # Act
        error = map_database_error("connection", message)

        # Assert
        assert isinstance(error, ConnectionError)
        assert error.message == message

    def test_query_error_type(self):
        """Test 'query' error type maps to QueryError"""
        # Arrange
        message = "Query failed"

        # Act
        error = map_database_error("query", message)

        # Assert
        assert isinstance(error, QueryError)
        assert error.message == message

    def test_transaction_error_type(self):
        """Test 'transaction' error type maps to TransactionError"""
        # Arrange
        message = "Transaction failed"

        # Act
        error = map_database_error("transaction", message)

        # Assert
        assert isinstance(error, TransactionError)
        assert error.message == message

    def test_not_found_error_type(self):
        """Test 'not_found' error type maps to RecordNotFoundError"""
        # Arrange
        message = "Record not found"

        # Act
        error = map_database_error("not_found", message)

        # Assert
        assert isinstance(error, RecordNotFoundError)
        assert error.message == message

    def test_duplicate_error_type(self):
        """Test 'duplicate' error type maps to DuplicateRecordError"""
        # Arrange
        message = "Duplicate key"

        # Act
        error = map_database_error("duplicate", message)

        # Assert
        assert isinstance(error, DuplicateRecordError)
        assert error.message == message

    def test_integrity_error_type(self):
        """Test 'integrity' error type maps to IntegrityError"""
        # Arrange
        message = "Integrity constraint violated"

        # Act
        error = map_database_error("integrity", message)

        # Assert
        assert isinstance(error, IntegrityError)
        assert error.message == message

    def test_unmapped_error_type_returns_database_error(self):
        """Test unmapped error type returns DatabaseError"""
        # Arrange
        message = "Unknown database error"

        # Act
        error = map_database_error("unknown", message)

        # Assert
        assert isinstance(error, DatabaseError)
        assert type(error) == DatabaseError
        assert error.message == message

    def test_with_original_error(self):
        """Test map_database_error with original_error parameter"""
        # Arrange
        message = "Connection failed"
        original = RuntimeError("Network timeout")

        # Act
        error = map_database_error("connection", message, original_error=original)

        # Assert
        assert isinstance(error, ConnectionError)
        assert error.message == message
        assert error.original_error is original

    def test_without_original_error(self):
        """Test map_database_error without original_error parameter"""
        # Arrange
        message = "Query failed"

        # Act
        error = map_database_error("query", message)

        # Assert
        assert isinstance(error, QueryError)
        assert error.message == message
        assert error.original_error is None

    def test_database_error_mapping_completeness(self):
        """Test DATABASE_ERROR_MAPPING contains expected mappings"""
        # Arrange & Act & Assert
        assert "connection" in DATABASE_ERROR_MAPPING
        assert "query" in DATABASE_ERROR_MAPPING
        assert "transaction" in DATABASE_ERROR_MAPPING
        assert "not_found" in DATABASE_ERROR_MAPPING
        assert "duplicate" in DATABASE_ERROR_MAPPING
        assert "integrity" in DATABASE_ERROR_MAPPING


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestExceptionIntegration:
    """Integration tests for exception handling scenarios"""

    def test_exception_chaining_with_original_error(self):
        """Test exception can wrap and preserve original error"""
        # Arrange
        original = ValueError("Original problem")
        message = "Wrapped error"

        # Act
        error = DevSkyyError(message, original_error=original)

        # Assert
        assert error.original_error is original
        assert str(original) == "Original problem"
        assert str(error) == message

    def test_exception_to_dict_serialization(self):
        """Test exception serialization to dict for logging"""
        # Arrange
        error = InvalidCredentialsError(
            "Login failed",
            error_code="AUTH_001",
            details={"username": "test_user", "attempt": 3},
        )

        # Act
        result = error.to_dict()

        # Assert
        assert result["error_type"] == "InvalidCredentialsError"
        assert result["error_code"] == "AUTH_001"
        assert result["message"] == "Login failed"
        assert result["details"]["username"] == "test_user"
        assert result["details"]["attempt"] == 3

    def test_exception_can_be_raised_and_caught_by_base_class(self):
        """Test specific exception can be caught by base class"""
        # Arrange & Act
        with pytest.raises(DevSkyyError) as exc_info:
            raise InvalidCredentialsError("Test error")

        # Assert
        assert isinstance(exc_info.value, InvalidCredentialsError)
        assert isinstance(exc_info.value, AuthenticationError)
        assert isinstance(exc_info.value, DevSkyyError)

    def test_exception_can_be_raised_and_caught_by_intermediate_class(self):
        """Test specific exception can be caught by intermediate class"""
        # Arrange & Act
        with pytest.raises(AuthenticationError) as exc_info:
            raise TokenExpiredError("Token expired")

        # Assert
        assert isinstance(exc_info.value, TokenExpiredError)
        assert isinstance(exc_info.value, AuthenticationError)

    def test_multiple_exceptions_have_unique_error_codes(self):
        """Test different exception classes have unique default error codes"""
        # Arrange & Act
        error1 = InvalidCredentialsError("Error 1")
        error2 = TokenExpiredError("Error 2")
        error3 = RecordNotFoundError("Error 3")

        # Assert
        assert error1.error_code == "InvalidCredentialsError"
        assert error2.error_code == "TokenExpiredError"
        assert error3.error_code == "RecordNotFoundError"
        assert error1.error_code != error2.error_code
        assert error2.error_code != error3.error_code

    def test_custom_error_codes_override_defaults(self):
        """Test custom error codes override class name defaults"""
        # Arrange & Act
        error1 = InvalidCredentialsError("Error", error_code="CUSTOM_001")
        error2 = InvalidCredentialsError("Error", error_code="CUSTOM_002")

        # Assert
        assert error1.error_code == "CUSTOM_001"
        assert error2.error_code == "CUSTOM_002"
        assert error1.error_code != "InvalidCredentialsError"

    def test_details_can_store_complex_data_structures(self):
        """Test details dictionary can store nested data"""
        # Arrange
        details = {
            "request_id": "req_123",
            "user": {"id": 456, "email": "test@example.com"},
            "validation_errors": [
                {"field": "email", "error": "invalid"},
                {"field": "password", "error": "too short"},
            ],
            "metadata": {"timestamp": "2025-11-28T12:00:00Z", "retry_count": 3},
        }

        # Act
        error = ValidationError("Validation failed", details=details)

        # Assert
        assert error.details["request_id"] == "req_123"
        assert error.details["user"]["id"] == 456
        assert len(error.details["validation_errors"]) == 2
        assert error.details["metadata"]["retry_count"] == 3

    def test_exception_message_preserved_in_string_conversion(self):
        """Test exception message is preserved when converted to string"""
        # Arrange
        message = "This is the error message"
        error = DevSkyyError(message)

        # Act
        str_representation = str(error)

        # Assert
        assert str_representation == message

    def test_exception_hierarchy_allows_granular_error_handling(self):
        """Test exception hierarchy enables specific error handling"""
        # Arrange
        def risky_operation(error_type: str):
            if error_type == "connection":
                raise ConnectionError("DB connection failed")
            elif error_type == "query":
                raise QueryError("Query syntax error")
            elif error_type == "generic":
                raise DatabaseError("Generic DB error")

        # Act & Assert - Catch specific error
        with pytest.raises(ConnectionError):
            risky_operation("connection")

        # Act & Assert - Catch parent class
        with pytest.raises(DatabaseError):
            risky_operation("query")

        # Act & Assert - Catch base class
        with pytest.raises(DevSkyyError):
            risky_operation("generic")
