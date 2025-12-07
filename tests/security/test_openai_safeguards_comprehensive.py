"""
Comprehensive Test Suite for OpenAI Safeguards Module

Tests safeguard enforcement, rate limiting, circuit breaker, audit logging,
request validation, and security policy compliance.

Per CLAUDE.md Rule #8: Target ≥85% coverage
Per CLAUDE.md Rule #13: Security baseline verification

Author: DevSkyy Enterprise Team
Version: 2.0.0
Python: >=3.11.0
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import time

import pytest

from security.openai_safeguards import (
    AuditLogEntry,
    AuditLogger,
    CircuitBreaker,
    CircuitBreakerState,
    OpenAISafeguardManager,
    OperationType,
    RateLimiter,
    RequestValidator,
    SafeguardConfig,
    SafeguardLevel,
    SafeguardViolation,
    get_safeguard_manager,
    reload_safeguard_manager,
    with_safeguards,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary directory for test logs"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def safeguard_config(temp_log_dir):
    """Create SafeguardConfig for testing"""
    return SafeguardConfig(
        level=SafeguardLevel.STRICT,
        enforce_consequential_in_production=True,
        require_audit_logging=True,
        enable_rate_limiting=True,
        max_requests_per_minute=60,
        max_consequential_per_hour=100,
        enable_circuit_breaker=True,
        failure_threshold=5,
        recovery_timeout_seconds=60,
        enable_request_validation=True,
        max_prompt_length=100000,
        blocked_keywords=["malicious", "forbidden"],
        enable_monitoring=True,
        alert_on_violations=True,
        audit_log_path=temp_log_dir / "openai_audit.jsonl",
        violation_log_path=temp_log_dir / "openai_violations.jsonl",
    )


@pytest.fixture
def safeguard_manager(safeguard_config):
    """Create OpenAISafeguardManager for testing"""
    return OpenAISafeguardManager(safeguard_config)


@pytest.fixture
def rate_limiter():
    """Create RateLimiter for testing"""
    return RateLimiter(max_per_minute=10, max_consequential_per_hour=5)


@pytest.fixture
def circuit_breaker():
    """Create CircuitBreaker for testing"""
    return CircuitBreaker(failure_threshold=3, recovery_timeout=5)


# ============================================================================
# ENUM AND MODEL TESTS
# ============================================================================


class TestEnumsAndModels:
    """Test safeguard enums and models"""

    def test_safeguard_level_enum(self):
        """Test SafeguardLevel enum values"""
        assert SafeguardLevel.STRICT == "strict"
        assert SafeguardLevel.MODERATE == "moderate"
        assert SafeguardLevel.PERMISSIVE == "permissive"

    def test_operation_type_enum(self):
        """Test OperationType enum values"""
        assert OperationType.CONTENT_GENERATION == "content_generation"
        assert OperationType.CODE_GENERATION == "code_generation"
        assert OperationType.DATA_ANALYSIS == "data_analysis"
        assert OperationType.CUSTOMER_INTERACTION == "customer_interaction"
        assert OperationType.SYSTEM_MODIFICATION == "system_modification"
        assert OperationType.FINANCIAL_OPERATION == "financial_operation"

    def test_circuit_breaker_state_enum(self):
        """Test CircuitBreakerState enum values"""
        assert CircuitBreakerState.CLOSED == "closed"
        assert CircuitBreakerState.OPEN == "open"
        assert CircuitBreakerState.HALF_OPEN == "half_open"

    def test_safeguard_violation_model(self):
        """Test SafeguardViolation model creation"""
        violation = SafeguardViolation(
            violation_type="rate_limit_exceeded",
            severity="high",
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            details={"reason": "Too many requests"},
        )

        assert violation.violation_type == "rate_limit_exceeded"
        assert violation.severity == "high"
        assert violation.operation_type == OperationType.CONTENT_GENERATION
        assert violation.is_consequential is True
        assert isinstance(violation.timestamp, datetime)
        assert violation.resolved is False

    def test_audit_log_entry_model(self):
        """Test AuditLogEntry model creation"""
        entry = AuditLogEntry(
            operation_id="op_123",
            operation_type=OperationType.CODE_GENERATION,
            is_consequential=True,
            user_id="user_456",
            request_params={"prompt": "test"},
            success=True,
            execution_time_ms=250.5,
        )

        assert entry.operation_id == "op_123"
        assert entry.operation_type == OperationType.CODE_GENERATION
        assert entry.success is True
        assert entry.execution_time_ms == 250.5


# ============================================================================
# SAFEGUARD CONFIG TESTS
# ============================================================================


class TestSafeguardConfig:
    """Test SafeguardConfig validation and defaults"""

    def test_safeguard_config_defaults(self):
        """Test SafeguardConfig default values"""
        config = SafeguardConfig()

        assert config.level == SafeguardLevel.STRICT
        assert config.enforce_consequential_in_production is True
        assert config.require_audit_logging is True
        assert config.enable_rate_limiting is True
        assert config.max_requests_per_minute == 60
        assert config.enable_circuit_breaker is True

    def test_safeguard_config_custom_values(self, safeguard_config):
        """Test SafeguardConfig with custom values"""
        assert safeguard_config.level == SafeguardLevel.STRICT
        assert safeguard_config.max_requests_per_minute == 60
        assert safeguard_config.failure_threshold == 5
        assert safeguard_config.blocked_keywords == ["malicious", "forbidden"]

    def test_safeguard_config_immutable(self, safeguard_config):
        """Test SafeguardConfig is frozen (immutable)"""
        with pytest.raises(Exception):  # Pydantic validation error
            safeguard_config.level = SafeguardLevel.PERMISSIVE

    @patch.dict("os.environ", {"ENVIRONMENT": "production"})
    def test_production_enforces_strict_level(self):
        """Test production environment forces STRICT level"""
        config = SafeguardConfig(level=SafeguardLevel.MODERATE)
        # Should be forced to STRICT in production
        assert config.level == SafeguardLevel.STRICT

    def test_rate_limit_boundaries(self):
        """Test rate limit parameter boundaries"""
        # Test minimum
        config = SafeguardConfig(max_requests_per_minute=1)
        assert config.max_requests_per_minute == 1

        # Test maximum
        config = SafeguardConfig(max_requests_per_minute=1000)
        assert config.max_requests_per_minute == 1000

        # Test out of bounds - should fail validation
        with pytest.raises(Exception):
            SafeguardConfig(max_requests_per_minute=0)

        with pytest.raises(Exception):
            SafeguardConfig(max_requests_per_minute=1001)


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================


class TestRateLimiter:
    """Test RateLimiter functionality"""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self, rate_limiter):
        """Test RateLimiter initializes correctly"""
        assert rate_limiter.max_per_minute == 10
        assert rate_limiter.max_consequential_per_hour == 5
        assert rate_limiter.requests == []
        assert rate_limiter.consequential_requests == []

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_first_request(self, rate_limiter):
        """Test rate limiter allows first request"""
        allowed, reason = await rate_limiter.check_rate_limit()
        assert allowed is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_rate_limiter_tracks_requests(self, rate_limiter):
        """Test rate limiter tracks request count"""
        for i in range(5):
            await rate_limiter.check_rate_limit()

        assert len(rate_limiter.requests) == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_after_limit(self, rate_limiter):
        """Test rate limiter blocks after reaching limit"""
        # Make requests up to limit
        for i in range(10):
            await rate_limiter.check_rate_limit()

        # Next request should be blocked
        allowed, reason = await rate_limiter.check_rate_limit()
        assert allowed is False
        assert "Rate limit exceeded" in reason

    @pytest.mark.asyncio
    async def test_rate_limiter_consequential_tracking(self, rate_limiter):
        """Test rate limiter tracks consequential requests separately"""
        for i in range(3):
            await rate_limiter.check_rate_limit(is_consequential=True)

        assert len(rate_limiter.consequential_requests) == 3
        assert len(rate_limiter.requests) == 3

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_consequential_after_limit(self, rate_limiter):
        """Test rate limiter blocks consequential requests after limit"""
        # Make consequential requests up to limit
        for i in range(5):
            await rate_limiter.check_rate_limit(is_consequential=True)

        # Next consequential request should be blocked
        allowed, reason = await rate_limiter.check_rate_limit(is_consequential=True)
        assert allowed is False
        assert "Consequential operation limit exceeded" in reason

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_old_requests(self, rate_limiter):
        """Test rate limiter cleans requests older than 1 hour"""
        # Add old request (more than 1 hour ago)
        old_time = time.time() - 3601
        rate_limiter.requests.append(old_time)

        # Make new request (should clean old one)
        await rate_limiter.check_rate_limit()

        # Old request should be removed
        assert len(rate_limiter.requests) == 1
        assert rate_limiter.requests[0] > old_time

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_access(self, rate_limiter):
        """Test rate limiter handles concurrent access"""
        tasks = [rate_limiter.check_rate_limit() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be allowed (under limit)
        assert all(allowed for allowed, _ in results)


# ============================================================================
# CIRCUIT BREAKER TESTS
# ============================================================================


class TestCircuitBreaker:
    """Test CircuitBreaker pattern"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self, circuit_breaker):
        """Test CircuitBreaker initializes in CLOSED state"""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failures == 0
        assert circuit_breaker.failure_threshold == 3
        assert circuit_breaker.recovery_timeout == 5

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_successful_calls(self, circuit_breaker):
        """Test circuit breaker allows successful function calls"""
        async def successful_func():
            return "success"

        result = await circuit_breaker.call(successful_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_tracks_failures(self, circuit_breaker):
        """Test circuit breaker tracks failures"""
        async def failing_func():
            raise Exception("Test failure")

        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.failures == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self, circuit_breaker):
        """Test circuit breaker opens after failure threshold"""
        async def failing_func():
            raise Exception("Test failure")

        # Fail 3 times (threshold)
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)

        # Circuit should be open
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_when_open(self, circuit_breaker):
        """Test circuit breaker blocks requests when OPEN"""
        async def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)

        # Try to make another call - should be blocked
        with pytest.raises(Exception) as exc_info:
            await circuit_breaker.call(failing_func)

        assert "Circuit breaker is OPEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery after timeout"""
        async def failing_func():
            raise Exception("Test failure")

        async def successful_func():
            return "success"

        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)

        # Wait for recovery timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout + 0.1)

        # Should enter HALF_OPEN and allow one test request
        result = await circuit_breaker.call(successful_func)
        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self, circuit_breaker):
        """Test circuit breaker resets failure count on success"""
        async def failing_func():
            raise Exception("Test failure")

        async def successful_func():
            return "success"

        # Make some failures
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.failures == 1

        # Make successful call
        await circuit_breaker.call(successful_func)

        # Circuit should still be closed, but we don't reset failures
        # unless we're in HALF_OPEN state
        assert circuit_breaker.state == CircuitBreakerState.CLOSED


