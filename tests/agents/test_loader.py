"""
Unit tests for Agent Configuration Loader

Tests configuration loading, validation, caching, and error handling.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from pydantic import ValidationError

from agents.loader import (
    AgentConfigLoader,
    AgentConfig,
    AgentCapability,
    LoaderError,
    ConfigValidationError,
    ConfigNotFoundError,
    load_agent_config
)


class TestAgentCapability:
    """Test AgentCapability dataclass"""

    def test_capability_creation_minimal(self):
        """Test creating capability with minimal fields"""
        cap = AgentCapability(name="test_cap", confidence=0.85)
        assert cap.name == "test_cap"
        assert cap.confidence == 0.85
        assert cap.keywords == []
        assert cap.dependencies == []

    def test_capability_creation_full(self):
        """Test creating capability with all fields"""
        cap = AgentCapability(
            name="python_gen",
            confidence=0.92,
            keywords=["python", "code", "generate"],
            dependencies=["ast", "black"]
        )
        assert cap.name == "python_gen"
        assert cap.confidence == 0.92
        assert len(cap.keywords) == 3
        assert len(cap.dependencies) == 2


class TestAgentConfig:
    """Test AgentConfig Pydantic model"""

    def test_minimal_config(self):
        """Test creating config with minimal required fields"""
        config = AgentConfig(
            agent_id="test_01",
            agent_name="Test Agent",
            agent_type="test"
        )
        assert config.agent_id == "test_01"
        assert config.agent_name == "Test Agent"
        assert config.agent_type == "test"
        assert config.priority == 50
        assert config.enabled is True

    def test_full_config(self, valid_config_data):
        """Test creating config with all fields"""
        config = AgentConfig(**valid_config_data)
        assert config.agent_id == "test_agent_01"
        assert config.priority == 75
        assert len(config.capabilities) == 1

    def test_config_validation_empty_agent_id(self):
        """Test validation fails for empty agent_id"""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                agent_id="",
                agent_name="Test",
                agent_type="test"
            )
        assert "agent_id" in str(exc_info.value)

    def test_config_validation_priority_too_high(self):
        """Test validation fails for priority > 100"""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="test_01",
                agent_name="Test",
                agent_type="test",
                priority=150
            )

    def test_agent_type_normalization(self):
        """Test agent_type is normalized to lowercase"""
        config = AgentConfig(
            agent_id="test_01",
            agent_name="Test",
            agent_type="CODE_GENERATOR"
        )
        assert config.agent_type == "code_generator"

    def test_capabilities_validation_confidence_range(self):
        """Test capabilities confidence must be 0.0-1.0"""
        with pytest.raises(ValidationError):
            AgentConfig(
                agent_id="test_01",
                agent_name="Test",
                agent_type="test",
                capabilities=[{"name": "test", "confidence": 1.5}]
            )

    def test_to_capability_objects(self, valid_config_data):
        """Test converting capabilities dict to AgentCapability objects"""
        config = AgentConfig(**valid_config_data)
        caps = config.to_capability_objects()
        
        assert len(caps) == 1
        assert isinstance(caps[0], AgentCapability)
        assert caps[0].name == "test_capability"


class TestAgentConfigLoader:
    """Test AgentConfigLoader class"""

    def test_loader_initialization_default(self):
        """Test loader initializes with default config directory"""
        loader = AgentConfigLoader()
        assert loader.config_dir == Path.cwd() / "config" / "agents"
        assert loader._cache == {}

    def test_load_config_success(self, config_loader):
        """Test loading a valid configuration"""
        config = config_loader.load_config("code_generator_01")
        
        assert config.agent_id == "code_generator_01"
        assert config.agent_name == "Python Code Generator"
        assert config.agent_type == "code_generator"

    def test_load_config_not_found(self, config_loader):
        """Test loading non-existent configuration"""
        with pytest.raises(ConfigNotFoundError) as exc_info:
            config_loader.load_config("nonexistent_agent")
        
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_config_caching(self, config_loader):
        """Test configuration caching works correctly"""
        config1 = config_loader.load_config("code_generator_01")
        config2 = config_loader.load_config("code_generator_01")
        
        assert config1 is config2
        assert "code_generator_01" in config_loader._cache

    def test_load_all_configs(self, config_loader):
        """Test loading all configurations"""
        configs = config_loader.load_all_configs()
        
        assert isinstance(configs, dict)
        assert len(configs) == 4
        assert "code_generator_01" in configs

    def test_get_enabled_agents(self, config_loader):
        """Test getting only enabled agents"""
        enabled_agents = config_loader.get_enabled_agents()
        
        assert len(enabled_agents) == 3
        agent_ids = [agent.agent_id for agent in enabled_agents]
        assert "disabled_agent" not in agent_ids

    def test_get_agents_by_type(self, config_loader):
        """Test filtering agents by type"""
        code_agents = config_loader.get_agents_by_type("code_generator")
        
        assert len(code_agents) == 1
        assert code_agents[0].agent_id == "code_generator_01"

    def test_clear_cache(self, config_loader):
        """Test clearing the cache"""
        config_loader.load_config("code_generator_01")
        config_loader.clear_cache()
        
        assert len(config_loader._cache) == 0