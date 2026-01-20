"""
Tests for 3D Pipeline Hardening
================================

Comprehensive tests for 3D asset pipeline security and resilience features:
- Request validation (file size, format, sanitization)
- Response validation (schema, data integrity)
- Retry logic with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- PII sanitization
"""

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
from pydantic import ValidationError

from ai_3d.providers.tripo import (
    ImageGenerationRequest,
    TextGenerationRequest,
    TripoAPIResponse,
    TripoClient,
    TripoTaskStatus,
)
from ai_3d.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    MaxRetriesExceededError,
    RetryConfig,
    RetryStrategy,
)

# =============================================================================
# Request Validation Tests
# =============================================================================


class TestRequestValidation:
    """Test comprehensive request validation."""

    def test_image_request_validates_file_exists(self, tmp_path: Path):
        """Test image request validates file existence."""
        nonexistent = tmp_path / "nonexistent.jpg"

        with pytest.raises(ValidationError, match="Image file does not exist"):
            ImageGenerationRequest(
                image_path=nonexistent,
                output_format="glb",
            )

    def test_image_request_validates_file_size(self, tmp_path: Path):
        """Test image request rejects files > 10MB."""
        large_image = tmp_path / "large.jpg"
        # Create file > 10MB
        large_image.write_bytes(b"x" * (11 * 1024 * 1024))

        with pytest.raises(ValidationError, match="Image file too large"):
            ImageGenerationRequest(
                image_path=large_image,
                output_format="glb",
            )

    def test_image_request_validates_format(self, tmp_path: Path):
        """Test image request validates file format."""
        invalid_format = tmp_path / "test.bmp"
        invalid_format.write_bytes(b"test")

        with pytest.raises(ValidationError, match="Invalid image format"):
            ImageGenerationRequest(
                image_path=invalid_format,
                output_format="glb",
            )

    def test_image_request_sanitizes_prompt(self, tmp_path: Path):
        """Test image request sanitizes prompts for XSS."""
        valid_image = tmp_path / "test.jpg"
        valid_image.write_bytes(b"test")

        with pytest.raises(
            ValidationError,
            match="Potentially dangerous content in prompt",
        ):
            ImageGenerationRequest(
                image_path=valid_image,
                prompt="<script>alert('xss')</script>",
                output_format="glb",
            )

    def test_image_request_enforces_texture_resolution_bounds(self, tmp_path: Path):
        """Test texture resolution must be 512-4096."""
        valid_image = tmp_path / "test.jpg"
        valid_image.write_bytes(b"test")

        # Too low
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                image_path=valid_image,
                texture_resolution=256,  # < 512
                output_format="glb",
            )

        # Too high
        with pytest.raises(ValidationError):
            ImageGenerationRequest(
                image_path=valid_image,
                texture_resolution=8192,  # > 4096
                output_format="glb",
            )

    def test_image_request_validates_output_format(self, tmp_path: Path):
        """Test output format must be in allowed list."""
        valid_image = tmp_path / "test.jpg"
        valid_image.write_bytes(b"test")

        with pytest.raises(ValidationError, match="Invalid format"):
            ImageGenerationRequest(
                image_path=valid_image,
                output_format="stl",  # Not in allowed list
            )

    def test_text_request_enforces_min_length(self):
        """Test text prompt must be at least 10 characters."""
        with pytest.raises(ValidationError, match="String should have at least 10 characters"):
            TextGenerationRequest(
                prompt="short",  # < 10 chars
                output_format="glb",
            )

    def test_text_request_sanitizes_prompt(self):
        """Test text prompt is sanitized for XSS."""
        with pytest.raises(
            ValidationError,
            match="Potentially dangerous content in prompt",
        ):
            TextGenerationRequest(
                prompt="Valid prompt but with javascript:void(0)",
                output_format="glb",
            )

    def test_text_request_trims_whitespace(self):
        """Test text prompt is trimmed."""
        request = TextGenerationRequest(
            prompt="  Valid prompt with spaces  ",
            output_format="glb",
        )
        assert request.prompt == "Valid prompt with spaces"


# =============================================================================
# Response Validation Tests
# =============================================================================


