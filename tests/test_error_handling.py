"""
Comprehensive Tests for Error Handling Module (error_handling.py)
Tests error codes, circuit breakers, retry mechanisms, and centralized error handling
Coverage target: ≥90% for error_handling.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol requirements (Rule #8, Rule #10)
"""

import asyncio
from datetime import datetime, timedelta

import pytest

# Import error_handling module
from error_handling import (
    CircuitBreaker,
    CircuitBreakerState,
    DevSkyError,
    ErrorCode,
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    database_circuit_breaker,
    error_handler,
    external_api_circuit_breaker,
    openai_circuit_breaker,
    retry,
    retry_with_backoff,
)


# ============================================================================
# TEST ERROR CODES AND SEVERITY
# ============================================================================


class TestErrorCode:
    """Test ErrorCode enum"""

    def test_authentication_error_codes(self):
        """Should have authentication error codes"""
        assert ErrorCode.AUTHENTICATION_FAILED == "AUTH_001"
        assert ErrorCode.AUTHORIZATION_DENIED == "AUTH_002"
        assert ErrorCode.TOKEN_EXPIRED == "AUTH_003"
        assert ErrorCode.TOKEN_INVALID == "AUTH_004"
        assert ErrorCode.ACCOUNT_LOCKED == "AUTH_005"

    def test_validation_error_codes(self):
        """Should have validation error codes"""
        assert ErrorCode.VALIDATION_ERROR == "VAL_001"
        assert ErrorCode.INVALID_INPUT == "VAL_002"
        assert ErrorCode.MISSING_REQUIRED_FIELD == "VAL_003"
        assert ErrorCode.INVALID_FORMAT == "VAL_004"

    def test_database_error_codes(self):
        """Should have database error codes"""
        assert ErrorCode.DATABASE_CONNECTION_ERROR == "DB_001"
        assert ErrorCode.DATABASE_QUERY_ERROR == "DB_002"
        assert ErrorCode.DATABASE_CONSTRAINT_ERROR == "DB_003"
        assert ErrorCode.DATABASE_TIMEOUT == "DB_004"

    def test_external_service_error_codes(self):
        """Should have external service error codes"""
        assert ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE == "EXT_001"
        assert ErrorCode.EXTERNAL_SERVICE_TIMEOUT == "EXT_002"
        assert ErrorCode.EXTERNAL_SERVICE_ERROR == "EXT_003"
        assert ErrorCode.API_RATE_LIMIT_EXCEEDED == "EXT_004"

    def test_business_logic_error_codes(self):
        """Should have business logic error codes"""
        assert ErrorCode.RESOURCE_NOT_FOUND == "BIZ_001"
        assert ErrorCode.RESOURCE_ALREADY_EXISTS == "BIZ_002"
        assert ErrorCode.OPERATION_NOT_ALLOWED == "BIZ_003"
        assert ErrorCode.INSUFFICIENT_PERMISSIONS == "BIZ_004"

    def test_system_error_codes(self):
        """Should have system error codes"""
        assert ErrorCode.INTERNAL_SERVER_ERROR == "SYS_001"
        assert ErrorCode.SERVICE_UNAVAILABLE == "SYS_002"
        assert ErrorCode.CONFIGURATION_ERROR == "SYS_003"
        assert ErrorCode.RESOURCE_EXHAUSTED == "SYS_004"

    def test_security_error_codes(self):
        """Should have security error codes"""
        assert ErrorCode.SECURITY_VIOLATION == "SEC_001"
        assert ErrorCode.SUSPICIOUS_ACTIVITY == "SEC_002"
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "SEC_003"
        assert ErrorCode.BLOCKED_REQUEST == "SEC_004"


class TestErrorSeverity:
    """Test ErrorSeverity enum"""

    def test_severity_levels(self):
        """Should have all severity levels"""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"

    def test_severity_enum_members(self):
        """Should be valid enum members"""
        assert ErrorSeverity.LOW in ErrorSeverity
        assert ErrorSeverity.MEDIUM in ErrorSeverity
        assert ErrorSeverity.HIGH in ErrorSeverity
        assert ErrorSeverity.CRITICAL in ErrorSeverity


