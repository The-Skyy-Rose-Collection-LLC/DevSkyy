"""
Tests for Production Error Handling System
==========================================

Tests the error hierarchy, error formatting, and exception handling
for the DevSkyy production error system.
"""

from errors.production_errors import (
    MINIMUM_FIDELITY_SCORE,
    AssetNotFoundError,
    AuthenticationError,
    AuthorizationError,
    DevSkyError,
    ExternalServiceError,
    ModelFidelityError,
    PipelineError,
    RateLimitError,
    ResourceConflictError,
    ResourceNotFoundError,
    SyncError,
    ValidationError,
    create_correlation_id,
    format_error_response,
)


class TestDevSkyError:
    """Tests for base DevSkyError class."""

    def test_basic_creation(self):
        """Test basic error creation."""
        error = DevSkyError("Test error message")
        assert error.message == "Test error message"
        assert error.correlation_id is not None
        assert error.timestamp is not None

    def test_with_correlation_id(self):
        """Test error with custom correlation ID."""
        correlation_id = "test-123-456"
        error = DevSkyError("Test error", correlation_id=correlation_id)
        assert error.correlation_id == correlation_id

    def test_with_context(self):
        """Test error with additional context."""
        context = {"field": "value", "count": 42}
        error = DevSkyError("Test error", context=context)
        assert error.context == context

    def test_to_dict(self):
        """Test error serialization to dictionary."""
        error = DevSkyError("Test error", correlation_id="test-id", context={"key": "value"})
        error_dict = error.to_dict()

        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["correlation_id"] == "test-id"


class TestValidationError:
    """Tests for ValidationError class."""

    def test_field_validation_error(self):
        """Test validation error with field information."""
        error = ValidationError("Invalid email format", field="email", value="not-an-email")
        # Field is stored in context
        assert error.context.get("field") == "email"
        assert error.context.get("invalid_value") == "not-an-email"
        assert error.message == "Invalid email format"

    def test_validation_error_severity(self):
        """Test that validation error has warning severity."""
        error = ValidationError("Invalid input")
        assert error.severity.name == "WARNING"


class TestModelFidelityError:
    """Tests for ModelFidelityError class."""

    def test_fidelity_threshold_constant(self):
        """Test that fidelity threshold is 95%."""
        assert MINIMUM_FIDELITY_SCORE == 95.0
        assert ModelFidelityError.MINIMUM_FIDELITY_THRESHOLD == 95.0

    def test_fidelity_error_creation(self):
        """Test creating a fidelity error."""
        error = ModelFidelityError(actual_fidelity=85.5, required_fidelity=95.0)
        assert error.context.get("actual_fidelity") == 85.5
        assert error.context.get("required_fidelity") == 95.0

    def test_fidelity_error_message(self):
        """Test fidelity error message includes score."""
        error = ModelFidelityError(actual_fidelity=80.0, required_fidelity=95.0)
        assert "80.0" in error.message


class TestPipelineError:
    """Tests for PipelineError class."""

    def test_pipeline_error_with_step(self):
        """Test pipeline error with step information."""
        error = PipelineError(pipeline_name="3d_generation", step="texture_mapping")
        assert error.context.get("pipeline_name") == "3d_generation"
        assert error.context.get("failed_step") == "texture_mapping"
        assert "3d_generation" in error.message


class TestSyncError:
    """Tests for SyncError class."""

    def test_sync_error_with_source_target(self):
        """Test sync error with source and target information."""
        error = SyncError(source="catalog", target="woocommerce")
        assert error.context.get("source") == "catalog"
        assert error.context.get("target") == "woocommerce"
        assert "catalog" in error.message


class TestErrorFormatting:
    """Tests for error formatting functions."""

    def test_format_error_response(self):
        """Test error response formatting."""
        error = DevSkyError("Test error", correlation_id="test-123")
        response = format_error_response(error)

        assert response["error"]["message"] == "Test error"
        assert response["error"]["correlation_id"] == "test-123"
        assert "timestamp" in response["error"]

    def test_create_correlation_id(self):
        """Test correlation ID generation."""
        id1 = create_correlation_id()
        id2 = create_correlation_id()

        assert id1 != id2
        assert len(id1) > 8
        assert isinstance(id1, str)


class TestExternalServiceError:
    """Tests for ExternalServiceError class."""

    def test_external_service_error(self):
        """Test external service error creation."""
        error = ExternalServiceError(
            service_name="Tripo3D", message="API request failed", status_code=500
        )
        assert error.context.get("service_name") == "Tripo3D"
        assert error.context.get("status_code") == 500
        assert error.message == "API request failed"


class TestRateLimitError:
    """Tests for RateLimitError class."""

    def test_rate_limit_error(self):
        """Test rate limit error with retry info."""
        error = RateLimitError(message="Too many requests", retry_after=60)
        assert error.retry_after_seconds == 60
        assert error.retryable is True


class TestAuthenticationError:
    """Tests for AuthenticationError class."""

    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError("Invalid token")
        assert error.message == "Invalid token"


class TestAuthorizationError:
    """Tests for AuthorizationError class."""

    def test_authorization_error(self):
        """Test authorization error."""
        error = AuthorizationError(
            message="Insufficient permissions", action="delete", resource="product"
        )
        assert error.context.get("action") == "delete"
        assert error.context.get("resource") == "product"


class TestResourceErrors:
    """Tests for resource-related errors."""

    def test_resource_not_found(self):
        """Test resource not found error."""
        error = ResourceNotFoundError(resource_type="3d_model", resource_id="asset-123")
        assert error.context.get("resource_type") == "3d_model"
        assert error.context.get("resource_id") == "asset-123"

    def test_resource_conflict(self):
        """Test resource conflict error."""
        error = ResourceConflictError(message="Asset already exists", resource_type="product")
        assert error.context.get("resource_type") == "product"
        assert error.message == "Asset already exists"


class TestAssetNotFoundError:
    """Tests for AssetNotFoundError class."""

    def test_asset_not_found(self):
        """Test asset not found error."""
        error = AssetNotFoundError(asset_id="model-456", asset_type="3d_model")
        # asset_id is passed to parent as resource_id
        assert error.context.get("resource_id") == "model-456"
        assert error.context.get("asset_type") == "3d_model"