class TestResponseValidation:
    """Test API response validation."""

    def test_api_response_validates_code_range(self):
        """Test API response code must be in valid range."""
        with pytest.raises(ValidationError, match="Invalid API response code"):
            TripoAPIResponse(
                code=999,  # Out of range
                message="test",
                data={},
            )

    def test_api_response_detects_success(self):
        """Test API response correctly identifies success."""
        success_response = TripoAPIResponse(
            code=200,
            message="Success",
            data={"task_id": "test-123"},
        )
        assert success_response.is_success() is True

    def test_api_response_detects_failure(self):
        """Test API response correctly identifies failure."""
        # HTTP error code
        error_response = TripoAPIResponse(
            code=400,
            message="Bad Request",
            data=None,
        )
        assert error_response.is_success() is False

        # Missing data
        no_data_response = TripoAPIResponse(
            code=200,
            message="OK",
            data=None,
        )
        assert no_data_response.is_success() is False

    def test_validate_task_result_checks_structure(self):
        """Test task result validation checks required fields."""
        client = TripoClient(api_key="test-key", enable_resilience=False)

        # Missing 'model' field
        with pytest.raises(ValueError, match="missing 'model' field"):
            client._validate_task_result({"other_field": "value"})

        # Invalid model structure
        with pytest.raises(ValueError, match="Invalid model data structure"):
            client._validate_task_result({"model": "not a dict"})

        # Missing URL
        with pytest.raises(ValueError, match="missing valid model URL"):
            client._validate_task_result({"model": {}})

        # Invalid URL
        with pytest.raises(ValueError, match="Invalid model URL"):
            client._validate_task_result({"model": {"url": "ftp://invalid"}})

    def test_validate_task_result_accepts_valid_structure(self):
        """Test task result validation accepts valid structure."""
        client = TripoClient(api_key="test-key", enable_resilience=False)

        valid_result = {
            "model": {
                "url": "https://example.com/model.glb",
                "format": "glb",
            }
        }

        # Should not raise
        client._validate_task_result(valid_result)


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    def test_retry_calculates_exponential_delay(self):
        """Test retry delay increases exponentially."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False,  # Disable for deterministic testing
        )
        strategy = RetryStrategy(config)

        # attempt 1: 1.0 * (2^0) = 1.0
        assert strategy.calculate_delay(1) == 1.0

        # attempt 2: 1.0 * (2^1) = 2.0
        assert strategy.calculate_delay(2) == 2.0

        # attempt 3: 1.0 * (2^2) = 4.0
        assert strategy.calculate_delay(3) == 4.0

        # attempt 4: 1.0 * (2^3) = 8.0
        assert strategy.calculate_delay(4) == 8.0

    def test_retry_respects_max_delay(self):
        """Test retry delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False,
        )
        strategy = RetryStrategy(config)

        # Large attempt number should be capped
        delay = strategy.calculate_delay(10)  # Would be 512 without cap
        assert delay == 10.0

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_attempt(self):
        """Test retry returns immediately on success."""

        async def success_func():
            return "success"

        strategy = RetryStrategy(RetryConfig(max_attempts=3))
        result = await strategy.execute(success_func)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Test retry succeeds after initial failures."""
        attempts = []

        async def flaky_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"

        strategy = RetryStrategy(RetryConfig(max_attempts=5, initial_delay=0.1))

        result = await strategy.execute(
            flaky_func,
            retryable_exceptions=(httpx.TimeoutException,),
        )

        assert result == "success"
        assert len(attempts) == 3  # Failed twice, succeeded on 3rd

    @pytest.mark.asyncio
    async def test_retry_raises_after_max_attempts(self):
        """Test retry raises MaxRetriesExceededError after exhausting attempts."""

        async def always_fails():
            raise ValueError("Always fails")

        strategy = RetryStrategy(RetryConfig(max_attempts=3, initial_delay=0.1))

        with pytest.raises(MaxRetriesExceededError) as exc_info:
            await strategy.execute(
                always_fails,
                retryable_exceptions=(ValueError,),
            )

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ValueError)


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_starts_closed(self):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        assert cb.state_data.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        # Record failures
        for _ in range(3):
            cb.record_failure()

        assert cb.state_data.state == CircuitState.OPEN

    def test_circuit_resets_failures_on_success_when_closed(self):
        """Test failure count resets on success in CLOSED state."""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("test", config)

        # Record some failures
        cb.record_failure()
        cb.record_failure()
        assert cb.state_data.failure_count == 2

        # Success resets count
        cb.record_success()
        assert cb.state_data.failure_count == 0

    def test_circuit_transitions_open_to_half_open_after_timeout(self):
        """Test circuit transitions from OPEN to HALF_OPEN after timeout."""
        import time

        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.5,  # 500ms timeout
        )
        cb = CircuitBreaker("test", config)

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state_data.state == CircuitState.OPEN

        # Should not allow attempt immediately
        assert cb._should_attempt() is False

        # Wait for timeout
        time.sleep(0.6)

        # Should now allow attempt (transitions to HALF_OPEN)
        assert cb._should_attempt() is True
        assert cb.state_data.state == CircuitState.HALF_OPEN

    def test_circuit_closes_after_success_threshold_in_half_open(self):
        """Test circuit closes after success threshold in HALF_OPEN."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
        )
        cb = CircuitBreaker("test", config)

        # Manually set to HALF_OPEN
        cb.state_data.state = CircuitState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.state_data.state == CircuitState.HALF_OPEN  # Still half-open

        cb.record_success()
        assert cb.state_data.state == CircuitState.CLOSED  # Now closed

    def test_circuit_reopens_on_failure_in_half_open(self):
        """Test circuit reopens on failure in HALF_OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker("test", config)

        # Set to HALF_OPEN
        cb.state_data.state = CircuitState.HALF_OPEN

        # Failure reopens circuit
        cb.record_failure()
        assert cb.state_data.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when OPEN."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=10.0)
        cb = CircuitBreaker("test", config)

        # Open the circuit
        cb.record_failure()
        assert cb.state_data.state == CircuitState.OPEN

        async def test_func():
            return "success"

        # Should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.call(test_func)

        assert "test" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_when_closed(self):
        """Test circuit breaker allows calls when CLOSED."""
        cb = CircuitBreaker("test", CircuitBreakerConfig())

        async def test_func():
            return "success"

        result = await cb.call(test_func)
        assert result == "success"
        assert cb.state_data.state == CircuitState.CLOSED


# =============================================================================
# Graceful Degradation Tests
# =============================================================================


class TestGracefulDegradation:
    """Test graceful degradation with caching and fallback."""

    @pytest.mark.asyncio
    async def test_download_retries_on_network_error(self, tmp_path: Path):
        """Test download retries on network errors."""
        client = TripoClient(api_key="test-key", enable_resilience=True)

        attempts = []

        async def mock_download(url: str, output_path: Path):
            attempts.append(1)
            if len(attempts) < 2:
                raise httpx.NetworkError("Connection failed")
            # Success on 2nd attempt
            output_path.write_bytes(b"model data")

        with patch.object(client, "_download_model", new=mock_download):
            output_path = tmp_path / "model.glb"
            await client._download_model_resilient(
                "https://example.com/model.glb",
                output_path,
            )

        assert len(attempts) == 2  # Retried once
        assert output_path.exists()

    @pytest.mark.asyncio
    async def test_client_sanitizes_logs(self):
        """Test client sanitizes sensitive data in logs."""
        client = TripoClient(api_key="test-key")

        long_text = "A" * 100 + "sensitive_data_here"
        sanitized = client._sanitize_for_logs(long_text, max_length=50)

        # Should be truncated
        assert len(sanitized) < len(long_text)
        # Should include hash
        assert "..." in sanitized


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
class TestIntegration:
    """Test full integration of hardening features."""

    async def test_generate_from_image_with_validation(self, tmp_path: Path):
        """Test image generation with full validation stack."""
        # Create valid test image
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake jpeg data")

        output_dir = tmp_path / "output"

        client = TripoClient(api_key="test-key", enable_resilience=False)

        # Mock the API calls
        with patch.object(client, "_create_image_to_3d_task") as mock_create:  # noqa: SIM117
            with patch.object(client, "_wait_for_task") as mock_wait:
                with patch.object(client, "_download_model") as mock_download:
                    # Setup mocks
                    mock_create.return_value = "task-123"
                    mock_wait.return_value = TripoTaskStatus(
                        task_id="task-123",
                        status="success",
                        progress=100,
                        result={"model": {"url": "https://example.com/model.glb"}},
                    )
                    mock_download.return_value = None

                    # Should succeed
                    result = await client.generate_from_image(
                        image_path=str(test_image),
                        output_dir=str(output_dir),
                        output_format="glb",
                        prompt="Test product",
                    )

                    assert result is not None
                    assert "test_3d.glb" in result

    async def test_generate_from_text_with_validation(self, tmp_path: Path):
        """Test text generation with full validation stack."""
        output_dir = tmp_path / "output"

        client = TripoClient(api_key="test-key", enable_resilience=False)

        with patch.object(client, "_create_text_to_3d_task") as mock_create:  # noqa: SIM117
            with patch.object(client, "_wait_for_task") as mock_wait:
                with patch.object(client, "_download_model") as mock_download:
                    mock_create.return_value = "task-456"
                    mock_wait.return_value = TripoTaskStatus(
                        task_id="task-456",
                        status="success",
                        progress=100,
                        result={"model": {"url": "https://example.com/model.glb"}},
                    )
                    mock_download.return_value = None

                    result = await client.generate_from_text(
                        prompt="A luxury black rose themed product",
                        output_dir=str(output_dir),
                        output_format="glb",
                    )

                    assert result is not None

    async def test_health_status_reports_circuit_state(self):
        """Test health status includes circuit breaker state."""
        client = TripoClient(api_key="test-key", enable_resilience=True)

        health = client.get_health_status()

        assert "service_name" in health
        assert health["service_name"] == "tripo3d"
        assert "circuit_breaker" in health
        assert "cache_size" in health


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