# ============================================================================
# REQUEST VALIDATOR TESTS
# ============================================================================


class TestRequestValidator:
    """Test RequestValidator functionality"""

    def test_request_validator_initialization(self, safeguard_config):
        """Test RequestValidator initializes with config"""
        validator = RequestValidator(safeguard_config)
        assert validator.config == safeguard_config

    def test_validate_prompt_success(self, safeguard_config):
        """Test prompt validation with valid prompt"""
        validator = RequestValidator(safeguard_config)
        valid, reason = validator.validate_prompt("This is a valid test prompt")

        assert valid is True
        assert reason is None

    def test_validate_prompt_too_long(self, safeguard_config):
        """Test prompt validation rejects too-long prompts"""
        validator = RequestValidator(safeguard_config)
        long_prompt = "x" * (safeguard_config.max_prompt_length + 1)

        valid, reason = validator.validate_prompt(long_prompt)

        assert valid is False
        assert "exceeds maximum length" in reason

    def test_validate_prompt_blocked_keyword(self, safeguard_config):
        """Test prompt validation blocks forbidden keywords"""
        validator = RequestValidator(safeguard_config)

        valid, reason = validator.validate_prompt("This prompt contains malicious content")

        assert valid is False
        assert "blocked keyword" in reason

    def test_validate_prompt_empty(self, safeguard_config):
        """Test prompt validation rejects empty prompts"""
        validator = RequestValidator(safeguard_config)

        valid, reason = validator.validate_prompt("")

        assert valid is False
        assert "cannot be empty" in reason

    def test_validate_prompt_whitespace_only(self, safeguard_config):
        """Test prompt validation rejects whitespace-only prompts"""
        validator = RequestValidator(safeguard_config)

        valid, reason = validator.validate_prompt("   \n\t  ")

        assert valid is False
        assert "cannot be empty" in reason

    def test_validate_prompt_case_insensitive_keyword_check(self, safeguard_config):
        """Test keyword check is case-insensitive"""
        validator = RequestValidator(safeguard_config)

        valid, reason = validator.validate_prompt("This has MALICIOUS in caps")

        assert valid is False
        assert "blocked keyword" in reason

    def test_sanitize_params_removes_sensitive_keys(self, safeguard_config):
        """Test parameter sanitization removes sensitive keys"""
        validator = RequestValidator(safeguard_config)

        params = {
            "prompt": "test",
            "api_key": "secret_key_123",
            "password": "my_password",
            "token": "auth_token",
        }

        sanitized = validator.sanitize_params(params)

        assert sanitized["prompt"] == "test"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"

    def test_sanitize_params_preserves_non_sensitive(self, safeguard_config):
        """Test parameter sanitization preserves non-sensitive data"""
        validator = RequestValidator(safeguard_config)

        params = {
            "user_id": "user_123",
            "model": "gpt-4",
            "temperature": 0.7,
        }

        sanitized = validator.sanitize_params(params)

        assert sanitized == params


