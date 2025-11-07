"""
Unit tests for AgentLightning Integration

Tests tracing, observability, and performance monitoring.
"""

import pytest
from unittest.mock import Mock, patch

from core.agentlightning_integration import (
    DevSkyyLightning,
    get_lightning,
    init_lightning,
    trace_agent,
    trace_llm
)


class TestDevSkyyLightning:
    """Test DevSkyyLightning class"""

    def test_initialization_default(self):
        """Test initialization with default parameters"""
        lightning = DevSkyyLightning()
        
        assert lightning.service_name == "devskyy-agents"
        assert isinstance(lightning.metrics, dict)

    def test_initialization_custom(self):
        """Test initialization with custom parameters"""
        lightning = DevSkyyLightning(
            service_name="custom-service",
            otlp_endpoint="http://localhost:4318/v1/traces",
            enable_console=True
        )
        
        assert lightning.service_name == "custom-service"
        assert lightning.enable_console is True

    def test_metrics_initialization(self):
        """Test metrics are properly initialized"""
        lightning = DevSkyyLightning()
        
        assert lightning.metrics["total_operations"] == 0
        assert lightning.metrics["successful_operations"] == 0
        assert lightning.metrics["failed_operations"] == 0

    @patch('core.agentlightning_integration.LLMProxy')
    def test_create_llm_proxy(self, mock_proxy):
        """Test creating LLM proxy"""
        lightning = DevSkyyLightning()
        
        lightning.create_llm_proxy(
            model="gpt-4",
            api_key="test_key"
        )
        
        mock_proxy.assert_called_once()


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_lightning_creates_instance(self):
        """Test get_lightning creates global instance"""
        instance = get_lightning()
        
        assert instance is not None
        assert isinstance(instance, DevSkyyLightning)

    def test_init_lightning_creates_new_instance(self):
        """Test init_lightning creates new instance"""
        instance = init_lightning(
            service_name="test-service",
            enable_console=True
        )
        
        assert instance.service_name == "test-service"


class TestDecorators:
    """Test decorator functions"""

    def test_trace_agent_decorator(self):
        """Test trace_agent decorator"""
        @trace_agent("test_operation", agent_id="test_agent")
        def test_function():
            return "test_result"
        
        result = test_function()
        assert result == "test_result"

    def test_trace_agent_decorator_with_exception(self):
        """Test trace_agent decorator handles exceptions"""
        @trace_agent("test_operation", agent_id="test_agent")
        def failing_function():
            error_message = "Test error"
            raise ValueError(error_message)
        
        with pytest.raises(ValueError):
            failing_function()