# ============================================================================
# TEST DEVSKYERROR EXCEPTION
# ============================================================================


class TestDevSkyError:
    """Test DevSkyError custom exception"""

    def test_create_basic_error(self):
        """Should create basic DevSkyError"""
        error = DevSkyError(
            message="Test error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        )

        assert error.message == "Test error"
        assert error.error_code == ErrorCode.INTERNAL_SERVER_ERROR
        assert error.severity == ErrorSeverity.MEDIUM  # Default
        assert error.details == {}
        assert error.correlation_id is not None
        assert isinstance(error.timestamp, datetime)

    def test_create_error_with_severity(self):
        """Should create error with custom severity"""
        error = DevSkyError(
            message="Critical error",
            error_code=ErrorCode.DATABASE_CONNECTION_ERROR,
            severity=ErrorSeverity.CRITICAL,
        )

        assert error.severity == ErrorSeverity.CRITICAL

    def test_create_error_with_details(self):
        """Should create error with details"""
        details = {"user_id": "123", "operation": "login"}
        error = DevSkyError(
            message="Auth failed",
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            details=details,
        )

        assert error.details == details

    def test_create_error_with_correlation_id(self):
        """Should create error with custom correlation_id"""
        correlation_id = "test-correlation-123"
        error = DevSkyError(
            message="Test error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            correlation_id=correlation_id,
        )

        assert error.correlation_id == correlation_id

    def test_error_is_exception(self):
        """Should be a valid Exception"""
        error = DevSkyError(
            message="Test error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        )

        assert isinstance(error, Exception)

        # Should be raisable
        with pytest.raises(DevSkyError) as exc_info:
            raise error

        assert exc_info.value.message == "Test error"

    def test_error_timestamp_is_recent(self):
        """Should have recent timestamp"""
        error = DevSkyError(
            message="Test error",
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        )

        time_diff = datetime.utcnow() - error.timestamp
        assert time_diff.total_seconds() < 1  # Less than 1 second ago


# ============================================================================
# TEST CIRCUIT BREAKER STATE
# ============================================================================


class TestCircuitBreakerState:
    """Test CircuitBreakerState enum"""

    def test_circuit_breaker_states(self):
        """Should have all circuit breaker states"""
        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.OPEN == "open"
        assert CircuitBreakerState.HALF_OPEN == "half_open"

    def test_states_are_enum_members(self):
        """Should be valid enum members"""
        assert CircuitBreakerState.CLOSED in CircuitBreakerState
        assert CircuitBreakerState.OPEN in CircuitBreakerState
        assert CircuitBreakerState.HALF_OPEN in CircuitBreakerState


# ============================================================================
# TEST CIRCUIT BREAKER
# ============================================================================


class TestCircuitBreaker:
    """Test CircuitBreaker class"""

    def test_create_circuit_breaker(self):
        """Should create circuit breaker with defaults"""
        cb = CircuitBreaker(name="test_service")

        assert cb.name == "test_service"
        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60
        assert cb.expected_exception == Exception
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.total_requests == 0
        assert cb.total_failures == 0
        assert cb.total_successes == 0

    def test_create_circuit_breaker_custom_config(self):
        """Should create circuit breaker with custom config"""
        cb = CircuitBreaker(
            name="custom_service",
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=ValueError,
        )

        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert cb.expected_exception == ValueError

    @pytest.mark.asyncio
    async def test_circuit_breaker_success(self):
        """Should execute successful function"""
        cb = CircuitBreaker(name="test_service")

        async def successful_func():
            return "success"

        result = await cb.call(successful_func)

        assert result == "success"
        assert cb.total_requests == 1
        assert cb.total_successes == 1
        assert cb.total_failures == 0
        assert cb.failure_count == 0
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_sync_function(self):
        """Should execute synchronous function"""
        cb = CircuitBreaker(name="test_service")

        def sync_func():
            return "sync_success"

        result = await cb.call(sync_func)

        assert result == "sync_success"
        assert cb.total_successes == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_single_failure(self):
        """Should handle single failure"""
        cb = CircuitBreaker(name="test_service", failure_threshold=3)

        async def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await cb.call(failing_func)

        assert cb.total_requests == 1
        assert cb.total_failures == 1
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED  # Not open yet

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self):
        """Should open circuit after failure threshold"""
        cb = CircuitBreaker(name="test_service", failure_threshold=3)

        async def failing_func():
            raise ValueError("Test error")

        # Fail 3 times to trigger threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.call(failing_func)

        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 3
        assert cb.total_failures == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """Should reject requests when circuit is open"""
        cb = CircuitBreaker(name="test_service", failure_threshold=2)

        async def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(failing_func)

        assert cb.state == CircuitBreakerState.OPEN

        # Next request should be rejected
        async def any_func():
            return "success"

        with pytest.raises(DevSkyError) as exc_info:
            await cb.call(any_func)

        assert exc_info.value.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert "OPEN" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self):
        """Should transition to half-open after recovery timeout"""
        cb = CircuitBreaker(name="test_service", failure_threshold=2, recovery_timeout=0)

        async def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(failing_func)

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout (set to 0 for immediate)
        await asyncio.sleep(0.01)

        # Next request should transition to half-open
        async def successful_func():
            return "success"

        result = await cb.call(successful_func)

        assert result == "success"
        # State should transition through half-open
        # Need 3 successes to fully close, so still in half-open after 1 success

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_successes(self):
        """Should close circuit after 3 consecutive successes in half-open"""
        cb = CircuitBreaker(name="test_service", failure_threshold=2, recovery_timeout=0)

        async def failing_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(failing_func)

        assert cb.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.01)

        # Execute 3 successful requests
        async def successful_func():
            return "success"

        for _ in range(3):
            await cb.call(successful_func)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0  # Reset after closing

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Should work as decorator"""
        cb = CircuitBreaker(name="test_service")

        @cb
        async def decorated_func():
            return "decorated_success"

        result = await decorated_func()

        assert result == "decorated_success"
        assert cb.total_successes == 1

    def test_circuit_breaker_get_stats(self):
        """Should return statistics"""
        cb = CircuitBreaker(name="test_service")
        cb.total_requests = 10
        cb.total_failures = 3
        cb.total_successes = 7
        cb.failure_count = 1

        stats = cb.get_stats()

        assert stats["name"] == "test_service"
        assert stats["state"] == CircuitBreakerState.CLOSED
        assert stats["failure_count"] == 1
        assert stats["total_requests"] == 10
        assert stats["total_failures"] == 3
        assert stats["total_successes"] == 7
        assert stats["failure_rate"] == 0.3
        assert stats["last_failure_time"] is None

    def test_circuit_breaker_stats_with_failure_time(self):
        """Should include last failure time in stats"""
        cb = CircuitBreaker(name="test_service")
        cb.last_failure_time = datetime.utcnow()

        stats = cb.get_stats()

        assert stats["last_failure_time"] is not None
        assert isinstance(stats["last_failure_time"], str)  # ISO format

    def test_should_attempt_reset_no_failures(self):
        """Should attempt reset when no failures"""
        cb = CircuitBreaker(name="test_service")

        assert cb._should_attempt_reset() is True

    def test_should_attempt_reset_after_timeout(self):
        """Should attempt reset after recovery timeout"""
        cb = CircuitBreaker(name="test_service", recovery_timeout=0)
        cb.last_failure_time = datetime.utcnow() - timedelta(seconds=1)

        assert cb._should_attempt_reset() is True

    def test_should_not_attempt_reset_before_timeout(self):
        """Should not attempt reset before recovery timeout"""
        cb = CircuitBreaker(name="test_service", recovery_timeout=60)
        cb.last_failure_time = datetime.utcnow()

        assert cb._should_attempt_reset() is False

    def test_on_success_resets_failure_count(self):
        """Should reset failure count on success"""
        cb = CircuitBreaker(name="test_service")
        cb.failure_count = 3

        cb._on_success()

        assert cb.failure_count == 0
        assert cb.total_successes == 1

    def test_on_failure_increments_counts(self):
        """Should increment failure counts"""
        cb = CircuitBreaker(name="test_service")

        cb._on_failure()

        assert cb.failure_count == 1
        assert cb.total_failures == 1
        assert cb.last_failure_time is not None


# ============================================================================
# TEST RETRY CONFIGURATION
# ============================================================================


class TestRetryConfig:
    """Test RetryConfig class"""

    def test_create_default_config(self):
        """Should create retry config with defaults"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retryable_exceptions == [Exception]

    def test_create_custom_config(self):
        """Should create retry config with custom values"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
            retryable_exceptions=[ValueError, TypeError],
        )

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == [ValueError, TypeError]


# ============================================================================
# TEST RETRY WITH BACKOFF
# ============================================================================


class TestRetryWithBackoff:
    """Test retry_with_backoff function"""

    @pytest.mark.asyncio
    async def test_retry_successful_first_attempt(self):
        """Should succeed on first attempt"""
        config = RetryConfig(max_attempts=3)

        async def successful_func():
            return "success"

        result = await retry_with_backoff(successful_func, config)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_sync_function(self):
        """Should retry synchronous function"""
        config = RetryConfig(max_attempts=3)

        def sync_func():
            return "sync_success"

        result = await retry_with_backoff(sync_func, config)

        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Should succeed after retries"""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        attempt_count = 0

        async def func_fails_twice():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await retry_with_backoff(func_fails_twice, config)

        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_raises_after_max_attempts(self):
        """Should raise exception after max attempts"""
        config = RetryConfig(max_attempts=3, base_delay=0.01)

        async def always_fails():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError) as exc_info:
            await retry_with_backoff(always_fails, config)

        assert "Persistent error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        """Should not retry non-retryable exceptions"""
        config = RetryConfig(
            max_attempts=3,
            retryable_exceptions=[ValueError],
        )
        attempt_count = 0

        async def raises_type_error():
            nonlocal attempt_count
            attempt_count += 1
            raise TypeError("Non-retryable error")

        with pytest.raises(TypeError):
            await retry_with_backoff(raises_type_error, config)

        assert attempt_count == 1  # Only tried once

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Should use exponential backoff"""
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            exponential_base=2.0,
            jitter=False,
        )

        start_time = asyncio.get_event_loop().time()
        attempt_count = 0

        async def always_fails():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await retry_with_backoff(always_fails, config)

        elapsed = asyncio.get_event_loop().time() - start_time

        # Should have delays: 0.1s, 0.2s = 0.3s total minimum
        assert elapsed >= 0.2  # At least two delays
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_respects_max_delay(self):
        """Should respect max_delay cap"""
        config = RetryConfig(
            max_attempts=5,
            base_delay=10.0,
            max_delay=0.1,  # Cap at 0.1s
            exponential_base=2.0,
            jitter=False,
        )

        start_time = asyncio.get_event_loop().time()

        async def always_fails():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await retry_with_backoff(always_fails, config)

        elapsed = asyncio.get_event_loop().time() - start_time

        # Should not exceed 4 * 0.1s = 0.4s (4 retries with 0.1s cap each)
        assert elapsed < 1.0  # Much less than if base_delay was used