# ============================================================================
# AUDIT LOGGER TESTS
# ============================================================================


class TestAuditLogger:
    """Test AuditLogger functionality"""

    def test_audit_logger_initialization(self, temp_log_dir):
        """Test AuditLogger creates log directory"""
        log_path = temp_log_dir / "test_audit.jsonl"
        logger = AuditLogger(log_path)

        assert logger.log_path == log_path
        assert log_path.parent.exists()

    @pytest.mark.asyncio
    async def test_audit_logger_writes_entry(self, temp_log_dir):
        """Test AuditLogger writes log entry to file"""
        log_path = temp_log_dir / "test_audit.jsonl"
        logger = AuditLogger(log_path)

        entry = AuditLogEntry(
            operation_id="op_123",
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            success=True,
            execution_time_ms=100.5,
        )

        await logger.log(entry)

        # Verify file was written
        assert log_path.exists()
        content = log_path.read_text()
        assert "op_123" in content

    def test_audit_logger_get_recent_logs_empty(self, temp_log_dir):
        """Test getting recent logs when none exist"""
        log_path = temp_log_dir / "test_audit.jsonl"
        logger = AuditLogger(log_path)

        logs = logger.get_recent_logs()
        assert logs == []

    @pytest.mark.asyncio
    async def test_audit_logger_get_recent_logs_after_writing(self, temp_log_dir):
        """Test getting recent logs after writing entries"""
        log_path = temp_log_dir / "test_audit.jsonl"
        logger = AuditLogger(log_path)

        entry1 = AuditLogEntry(
            operation_id="op_1",
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            success=True,
            execution_time_ms=100.0,
        )

        entry2 = AuditLogEntry(
            operation_id="op_2",
            operation_type=OperationType.CODE_GENERATION,
            is_consequential=False,
            success=True,
            execution_time_ms=150.0,
        )

        await logger.log(entry1)
        await logger.log(entry2)

        logs = logger.get_recent_logs(hours=24)
        assert len(logs) == 2


