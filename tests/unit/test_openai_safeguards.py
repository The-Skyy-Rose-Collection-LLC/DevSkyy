"""
Comprehensive Unit Tests for OpenAI Safeguards and Guardrails
Testing all aspects of the safeguard system

Per Truth Protocol:
- Rule #1: Never guess - Verify all operations
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline verification
"""

import asyncio
from pathlib import Path
import tempfile

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
    get_safeguard_manager,
    reload_safeguard_manager,
)


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================


class TestSafeguardConfig:
    """Test SafeguardConfig validation and defaults"""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default configuration values"""
        config = SafeguardConfig()

        assert config.level == SafeguardLevel.STRICT
        assert config.enforce_consequential_in_production is True
        assert config.require_audit_logging is True
        assert config.enable_rate_limiting is True
        assert config.max_requests_per_minute == 60
        assert config.max_consequential_per_hour == 100
        assert config.enable_circuit_breaker is True
        assert config.enable_request_validation is True
        assert config.enable_monitoring is True
        assert config.alert_on_violations is True

    @pytest.mark.unit
    def test_production_forces_strict_level(self, monkeypatch):
        """Test production environment forces STRICT level"""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = SafeguardConfig(level=SafeguardLevel.PERMISSIVE)

        # Should be forced to STRICT
        assert config.level == SafeguardLevel.STRICT

    @pytest.mark.unit
    def test_custom_rate_limits(self):
        """Test custom rate limit configuration"""
        config = SafeguardConfig(max_requests_per_minute=100, max_consequential_per_hour=200)

        assert config.max_requests_per_minute == 100
        assert config.max_consequential_per_hour == 200

    @pytest.mark.unit
    def test_disable_features(self):
        """Test disabling individual features"""
        config = SafeguardConfig(enable_rate_limiting=False, enable_circuit_breaker=False, enable_monitoring=False)

        assert config.enable_rate_limiting is False
        assert config.enable_circuit_breaker is False
        assert config.enable_monitoring is True  # Always enabled

    @pytest.mark.unit
    def test_config_is_frozen(self):
        """Test configuration is immutable"""
        config = SafeguardConfig()

        with pytest.raises(Exception):  # Pydantic ValidationError
            config.level = SafeguardLevel.PERMISSIVE


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================


class TestRateLimiter:
    """Test RateLimiter functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_requests_within_limit(self):
        """Test requests are allowed within rate limit"""
        limiter = RateLimiter(max_per_minute=5, max_consequential_per_hour=3)

        for _i in range(5):
            allowed, reason = await limiter.check_rate_limit(is_consequential=False)
            assert allowed is True
            assert reason is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_blocks_requests_exceeding_limit(self):
        """Test requests are blocked when exceeding rate limit"""
        limiter = RateLimiter(max_per_minute=3, max_consequential_per_hour=10)

        # Use up the limit
        for _i in range(3):
            allowed, _ = await limiter.check_rate_limit()
            assert allowed is True

        # Next request should be blocked
        allowed, reason = await limiter.check_rate_limit()
        assert allowed is False
        assert "Rate limit exceeded" in reason

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_consequential_rate_limiting(self):
        """Test separate rate limiting for consequential operations"""
        limiter = RateLimiter(max_per_minute=10, max_consequential_per_hour=2)

        # Use up consequential limit
        for _i in range(2):
            allowed, _ = await limiter.check_rate_limit(is_consequential=True)
            assert allowed is True

        # Next consequential should be blocked
        allowed, reason = await limiter.check_rate_limit(is_consequential=True)
        assert allowed is False
        assert "Consequential operation limit exceeded" in reason

        # But non-consequential should still work
        allowed, reason = await limiter.check_rate_limit(is_consequential=False)
        assert allowed is True


# ============================================================================
# CIRCUIT BREAKER TESTS
# ============================================================================


class TestCircuitBreaker:
    """Test CircuitBreaker pattern"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_successful_calls(self):
        """Test circuit breaker allows successful calls"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_opens_on_failures(self):
        """Test circuit breaker opens after failure threshold"""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

        async def failure_func():
            raise Exception("API Error")

        # Trigger failures
        for _i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failure_func)

        # Circuit should be open
        assert breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_blocks_when_open(self):
        """Test circuit breaker blocks requests when open"""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

        async def failure_func():
            raise Exception("API Error")

        # Open the circuit
        for _i in range(2):
            with pytest.raises(Exception):
                await breaker.call(failure_func)

        # Should block new requests
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failure_func)