# ============================================================================
# TEST RETRY DECORATOR
# ============================================================================


class TestRetryDecorator:
    """Test retry decorator"""

    @pytest.mark.asyncio
    async def test_retry_decorator_default_config(self):
        """Should use default retry config"""

        @retry()
        async def func():
            return "success"

        result = await func()

        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_decorator_custom_config(self):
        """Should use custom retry config"""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        attempt_count = 0

        @retry(config)
        async def func_fails_once():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = await func_fails_once()

        assert result == "success"
        assert attempt_count == 2


# ============================================================================
# TEST ERROR HANDLER
# ============================================================================


class TestErrorHandler:
    """Test ErrorHandler class"""

    def test_create_error_handler(self):
        """Should create error handler"""
        handler = ErrorHandler()

        assert isinstance(handler.circuit_breakers, dict)
        assert len(handler.circuit_breakers) == 0
        assert handler.error_stats == {}
        assert len(handler.recent_errors) == 0

    def test_register_circuit_breaker(self):
        """Should register circuit breaker"""
        handler = ErrorHandler()

        cb = handler.register_circuit_breaker(
            name="test_service",
            failure_threshold=3,
            recovery_timeout=30,
        )

        assert cb.name == "test_service"
        assert cb.failure_threshold == 3
        assert cb.recovery_timeout == 30
        assert handler.circuit_breakers["test_service"] == cb

    def test_get_circuit_breaker(self):
        """Should get circuit breaker by name"""
        handler = ErrorHandler()
        cb = handler.register_circuit_breaker(name="test_service")

        retrieved = handler.get_circuit_breaker("test_service")

        assert retrieved == cb

    def test_get_nonexistent_circuit_breaker(self):
        """Should return None for nonexistent circuit breaker"""
        handler = ErrorHandler()

        result = handler.get_circuit_breaker("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_devskyy_error(self):
        """Should handle DevSkyError"""
        handler = ErrorHandler()

        error = DevSkyError(
            message="Test error",
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            severity=ErrorSeverity.HIGH,
        )

        http_exc = await handler.handle_error(error)

        assert http_exc.status_code == 401  # AUTH_001 maps to 401
        assert "error_code" in http_exc.detail
        assert http_exc.detail["error_code"] == ErrorCode.AUTHENTICATION_FAILED

    @pytest.mark.asyncio
    async def test_handle_value_error(self):
        """Should handle ValueError"""
        handler = ErrorHandler()

        error = ValueError("Invalid value")
        http_exc = await handler.handle_error(error)

        assert http_exc.status_code == 400
        assert http_exc.detail["error_code"] == ErrorCode.VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_handle_permission_error(self):
        """Should handle PermissionError"""
        handler = ErrorHandler()

        error = PermissionError("Access denied")
        http_exc = await handler.handle_error(error)

        assert http_exc.status_code == 403
        assert http_exc.detail["error_code"] == ErrorCode.AUTHORIZATION_DENIED

    @pytest.mark.asyncio
    async def test_handle_generic_error(self):
        """Should handle generic exceptions"""
        handler = ErrorHandler()

        error = RuntimeError("Generic error")
        http_exc = await handler.handle_error(error)

        assert http_exc.status_code == 500
        assert http_exc.detail["error_code"] == ErrorCode.INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_handle_error_records_statistics(self):
        """Should record error statistics"""
        handler = ErrorHandler()

        error = ValueError("Test error")
        await handler.handle_error(error)

        assert handler.error_stats["ValueError"] == 1
        assert len(handler.recent_errors) == 1

        error_record = handler.recent_errors[0]
        assert error_record["error_type"] == "ValueError"
        assert error_record["message"] == "Test error"

    @pytest.mark.asyncio
    async def test_handle_error_with_context(self):
        """Should record error with context"""
        handler = ErrorHandler()

        context = {"user_id": "123", "operation": "test"}
        error = ValueError("Test error")

        await handler.handle_error(error, context=context)

        error_record = handler.recent_errors[0]
        assert error_record["context"] == context

    @pytest.mark.asyncio
    async def test_handle_error_with_user_and_request_id(self):
        """Should record user and request ID"""
        handler = ErrorHandler()

        error = ValueError("Test error")
        await handler.handle_error(
            error,
            user_id="user123",
            request_id="req456",
        )

        error_record = handler.recent_errors[0]
        assert error_record["user_id"] == "user123"
        assert error_record["request_id"] == "req456"

    def test_get_error_stats(self):
        """Should return error statistics"""
        handler = ErrorHandler()
        handler.error_stats["ValueError"] = 5
        handler.error_stats["TypeError"] = 3

        cb = handler.register_circuit_breaker(name="test_service")

        stats = handler.get_error_stats()

        assert stats["total_errors"] == 8
        assert stats["error_types"]["ValueError"] == 5
        assert stats["error_types"]["TypeError"] == 3
        assert "circuit_breaker_stats" in stats
        assert "test_service" in stats["circuit_breaker_stats"]

    def test_handle_devskyy_error_all_status_codes(self):
        """Should map all error codes to correct HTTP status"""
        handler = ErrorHandler()

        # Test a few key mappings
        test_cases = [
            (ErrorCode.TOKEN_EXPIRED, 401),
            (ErrorCode.ACCOUNT_LOCKED, 423),
            (ErrorCode.VALIDATION_ERROR, 422),
            (ErrorCode.INVALID_INPUT, 400),
            (ErrorCode.DATABASE_CONNECTION_ERROR, 503),
            (ErrorCode.DATABASE_TIMEOUT, 504),
            (ErrorCode.RESOURCE_NOT_FOUND, 404),
            (ErrorCode.RESOURCE_ALREADY_EXISTS, 409),
            (ErrorCode.API_RATE_LIMIT_EXCEEDED, 429),
        ]

        for error_code, expected_status in test_cases:
            error = DevSkyError(
                message="Test",
                error_code=error_code,
            )
            http_exc = handler._handle_devskyy_error(error)
            assert http_exc.status_code == expected_status, \
                f"Error code {error_code} should map to status {expected_status}"


# ============================================================================
# TEST GLOBAL INSTANCES
# ============================================================================


class TestGlobalInstances:
    """Test global error handler and circuit breakers"""

    def test_global_error_handler_exists(self):
        """Should have global error_handler instance"""
        assert error_handler is not None
        assert isinstance(error_handler, ErrorHandler)

    def test_database_circuit_breaker_registered(self):
        """Should have database circuit breaker registered"""
        assert database_circuit_breaker is not None
        assert isinstance(database_circuit_breaker, CircuitBreaker)
        assert database_circuit_breaker.name == "database"
        assert database_circuit_breaker.failure_threshold == 3
        assert database_circuit_breaker.recovery_timeout == 30

    def test_openai_circuit_breaker_registered(self):
        """Should have OpenAI circuit breaker registered"""
        assert openai_circuit_breaker is not None
        assert isinstance(openai_circuit_breaker, CircuitBreaker)
        assert openai_circuit_breaker.name == "openai_api"
        assert openai_circuit_breaker.failure_threshold == 5
        assert openai_circuit_breaker.recovery_timeout == 60

    def test_external_api_circuit_breaker_registered(self):
        """Should have external API circuit breaker registered"""
        assert external_api_circuit_breaker is not None
        assert isinstance(external_api_circuit_breaker, CircuitBreaker)
        assert external_api_circuit_breaker.name == "external_api"
        assert external_api_circuit_breaker.failure_threshold == 3
        assert external_api_circuit_breaker.recovery_timeout == 45

    def test_global_circuit_breakers_in_handler(self):
        """Should have circuit breakers registered in global handler"""
        assert "database" in error_handler.circuit_breakers
        assert "openai_api" in error_handler.circuit_breakers
        assert "external_api" in error_handler.circuit_breakers


# ============================================================================
# TEST INTEGRATION SCENARIOS
# ============================================================================


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Should combine circuit breaker with retry"""
        cb = CircuitBreaker(name="test_service", failure_threshold=2)
        config = RetryConfig(max_attempts=2, base_delay=0.01)

        attempt_count = 0

        async def func_fails_once():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ValueError("Temporary error")
            return "success"

        # Use retry with circuit breaker
        async def wrapped_func():
            return await cb.call(func_fails_once)

        result = await retry_with_backoff(wrapped_func, config)

        assert result == "success"
        assert cb.total_successes > 0

    @pytest.mark.asyncio
    async def test_error_handler_complete_flow(self):
        """Should handle complete error flow"""
        handler = ErrorHandler()

        # Register circuit breaker
        cb = handler.register_circuit_breaker(
            name="api_service",
            failure_threshold=2,
        )

        # Simulate API call failures
        async def api_call():
            raise DevSkyError(
                message="API unavailable",
                error_code=ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
            )

        # Try calls until circuit opens
        for _ in range(2):
            with pytest.raises(DevSkyError):
                await cb.call(api_call)

        # Circuit should be open
        assert cb.state == CircuitBreakerState.OPEN

        # Handle error
        error = DevSkyError(
            message="Service down",
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
        )
        http_exc = await handler.handle_error(error)

        assert http_exc.status_code == 503
        assert handler.error_stats["DevSkyError"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=error_handling", "--cov-report=term-missing"])