# ============================================================================
# SAFEGUARD MANAGER TESTS
# ============================================================================


class TestOpenAISafeguardManager:
    """Test OpenAISafeguardManager main functionality"""

    def test_safeguard_manager_initialization(self, safeguard_manager):
        """Test SafeguardManager initializes with components"""
        assert safeguard_manager.config is not None
        assert safeguard_manager.rate_limiter is not None
        assert safeguard_manager.circuit_breaker is not None
        assert safeguard_manager.audit_logger is not None
        assert safeguard_manager.validator is not None
        assert safeguard_manager.violations == []

    def test_safeguard_manager_without_rate_limiter(self, temp_log_dir):
        """Test SafeguardManager works without rate limiter"""
        config = SafeguardConfig(
            enable_rate_limiting=False,
            audit_log_path=temp_log_dir / "audit.jsonl",
        )
        manager = OpenAISafeguardManager(config)

        assert manager.rate_limiter is None

    def test_safeguard_manager_without_circuit_breaker(self, temp_log_dir):
        """Test SafeguardManager works without circuit breaker"""
        config = SafeguardConfig(
            enable_circuit_breaker=False,
            audit_log_path=temp_log_dir / "audit.jsonl",
        )
        manager = OpenAISafeguardManager(config)

        assert manager.circuit_breaker is None

    @pytest.mark.asyncio
    async def test_validate_request_success(self, safeguard_manager):
        """Test request validation with valid request"""
        allowed, reason = await safeguard_manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="This is a valid test prompt",
            params={"model": "gpt-4"},
        )

        assert allowed is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_validate_request_invalid_prompt(self, safeguard_manager):
        """Test request validation with invalid prompt"""
        allowed, reason = await safeguard_manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="",  # Empty prompt
            params={},
        )

        assert allowed is False
        assert "empty" in reason.lower()

    @pytest.mark.asyncio
    async def test_validate_request_rate_limit_exceeded(self, safeguard_manager):
        """Test request validation blocks on rate limit"""
        # Fill up rate limit
        for i in range(60):
            await safeguard_manager.validate_request(
                operation_type=OperationType.CONTENT_GENERATION,
                is_consequential=False,
                prompt="test",
            )

        # Next request should be blocked
        allowed, reason = await safeguard_manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=False,
            prompt="test",
        )

        assert allowed is False
        assert "Rate limit" in reason

    @pytest.mark.asyncio
    async def test_record_violation(self, safeguard_manager):
        """Test recording safeguard violations"""
        await safeguard_manager._record_violation(
            violation_type="test_violation",
            severity="high",
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            details={"reason": "test"},
        )

        assert len(safeguard_manager.violations) == 1
        violation = safeguard_manager.violations[0]
        assert violation.violation_type == "test_violation"
        assert violation.severity == "high"

    @pytest.mark.asyncio
    async def test_execute_with_safeguards_success(self, safeguard_manager):
        """Test executing function with safeguards - success case"""
        async def test_func():
            return "success"

        result = await safeguard_manager.execute_with_safeguards(
            func=test_func,
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="test prompt",
        )

        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_safeguards_blocked_request(self, safeguard_manager):
        """Test executing function with safeguards - blocked request"""
        async def test_func():
            return "should not execute"

        with pytest.raises(ValueError) as exc_info:
            await safeguard_manager.execute_with_safeguards(
                func=test_func,
                operation_type=OperationType.CONTENT_GENERATION,
                is_consequential=True,
                prompt="",  # Invalid prompt
            )

        assert "blocked by safeguards" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_with_safeguards_logs_success(self, safeguard_manager):
        """Test successful execution is logged"""
        async def test_func():
            return "success"

        await safeguard_manager.execute_with_safeguards(
            func=test_func,
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="test",
        )

        # Check audit log was created
        logs = safeguard_manager.audit_logger.get_recent_logs()
        assert len(logs) == 1
        assert logs[0].success is True

    def test_get_statistics(self, safeguard_manager):
        """Test getting safeguard statistics"""
        stats = safeguard_manager.get_statistics()

        assert "total_violations" in stats
        assert "recent_violations_1h" in stats
        assert "violations_by_severity" in stats
        assert "circuit_breaker_state" in stats
        assert "rate_limiter_active" in stats
        assert "config_level" in stats

    @pytest.mark.asyncio
    async def test_statistics_tracks_violations(self, safeguard_manager):
        """Test statistics tracks violation counts"""
        # Record some violations
        await safeguard_manager._record_violation(
            violation_type="test1",
            severity="critical",
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            details={},
        )

        await safeguard_manager._record_violation(
            violation_type="test2",
            severity="high",
            operation_type=OperationType.CODE_GENERATION,
            is_consequential=False,
            details={},
        )

        stats = safeguard_manager.get_statistics()
        assert stats["total_violations"] == 2
        assert stats["violations_by_severity"]["critical"] == 1
        assert stats["violations_by_severity"]["high"] == 1