# ============================================================================
# AUDIT LOGGER TESTS
# ============================================================================


class TestAuditLogger:
    """Test AuditLogger functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_writes_audit_log(self):
        """Test audit logger writes entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            logger = AuditLogger(log_path)

            entry = AuditLogEntry(
                operation_id="test-123",
                operation_type=OperationType.CONTENT_GENERATION,
                is_consequential=True,
                success=True,
                execution_time_ms=150.5,
            )

            await logger.log(entry)

            assert log_path.exists()
            with open(log_path) as f:
                content = f.read()
                assert "test-123" in content
                assert "CONTENT_GENERATION" in content

    @pytest.mark.unit
    def test_retrieves_recent_logs(self):
        """Test retrieval of recent audit logs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            logger = AuditLogger(log_path)

            # Write test entries
            asyncio.run(
                logger.log(
                    AuditLogEntry(
                        operation_id="test-1",
                        operation_type=OperationType.CODE_GENERATION,
                        is_consequential=True,
                        success=True,
                        execution_time_ms=100,
                    )
                )
            )

            recent = logger.get_recent_logs(hours=24)
            assert len(recent) == 1
            assert recent[0].operation_id == "test-1"


# ============================================================================
# REQUEST VALIDATOR TESTS
# ============================================================================


class TestRequestValidator:
    """Test RequestValidator functionality"""

    @pytest.mark.unit
    def test_validates_prompt_length(self):
        """Test prompt length validation"""
        config = SafeguardConfig(max_prompt_length=100)
        validator = RequestValidator(config)

        valid, reason = validator.validate_prompt("Short prompt")
        assert valid is True

        long_prompt = "x" * 101
        valid, reason = validator.validate_prompt(long_prompt)
        assert valid is False
        assert "exceeds maximum length" in reason

    @pytest.mark.unit
    def test_blocks_keywords(self):
        """Test blocked keyword detection"""
        config = SafeguardConfig(blocked_keywords=["forbidden", "banned"])
        validator = RequestValidator(config)

        valid, reason = validator.validate_prompt("This is a normal prompt")
        assert valid is True

        valid, reason = validator.validate_prompt("This contains forbidden word")
        assert valid is False
        assert "blocked keyword" in reason.lower()

    @pytest.mark.unit
    def test_rejects_empty_prompts(self):
        """Test empty prompt rejection"""
        config = SafeguardConfig()
        validator = RequestValidator(config)

        valid, reason = validator.validate_prompt("")
        assert valid is False
        assert "cannot be empty" in reason

    @pytest.mark.unit
    def test_sanitizes_params(self):
        """Test parameter sanitization"""
        config = SafeguardConfig()
        validator = RequestValidator(config)

        params = {"model": "gpt-4", "api_key": "secret-key-123", "password": "user-password", "normal_param": "value"}

        sanitized = validator.sanitize_params(params)

        assert sanitized["model"] == "gpt-4"
        assert sanitized["normal_param"] == "value"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"


# ============================================================================
# SAFEGUARD MANAGER TESTS
# ============================================================================


class TestOpenAISafeguardManager:
    """Test OpenAISafeguardManager integration"""

    @pytest.mark.unit
    def test_initializes_with_config(self):
        """Test manager initializes with configuration"""
        config = SafeguardConfig()
        manager = OpenAISafeguardManager(config)

        assert manager.config.level == SafeguardLevel.STRICT
        assert manager.rate_limiter is not None
        assert manager.circuit_breaker is not None
        assert manager.audit_logger is not None
        assert manager.validator is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validates_requests(self):
        """Test request validation"""
        config = SafeguardConfig(max_requests_per_minute=5)
        manager = OpenAISafeguardManager(config)

        allowed, reason = await manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION, is_consequential=True, prompt="Test prompt"
        )

        assert allowed is True
        assert reason is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enforces_production_safeguards(self, monkeypatch):
        """Test production safeguard enforcement"""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = SafeguardConfig(enforce_consequential_in_production=True)
        manager = OpenAISafeguardManager(config)

        # Should block non-consequential in production
        allowed, reason = await manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION, is_consequential=False
        )

        assert allowed is False
        assert "Production environment requires" in reason

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_records_violations(self):
        """Test violation recording"""
        config = SafeguardConfig(max_requests_per_minute=1)
        manager = OpenAISafeguardManager(config)

        # Exceed rate limit
        await manager.validate_request(operation_type=OperationType.CONTENT_GENERATION, is_consequential=True)

        allowed, _ = await manager.validate_request(
            operation_type=OperationType.CONTENT_GENERATION, is_consequential=True
        )

        assert allowed is False
        assert len(manager.violations) > 0

    @pytest.mark.unit
    def test_get_statistics(self):
        """Test statistics retrieval"""
        config = SafeguardConfig()
        manager = OpenAISafeguardManager(config)

        stats = manager.get_statistics()

        assert "total_violations" in stats
        assert "recent_violations_1h" in stats
        assert "violations_by_severity" in stats
        assert "circuit_breaker_state" in stats
        assert "config_level" in stats
        assert stats["config_level"] == "strict"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSafeguardIntegration:
    """Test full safeguard integration"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_request_flow(self):
        """Test complete request flow with safeguards"""
        config = SafeguardConfig(max_requests_per_minute=10, enable_rate_limiting=True, enable_circuit_breaker=True)
        manager = OpenAISafeguardManager(config)

        async def mock_api_call():
            return {"status": "success"}

        result = await manager.execute_with_safeguards(
            func=mock_api_call,
            operation_type=OperationType.CONTENT_GENERATION,
            is_consequential=True,
            prompt="Test prompt",
            params={"model": "gpt-4"},
        )

        assert result["status"] == "success"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_handles_api_failures(self):
        """Test safeguard handling of API failures"""
        config = SafeguardConfig(failure_threshold=2)
        manager = OpenAISafeguardManager(config)

        async def failing_api_call():
            raise Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await manager.execute_with_safeguards(
                func=failing_api_call, operation_type=OperationType.CONTENT_GENERATION, is_consequential=True
            )


