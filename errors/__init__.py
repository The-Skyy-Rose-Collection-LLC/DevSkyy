# errors/__init__.py
"""
DevSkyy Production Error Handling Module.

This module provides a comprehensive error hierarchy for production-grade
error handling across all DevSkyy services.

Design Principles:
- All errors inherit from DevSkyError for unified handling
- Errors carry correlation IDs for distributed tracing
- Severity levels enable appropriate alerting
- Context preservation for debugging
"""

from errors.production_errors import (
    AgentExecutionError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
    EncryptionError,
    ExternalServiceError,
    ImageProcessingError,
    LLMProviderError,
    MCPServerError,
    ModelFidelityError,
    PipelineError,
    RateLimitError,
    ResourceConflictError,
    ResourceNotFoundError,
    SecurityError,
    ThreeDGenerationError,
    ToolExecutionError,
    ValidationError,
    WordPressIntegrationError,
    classify_error,
    create_error_response,
    error_handler,
)

__all__ = [
    # Base
    "DevSkyError",
    "DevSkyErrorCode",
    "DevSkyErrorSeverity",
    # Auth
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    # External
    "ExternalServiceError",
    "DatabaseError",
    "ConfigurationError",
    # Resources
    "ResourceNotFoundError",
    "ResourceConflictError",
    # 3D/Imagery
    "ThreeDGenerationError",
    "ImageProcessingError",
    "ModelFidelityError",
    # Integration
    "WordPressIntegrationError",
    "MCPServerError",
    "LLMProviderError",
    # Execution
    "ToolExecutionError",
    "AgentExecutionError",
    # Security
    "SecurityError",
    "EncryptionError",
    # Pipeline
    "PipelineError",
    # Utilities
    "error_handler",
    "classify_error",
    "create_error_response",
]
