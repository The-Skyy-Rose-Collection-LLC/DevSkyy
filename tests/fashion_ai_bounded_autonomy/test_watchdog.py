"""
Unit tests for Watchdog
Tests health monitoring and recovery
"""

import asyncio
from pathlib import Path
import shutil
import tempfile
from unittest.mock import AsyncMock, Mock

import pytest

from fashion_ai_bounded_autonomy.watchdog import Watchdog


class MockAgent:
    """Mock agent for testing"""

    def __init__(self, name: str, healthy: bool = True):
        self.name = name
        self.healthy = healthy
        self.initialize_called = False

    async def health_check(self) -> dict:
        if self.healthy:
            return {"status": "healthy", "agent": self.name}
        else:
            return {"status": "failed", "agent": self.name}

    async def initialize(self) -> bool:
        self.initialize_called = True
        return True


class MockOrchestrator:
    """Mock orchestrator for testing"""

    def __init__(self):
        self.agents = {}

    def add_agent(self, name: str, agent):
        self.agents[name] = agent


@pytest.fixture
def temp_config_path():
    """Create temporary config file"""
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "monitor.yaml"

    config = {"monitoring": {"watchdog": {"check_interval_seconds": 1, "error_threshold": 3}}}

    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    yield str(config_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def watchdog(temp_config_path):
    """Create Watchdog instance"""
    return Watchdog(config_path=temp_config_path, max_restart_attempts=3)


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator"""
    return MockOrchestrator()


class TestWatchdogInitialization:
    """Test Watchdog initialization"""

    def test_init_loads_config(self, watchdog):
        """Test that initialization loads configuration"""
        assert watchdog.config is not None
        assert "check_interval_seconds" in watchdog.config

    def test_init_creates_incident_log_dir(self, watchdog):
        """Test that initialization creates incident log directory"""
        assert watchdog.incident_log_path.exists()

    def test_init_sets_defaults(self, watchdog):
        """Test that initialization sets default values"""
        assert watchdog.max_restart_attempts == 3
        assert watchdog.running is False
        assert len(watchdog.agent_error_counts) == 0


class TestStartStop:
    """Test starting and stopping watchdog"""

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, watchdog, mock_orchestrator):
        """Test that start sets running flag"""
        task = asyncio.create_task(watchdog.start(mock_orchestrator))
        await asyncio.sleep(0.1)

        assert watchdog.running is True

        await watchdog.stop()
        await task

    @pytest.mark.asyncio
    async def test_stop_clears_running_flag(self, watchdog, mock_orchestrator):
        """Test that stop clears running flag"""
        task = asyncio.create_task(watchdog.start(mock_orchestrator))
        await asyncio.sleep(0.1)

        await watchdog.stop()
        await task

        assert watchdog.running is False


class TestHealthChecking:
    """Test agent health checking"""

    @pytest.mark.asyncio
    async def test_check_healthy_agent(self, watchdog):
        """Test checking healthy agent"""
        agent = MockAgent("test_agent", healthy=True)

        await watchdog._check_agent("test_agent", agent)

        # No errors should be recorded
        assert "test_agent" not in watchdog.agent_error_counts

    @pytest.mark.asyncio
    async def test_check_failed_agent(self, watchdog):
        """Test checking failed agent"""
        agent = MockAgent("test_agent", healthy=False)

        await watchdog._check_agent("test_agent", agent)

        # Error should be recorded
        assert "test_agent" in watchdog.agent_error_counts


class TestAgentFailureHandling:
    """Test handling agent failures"""

    @pytest.mark.asyncio
    async def test_handle_agent_failure_increments_count(self, watchdog):
        """Test that failure handling increments error count"""
        agent = MockAgent("test_agent")

        await watchdog._handle_agent_failure("test_agent", agent)

        assert watchdog.agent_error_counts["test_agent"] == 1

    @pytest.mark.asyncio
    async def test_handle_repeated_failures_halts_agent(self, watchdog):
        """Test that repeated failures halt the agent"""
        agent = MockAgent("test_agent")

        # Trigger failures beyond threshold
        for _i in range(5):
            await watchdog._handle_agent_failure("test_agent", agent)

        assert "test_agent" in watchdog.halted_agents


class TestAgentRestart:
    """Test agent restart functionality"""

    @pytest.mark.asyncio
    async def test_restart_agent_success(self, watchdog):
        """Test successful agent restart"""
        agent = MockAgent("test_agent")

        await watchdog._restart_agent("test_agent", agent)

        assert agent.initialize_called is True
        assert watchdog.agent_restart_counts["test_agent"] == 1

    @pytest.mark.asyncio
    async def test_restart_agent_max_attempts_exceeded(self, watchdog):
        """Test that agent is halted after max restart attempts"""
        agent = MockAgent("test_agent")

        # Exceed max restart attempts
        for _i in range(5):
            await watchdog._restart_agent("test_agent", agent)

        assert "test_agent" in watchdog.halted_agents


class TestAgentHalt:
    """Test agent halting"""

    @pytest.mark.asyncio
    async def test_halt_agent_records_details(self, watchdog):
        """Test that halting records agent details"""
        await watchdog._halt_agent("test_agent", "test reason")

        assert "test_agent" in watchdog.halted_agents
        assert watchdog.halted_agents["test_agent"]["reason"] == "test reason"

    @pytest.mark.asyncio
    async def test_halt_agent_creates_incident(self, watchdog):
        """Test that halting creates incident report"""
        await watchdog._halt_agent("test_agent", "test reason")

        assert len(watchdog.incidents) > 0
        assert watchdog.incidents[-1]["type"] == "agent_halted"


class TestAgentRecovery:
    """Test agent recovery handling"""

    @pytest.mark.asyncio
    async def test_handle_agent_recovery_clears_counts(self, watchdog):
        """Test that recovery clears error and restart counts"""
        watchdog.agent_error_counts["test_agent"] = 2
        watchdog.agent_restart_counts["test_agent"] = 1

        await watchdog._handle_agent_recovery("test_agent")

        assert "test_agent" not in watchdog.agent_error_counts
        assert "test_agent" not in watchdog.agent_restart_counts


class TestIncidentLogging:
    """Test incident logging"""

    def test_log_incident(self, watchdog):
        """Test logging incident"""
        incident = {"type": "test_incident", "agent_name": "test_agent", "timestamp": "2024-01-01T00:00:00"}

        watchdog._log_incident(incident)

        assert len(watchdog.incidents) == 1
        assert watchdog.incidents[0]["type"] == "test_incident"


class TestOperatorNotification:
    """Test operator notification"""

    @pytest.mark.asyncio
    async def test_notify_operator_creates_notification_file(self, watchdog):
        """Test that notification creates file"""
        incident = {"type": "critical_failure", "agent_name": "test_agent"}

        await watchdog._notify_operator(incident)

        notification_file = Path("fashion_ai_bounded_autonomy/notifications.json")
        assert notification_file.exists()


class TestGetStatus:
    """Test getting watchdog status"""

    @pytest.mark.asyncio
    async def test_get_status_complete(self, watchdog):
        """Test getting complete status"""
        status = await watchdog.get_status()

        assert "running" in status
        assert "total_incidents" in status
        assert "halted_agents" in status

    @pytest.mark.asyncio
    async def test_get_status_includes_error_counts(self, watchdog):
        """Test that status includes error counts"""
        watchdog.agent_error_counts["agent1"] = 2

        status = await watchdog.get_status()

        assert "agent1" in status["agents_with_errors"]
        assert status["agents_with_errors"]["agent1"] == 2


class TestClearAgentHalt:
    """Test clearing agent halt status"""

    @pytest.mark.asyncio
    async def test_clear_agent_halt_removes_halt(self, watchdog):
        """Test that clearing removes halt status"""
        await watchdog._halt_agent("test_agent", "test")

        result = await watchdog.clear_agent_halt("test_agent", "operator")

        assert result["status"] == "cleared"
        assert "test_agent" not in watchdog.halted_agents

    @pytest.mark.asyncio
    async def test_clear_nonhalted_agent_returns_error(self, watchdog):
        """Test clearing non-halted agent returns error"""
        result = await watchdog.clear_agent_halt("nonexistent", "operator")

        assert "error" in result


class TestEdgeCases:
    """Test edge cases"""

    @pytest.mark.asyncio
    async def test_check_agent_with_exception(self, watchdog):
        """Test handling exception during health check"""
        agent = Mock()
        agent.health_check = AsyncMock(side_effect=Exception("Test error"))

        await watchdog._check_agent("test_agent", agent)

        # Should log incident without crashing
        assert len(watchdog.incidents) > 0
