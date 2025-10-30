"""
Unit Tests for Watchdog System
Tests health monitoring and recovery
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock

from fashion_ai_bounded_autonomy.watchdog import Watchdog
from agent.modules.base_agent import BaseAgent, AgentStatus


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, name, fail_health_check=False):
        """
        Create a test MockAgent with controllable health-check behavior.
        
        Parameters:
            name (str): Agent identifier.
            fail_health_check (bool): If True, the agent will simulate failing health checks; if False, it will simulate healthy checks.
        
        Notes:
            - Initializes an `initialize_count` counter to 0.
            - Sets the agent version to "1.0.0" via the base class initializer.
        """
        super().__init__(name, version="1.0.0")
        self.fail_health_check = fail_health_check
        self.initialize_count = 0
    
    async def initialize(self) -> bool:
        """
        Initialize the mock agent and set its status to healthy.
        
        Increments the agent's internal initialize counter and sets its status to AgentStatus.HEALTHY.
        
        Returns:
            bool: `True` if initialization succeeded.
        """
        self.initialize_count += 1
        self.status = AgentStatus.HEALTHY
        return True
    
    async def execute_core_function(self, **_kwargs):
        """
        Execute the agent's primary core function and indicate success.
        
        Returns:
            dict: A dictionary with "status" set to "success".
        """
        return {"status": "success"}
    
    async def health_check(self):
        """
        Report the agent's current health status.
        
        Returns:
            dict: `{'status': 'healthy'}` if the agent is healthy, `{'status': 'failed'}` if configured to fail health checks.
        """
        if self.fail_health_check:
            return {"status": "failed"}
        return {"status": "healthy"}


@pytest.fixture
def temp_config():
    """
    Create a temporary Watchdog configuration file and yield its path.
    
    Writes a YAML file at a temporary config/monitor.yaml containing a minimal
    watchdog configuration (enabled: True, check_interval_seconds: 1,
    error_threshold: 3). Yields the string path to the created monitor.yaml and
    removes the entire temporary directory after the caller finishes using the fixture.
    
    Returns:
        config_path (str): Filesystem path to the generated monitor.yaml file.
    """
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir()
    
    config = {
        "monitoring": {
            "watchdog": {
                "enabled": True,
                "check_interval_seconds": 1,
                "error_threshold": 3
            }
        }
    }
    
    config_path = config_dir / "monitor.yaml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    yield str(config_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def watchdog(temp_config):
    """
    Create a Watchdog instance using the provided configuration path.
    
    Parameters:
        temp_config (str): File path to the monitor configuration (e.g., config/monitor.yaml).
    
    Returns:
        Watchdog: An initialized Watchdog configured with the given config path.
    """
    return Watchdog(config_path=temp_config)


class TestWatchdogInitialization:
    """Test watchdog initialization"""

    def test_initialization(self, temp_config):
        """Test basic initialization"""
        wd = Watchdog(config_path=temp_config)
        
        assert wd.running is False
        assert wd.incident_log_path.exists()
        assert wd.config is not None


class TestHealthChecking:
    """Test health checking functionality"""

    @pytest.mark.asyncio
    async def test_check_healthy_agent(self, watchdog):
        """
        Verifies that Watchdog._check_agent does not record an error for an agent that reports healthy.
        
        Sets up a MockAgent marked healthy and a mocked orchestrator containing that agent, invokes _check_agent, and asserts the agent has no entry in watchdog.agent_error_counts.
        """
        agent = MockAgent("test_agent", fail_health_check=False)
        
        # Mock orchestrator
        orchestrator = Mock()
        orchestrator.agents = {"test_agent": agent}
        watchdog.orchestrator = orchestrator
        
        await watchdog._check_agent("test_agent", agent)
        
        # Should not increment error count
        assert "test_agent" not in watchdog.agent_error_counts

    @pytest.mark.asyncio
    async def test_check_failed_agent(self, watchdog):
        """Test checking failed agent"""
        agent = MockAgent("test_agent", fail_health_check=True)
        
        orchestrator = Mock()
        orchestrator.agents = {"test_agent": agent}
        watchdog.orchestrator = orchestrator
        
        await watchdog._check_agent("test_agent", agent)
        
        # Should increment error count
        assert watchdog.agent_error_counts.get("test_agent", 0) > 0


class TestAgentRestart:
    """Test agent restart functionality"""

    @pytest.mark.asyncio
    async def test_restart_agent(self, watchdog):
        """Test restarting failed agent"""
        agent = MockAgent("test_agent")
        
        await watchdog._restart_agent("test_agent", agent)
        
        assert agent.initialize_count > 0


class TestIncidentLogging:
    """Test incident logging"""

    def test_log_incident(self, watchdog):
        """Test logging an incident"""
        incident = {
            "type": "test_incident",
            "agent_name": "test_agent",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        watchdog._log_incident(incident)
        
        assert len(watchdog.incidents) > 0
        assert watchdog.incidents[0]["type"] == "test_incident"


class TestAgentHalting:
    """Test agent halting functionality"""

    @pytest.mark.asyncio
    async def test_halt_agent(self, watchdog):
        """Test halting an agent"""
        await watchdog._halt_agent("test_agent", "test_reason")
        
        assert "test_agent" in watchdog.halted_agents
        assert watchdog.halted_agents["test_agent"]["reason"] == "test_reason"

    @pytest.mark.asyncio
    async def test_clear_agent_halt(self, watchdog):
        """Test clearing agent halt"""
        # First halt
        await watchdog._halt_agent("test_agent", "test")
        
        # Then clear
        result = await watchdog.clear_agent_halt("test_agent", "operator")
        
        assert result["status"] == "cleared"
        assert "test_agent" not in watchdog.halted_agents


class TestWatchdogStatus:
    """Test watchdog status reporting"""

    @pytest.mark.asyncio
    async def test_get_status(self, watchdog):
        """Test getting watchdog status"""
        status = await watchdog.get_status()
        
        assert "running" in status
        assert "total_incidents" in status
        assert "halted_agents" in status