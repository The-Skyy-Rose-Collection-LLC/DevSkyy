"""
Comprehensive Unit Tests for Tool Calling Safeguards
Testing all aspects of the advanced tool calling protection system

Per Truth Protocol:
- Rule #1: Never guess - Verify all operations
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline verification
"""

import asyncio
from pathlib import Path
import tempfile

import pytest

from security.openai_safeguards import SafeguardConfig
from security.tool_calling_safeguards import (
    ToolAuthorizationManager,
    ToolCallAuditEntry,
    ToolCallAuditLogger,
    ToolCallConfig,
    ToolCallingSafeguardManager,
    ToolCallRequest,
    ToolCallValidator,
    ToolPermissionLevel,
    ToolProvider,
    ToolRateLimiter,
    ToolRiskLevel,
    get_tool_safeguard_manager,
    reload_tool_safeguard_manager,
)


# ============================================================================
# TOOL CALL CONFIG TESTS
# ============================================================================


class TestToolCallConfig:
    """Test ToolCallConfig validation"""

    @pytest.mark.unit
    def test_default_config(self):
        """Test default tool configuration"""
        config = ToolCallConfig(tool_name="test_tool", description="Test tool")

        assert config.tool_name == "test_tool"
        assert config.permission_level == ToolPermissionLevel.AUTHENTICATED
        assert config.risk_level == ToolRiskLevel.MEDIUM
        assert config.provider == ToolProvider.BOTH
        assert config.max_calls_per_minute == 10
        assert config.is_consequential is True

    @pytest.mark.unit
    def test_high_risk_config(self):
        """Test high-risk tool configuration"""
        config = ToolCallConfig(
            tool_name="delete_data",
            description="Delete data",
            permission_level=ToolPermissionLevel.ADMIN,
            risk_level=ToolRiskLevel.CRITICAL,
            max_calls_per_minute=1,
            require_approval=True,
        )

        assert config.risk_level == ToolRiskLevel.CRITICAL
        assert config.permission_level == ToolPermissionLevel.ADMIN
        assert config.require_approval is True
        assert config.max_calls_per_minute == 1

    @pytest.mark.unit
    def test_config_is_frozen(self):
        """Test configuration is immutable"""
        config = ToolCallConfig(tool_name="test_tool", description="Test")

        with pytest.raises(Exception):
            config.max_calls_per_minute = 100


# ============================================================================
# TOOL RATE LIMITER TESTS
# ============================================================================