# ============================================================================
# GLOBAL MANAGER TESTS
# ============================================================================


class TestGlobalSafeguardManager:
    """Test global safeguard manager functions"""

    @pytest.mark.unit
    def test_get_safeguard_manager(self):
        """Test getting global manager instance"""
        manager1 = get_safeguard_manager()
        manager2 = get_safeguard_manager()

        assert manager1 is manager2  # Should be singleton

    @pytest.mark.unit
    def test_reload_safeguard_manager(self):
        """Test reloading manager with new config"""
        config = SafeguardConfig(max_requests_per_minute=100)
        manager = reload_safeguard_manager(config)

        assert manager.config.max_requests_per_minute == 100


# ============================================================================
# SECURITY TESTS
# ============================================================================


class TestSafeguardSecurity:
    """Test security aspects of safeguards"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_sensitive_data_not_logged(self):
        """Test sensitive data is not logged"""
        config = SafeguardConfig()
        validator = RequestValidator(config)

        params = {"api_key": "sk-secret123", "password": "mypassword", "token": "token123"}

        sanitized = validator.sanitize_params(params)

        for value in sanitized.values():
            assert "sk-secret" not in str(value)
            assert "mypassword" not in str(value)
            assert "token123" not in str(value)

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_production_requires_consequential(self, monkeypatch):
        """Test production enforces consequential flag"""
        monkeypatch.setenv("ENVIRONMENT", "production")

        config = SafeguardConfig(enforce_consequential_in_production=True)
        manager = OpenAISafeguardManager(config)

        allowed, reason = await manager.validate_request(
            operation_type=OperationType.SYSTEM_MODIFICATION, is_consequential=False
        )

        assert allowed is False
        assert "requires is_consequential=True" in reason


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestSafeguardPerformance:
    """Test performance characteristics of safeguards"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validation_performance(self):
        """Test validation doesn't add significant overhead"""
        import time

        config = SafeguardConfig()
        manager = OpenAISafeguardManager(config)

        start = time.time()

        for _i in range(50):
            await manager.validate_request(
                operation_type=OperationType.CONTENT_GENERATION, is_consequential=True, prompt="Test prompt"
            )

        duration = time.time() - start

        # Should complete 50 validations in under 1 second
        assert duration < 1.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        config = SafeguardConfig(max_requests_per_minute=100)
        manager = OpenAISafeguardManager(config)

        async def validate():
            return await manager.validate_request(
                operation_type=OperationType.CONTENT_GENERATION, is_consequential=True
            )

        # Run 20 concurrent validations
        results = await asyncio.gather(*[validate() for _ in range(20)])

        # All should succeed
        assert all(allowed for allowed, _ in results)