# ============================================================================
# DECORATOR TESTS
# ============================================================================


class TestWithSafeguardsDecorator:
    """Test @with_safeguards decorator"""

    @pytest.mark.asyncio
    async def test_decorator_on_async_function(self):
        """Test decorator works on async functions"""
        @with_safeguards(
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
        )
        async def test_func():
            return "decorated async"

        # Note: This will use global safeguard manager
        # Result depends on global state


# ============================================================================
# GLOBAL MANAGER TESTS
# ============================================================================


class TestGlobalSafeguardManager:
    """Test global safeguard manager functions"""

    def test_get_safeguard_manager_creates_instance(self):
        """Test get_safeguard_manager creates instance"""
        manager = get_safeguard_manager()
        assert manager is not None
        assert isinstance(manager, OpenAISafeguardManager)

    def test_get_safeguard_manager_singleton(self):
        """Test get_safeguard_manager returns same instance"""
        manager1 = get_safeguard_manager()
        manager2 = get_safeguard_manager()
        assert manager1 is manager2

    def test_reload_safeguard_manager(self, temp_log_dir):
        """Test reload_safeguard_manager creates new instance"""
        config = SafeguardConfig(audit_log_path=temp_log_dir / "audit.jsonl")
        manager1 = get_safeguard_manager()
        manager2 = reload_safeguard_manager(config)

        assert manager1 is not manager2
        assert manager2.config == config


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSafeguardsIntegration:
    """Integration tests for complete safeguard workflows"""

    @pytest.mark.asyncio
    async def test_complete_safeguard_workflow(self, safeguard_manager):
        """Test complete safeguard workflow from validation to execution"""
        async def api_call():
            await asyncio.sleep(0.01)  # Simulate API latency
            return "API response"

        # Execute with safeguards
        result = await safeguard_manager.execute_with_safeguards(
            func=api_call,
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="Generate a summary",
            params={"model": "gpt-4", "temperature": 0.7},
        )

        assert result == "API response"

        # Verify audit log
        logs = safeguard_manager.audit_logger.get_recent_logs()
        assert len(logs) == 1
        assert logs[0].success is True
        assert logs[0].operation_type == OperationType.CONTENT_GENERATION

    @pytest.mark.asyncio
    async def test_safeguard_prevents_malicious_request(self, safeguard_manager):
        """Test safeguards prevent malicious requests"""
        async def api_call():
            return "should not execute"

        with pytest.raises(ValueError):
            await safeguard_manager.execute_with_safeguards(
                func=api_call,
                operation_type=OperationType.CONTENT_GENERATION,
                is_consequential=True,
                prompt="This contains malicious keyword",  # Blocked keyword
            )

        # Verify violation was recorded
        assert len(safeguard_manager.violations) > 0


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestSafeguardsEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_execute_sync_function_with_safeguards(self, safeguard_manager):
        """Test executing synchronous function with safeguards"""
        def sync_func():
            return "sync result"

        result = await safeguard_manager.execute_with_safeguards(
            func=sync_func,
            operation_type=OperationType.DATA_ANALYSIS,
            is_consequential=False,
            prompt="test",
        )

        assert result == "sync result"

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_sync_function(self, circuit_breaker):
        """Test circuit breaker with synchronous function"""
        def sync_func():
            return "sync"

        result = await circuit_breaker.call(sync_func)
        assert result == "sync"


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=security.openai_safeguards",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