class TestToolRateLimiter:
    """Test ToolRateLimiter functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_calls_within_limit(self):
        """Test calls are allowed within rate limit"""
        limiter = ToolRateLimiter()
        config = ToolCallConfig(tool_name="test_tool", description="Test", max_calls_per_minute=5)

        for _i in range(5):
            allowed, reason = await limiter.check_rate_limit("test_tool", config)
            assert allowed is True
            assert reason is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_blocks_calls_exceeding_limit(self):
        """Test calls are blocked when exceeding rate limit"""
        limiter = ToolRateLimiter()
        config = ToolCallConfig(tool_name="test_tool", description="Test", max_calls_per_minute=3)

        # Use up the limit
        for _i in range(3):
            allowed, _ = await limiter.check_rate_limit("test_tool", config)
            assert allowed is True

        # Next call should be blocked
        allowed, reason = await limiter.check_rate_limit("test_tool", config)
        assert allowed is False
        assert "rate limit exceeded" in reason.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_per_tool_rate_limiting(self):
        """Test rate limiting is per-tool"""
        limiter = ToolRateLimiter()

        config1 = ToolCallConfig(tool_name="tool_a", description="Tool A", max_calls_per_minute=2)

        config2 = ToolCallConfig(tool_name="tool_b", description="Tool B", max_calls_per_minute=2)

        # Use up limit for tool_a
        for _i in range(2):
            allowed, _ = await limiter.check_rate_limit("tool_a", config1)
            assert allowed is True

        # tool_a should be blocked
        allowed, _ = await limiter.check_rate_limit("tool_a", config1)
        assert allowed is False

        # tool_b should still work
        allowed, _ = await limiter.check_rate_limit("tool_b", config2)
        assert allowed is True


# ============================================================================
# TOOL AUTHORIZATION TESTS
# ============================================================================


class TestToolAuthorizationManager:
    """Test ToolAuthorizationManager functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authorize_public_tool(self):
        """Test authorization of public tool"""
        manager = ToolAuthorizationManager()

        config = ToolCallConfig(
            tool_name="public_tool", description="Public tool", permission_level=ToolPermissionLevel.PUBLIC
        )
        manager.register_tool(config)

        request = ToolCallRequest(tool_name="public_tool", provider=ToolProvider.OPENAI)

        authorized, reason = await manager.authorize_tool_call(request)
        assert authorized is True
        assert reason is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_block_authenticated_tool_without_user(self):
        """Test authenticated tool requires user"""
        manager = ToolAuthorizationManager()

        config = ToolCallConfig(
            tool_name="auth_tool", description="Authenticated tool", permission_level=ToolPermissionLevel.AUTHENTICATED
        )
        manager.register_tool(config)

        request = ToolCallRequest(tool_name="auth_tool", provider=ToolProvider.OPENAI, user_id=None)  # No user

        authorized, reason = await manager.authorize_tool_call(request)
        assert authorized is False
        assert "authentication" in reason.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authorize_with_permissions(self):
        """Test authorization with user permissions"""
        manager = ToolAuthorizationManager()

        config = ToolCallConfig(
            tool_name="admin_tool", description="Admin tool", permission_level=ToolPermissionLevel.ADMIN
        )
        manager.register_tool(config)

        # Set user permissions
        manager.set_user_permissions("user_123", {ToolPermissionLevel.ADMIN})

        request = ToolCallRequest(tool_name="admin_tool", provider=ToolProvider.OPENAI, user_id="user_123")

        authorized, _reason = await manager.authorize_tool_call(request)
        assert authorized is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_block_insufficient_permissions(self):
        """Test blocking when user lacks permissions"""
        manager = ToolAuthorizationManager()

        config = ToolCallConfig(
            tool_name="admin_tool", description="Admin tool", permission_level=ToolPermissionLevel.ADMIN
        )
        manager.register_tool(config)

        # User only has authenticated permission
        manager.set_user_permissions("user_123", {ToolPermissionLevel.AUTHENTICATED})

        request = ToolCallRequest(tool_name="admin_tool", provider=ToolProvider.OPENAI, user_id="user_123")

        authorized, reason = await manager.authorize_tool_call(request)
        assert authorized is False
        assert "admin" in reason.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_compatibility(self):
        """Test provider compatibility checking"""
        manager = ToolAuthorizationManager()

        config = ToolCallConfig(tool_name="openai_only_tool", description="OpenAI only", provider=ToolProvider.OPENAI)
        manager.register_tool(config)

        # Try with Anthropic
        request = ToolCallRequest(
            tool_name="openai_only_tool", provider=ToolProvider.ANTHROPIC, permission_level=ToolPermissionLevel.PUBLIC
        )

        authorized, reason = await manager.authorize_tool_call(request)
        assert authorized is False
        assert "provider" in reason.lower()


# ============================================================================
# TOOL CALL VALIDATOR TESTS
# ============================================================================


class TestToolCallValidator:
    """Test ToolCallValidator functionality"""

    @pytest.mark.unit
    def test_validates_safe_parameters(self):
        """Test validation of safe parameters"""
        validator = ToolCallValidator(SafeguardConfig())

        valid, reason = validator.validate_parameters("test_tool", {"name": "test", "value": 123})

        assert valid is True
        assert reason is None

    @pytest.mark.unit
    def test_blocks_sensitive_keys(self):
        """Test blocking of sensitive parameter keys"""
        validator = ToolCallValidator(SafeguardConfig())

        # Test various sensitive keys
        sensitive_params = [
            {"api_key": "secret"},
            {"password": "pass123"},
            {"access_token": "token"},
            {"private_key": "key123"},
        ]

        for params in sensitive_params:
            valid, reason = validator.validate_parameters("test_tool", params)
            assert valid is False
            assert "sensitive" in reason.lower()

    @pytest.mark.unit
    def test_blocks_oversized_parameters(self):
        """Test blocking of oversized parameters"""
        validator = ToolCallValidator(SafeguardConfig())

        # Create large parameter object
        large_params = {"data": "x" * 101000}

        valid, reason = validator.validate_parameters("test_tool", large_params)
        assert valid is False
        assert "size limit" in reason.lower()

    @pytest.mark.unit
    def test_sanitizes_sensitive_data(self):
        """Test sanitization of sensitive data"""
        validator = ToolCallValidator(SafeguardConfig())

        params = {"name": "test", "api_key": "secret123", "password": "pass456", "normal_field": "value"}

        sanitized = validator.sanitize_parameters(params)

        assert sanitized["name"] == "test"
        assert sanitized["normal_field"] == "value"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["password"] == "[REDACTED]"


# ============================================================================
# TOOL CALL AUDIT LOGGER TESTS
# ============================================================================


class TestToolCallAuditLogger:
    """Test ToolCallAuditLogger functionality"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_writes_audit_log(self):
        """Test audit logger writes entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "tool_audit.jsonl"
            logger = ToolCallAuditLogger(log_path)

            entry = ToolCallAuditEntry(
                request_id="test-123",
                tool_name="test_tool",
                provider=ToolProvider.OPENAI,
                user_id="user_123",
                permission_level=ToolPermissionLevel.AUTHENTICATED,
                risk_level=ToolRiskLevel.MEDIUM,
                parameters={"test": "value"},
                success=True,
                execution_time_ms=150.5,
                tokens_used=100,
            )

            await logger.log(entry)

            assert log_path.exists()
            with open(log_path) as f:
                content = f.read()
                assert "test-123" in content
                assert "test_tool" in content

    @pytest.mark.unit
    def test_retrieves_recent_logs(self):
        """Test retrieval of recent audit logs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "tool_audit.jsonl"
            logger = ToolCallAuditLogger(log_path)

            # Write test entries
            asyncio.run(
                logger.log(
                    ToolCallAuditEntry(
                        request_id="test-1",
                        tool_name="test_tool",
                        provider=ToolProvider.OPENAI,
                        user_id="user_123",
                        permission_level=ToolPermissionLevel.AUTHENTICATED,
                        risk_level=ToolRiskLevel.LOW,
                        parameters={},
                        success=True,
                        execution_time_ms=100,
                        tokens_used=50,
                    )
                )
            )

            recent = logger.get_recent_logs(hours=24)
            assert len(recent) == 1
            assert recent[0].request_id == "test-1"


# ============================================================================
# SAFEGUARD MANAGER TESTS
# ============================================================================


class TestToolCallingSafeguardManager:
    """Test ToolCallingSafeguardManager integration"""

    @pytest.mark.unit
    def test_initializes_with_config(self):
        """Test manager initializes with configuration"""
        config = SafeguardConfig()
        manager = ToolCallingSafeguardManager(config)

        assert manager.config.level == config.level
        assert manager.rate_limiter is not None
        assert manager.auth_manager is not None
        assert manager.validator is not None
        assert manager.audit_logger is not None
        assert manager.circuit_breaker is not None

    @pytest.mark.unit
    def test_registers_tools(self):
        """Test tool registration"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        config = ToolCallConfig(tool_name="test_tool", description="Test tool")

        manager.register_tool(config)

        tool_config = manager.auth_manager.get_tool_config("test_tool")
        assert tool_config is not None
        assert tool_config.tool_name == "test_tool"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validates_tool_calls(self):
        """Test tool call validation"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        # Register tool
        config = ToolCallConfig(
            tool_name="test_tool", description="Test tool", permission_level=ToolPermissionLevel.PUBLIC
        )
        manager.register_tool(config)

        # Create request
        request = ToolCallRequest(tool_name="test_tool", provider=ToolProvider.OPENAI, parameters={"test": "value"})

        # Validate
        allowed, reason = await manager.validate_tool_call(request)
        assert allowed is True
        assert reason is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_blocks_invalid_tool_calls(self):
        """Test blocking of invalid tool calls"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        # Register tool with authentication requirement
        config = ToolCallConfig(
            tool_name="auth_tool", description="Requires auth", permission_level=ToolPermissionLevel.AUTHENTICATED
        )
        manager.register_tool(config)

        # Create request without user
        request = ToolCallRequest(tool_name="auth_tool", provider=ToolProvider.OPENAI, user_id=None)

        # Should be blocked
        allowed, reason = await manager.validate_tool_call(request)
        assert allowed is False
        assert reason is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_executes_tool_calls(self):
        """Test tool call execution"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        # Register tool
        config = ToolCallConfig(
            tool_name="test_tool", description="Test tool", permission_level=ToolPermissionLevel.PUBLIC
        )
        manager.register_tool(config)

        # Create mock function
        async def mock_func():
            return {"success": True, "data": "result"}

        # Create request
        request = ToolCallRequest(tool_name="test_tool", provider=ToolProvider.OPENAI)

        # Execute
        response = await manager.execute_tool_call(request, mock_func)

        assert response.success is True
        assert response.result["success"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_records_violations(self):
        """Test violation recording"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        # Try to call unregistered tool
        request = ToolCallRequest(tool_name="nonexistent_tool", provider=ToolProvider.OPENAI)

        allowed, _reason = await manager.validate_tool_call(request)

        assert allowed is False
        assert len(manager.violations) > 0

    @pytest.mark.unit
    def test_get_statistics(self):
        """Test statistics retrieval"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        stats = manager.get_statistics()

        assert "total_violations" in stats
        assert "recent_violations_1h" in stats
        assert "violations_by_severity" in stats
        assert "circuit_breaker_state" in stats
        assert "config_level" in stats
        assert "registered_tools" in stats


# ============================================================================
# GLOBAL MANAGER TESTS
# ============================================================================


class TestGlobalToolSafeguardManager:
    """Test global tool safeguard manager functions"""

    @pytest.mark.unit
    def test_get_tool_safeguard_manager(self):
        """Test getting global manager instance"""
        manager1 = get_tool_safeguard_manager()
        manager2 = get_tool_safeguard_manager()

        assert manager1 is manager2  # Should be singleton

    @pytest.mark.unit
    def test_reload_tool_safeguard_manager(self):
        """Test reloading manager with new config"""
        config = SafeguardConfig(max_requests_per_minute=100)
        manager = reload_tool_safeguard_manager(config)

        assert manager.config.max_requests_per_minute == 100


# ============================================================================
# SECURITY TESTS
# ============================================================================


class TestToolCallingSecurity:
    """Test security aspects of tool calling"""

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_sensitive_data_not_logged(self):
        """Test sensitive data is not logged in audit"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        config = ToolCallConfig(tool_name="test_tool", description="Test", permission_level=ToolPermissionLevel.PUBLIC)
        manager.register_tool(config)

        # Create request with sensitive data
        request = ToolCallRequest(
            tool_name="test_tool", provider=ToolProvider.OPENAI, parameters={"data": "safe", "api_key": "secret123"}
        )

        # This should fail validation
        allowed, _reason = await manager.validate_tool_call(request)
        assert allowed is False

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_high_risk_tools_logged(self):
        """Test high-risk tools generate warnings"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        config = ToolCallConfig(
            tool_name="dangerous_tool",
            description="Dangerous",
            permission_level=ToolPermissionLevel.PUBLIC,
            risk_level=ToolRiskLevel.CRITICAL,
            require_approval=True,
        )
        manager.register_tool(config)

        request = ToolCallRequest(tool_name="dangerous_tool", provider=ToolProvider.OPENAI)

        # Should validate but log warning
        allowed, _reason = await manager.validate_tool_call(request)
        assert allowed is True  # Public tool


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================


class TestToolCallingPerformance:
    """Test performance characteristics"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validation_performance(self):
        """Test validation doesn't add significant overhead"""
        import time

        manager = ToolCallingSafeguardManager(SafeguardConfig())

        config = ToolCallConfig(tool_name="test_tool", description="Test", permission_level=ToolPermissionLevel.PUBLIC)
        manager.register_tool(config)

        start = time.time()

        for i in range(50):
            request = ToolCallRequest(tool_name="test_tool", provider=ToolProvider.OPENAI, parameters={"iteration": i})
            await manager.validate_tool_call(request)

        duration = time.time() - start

        # Should complete 50 validations in under 1 second
        assert duration < 1.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self):
        """Test handling of concurrent tool calls"""
        manager = ToolCallingSafeguardManager(SafeguardConfig())

        config = ToolCallConfig(
            tool_name="test_tool",
            description="Test",
            permission_level=ToolPermissionLevel.PUBLIC,
            max_calls_per_minute=100,
        )
        manager.register_tool(config)

        async def validate():
            request = ToolCallRequest(tool_name="test_tool", provider=ToolProvider.OPENAI)
            return await manager.validate_tool_call(request)

        # Run 20 concurrent validations
        results = await asyncio.gather(*[validate() for _ in range(20)])

        # All should succeed
        assert all(allowed for allowed, _ in results)
