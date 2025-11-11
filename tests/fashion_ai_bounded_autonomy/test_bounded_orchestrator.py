"""
Unit tests for BoundedOrchestrator
Tests bounded orchestration with approval workflows
"""

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from agent.orchestrator import ExecutionPriority
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel
from fashion_ai_bounded_autonomy.bounded_orchestrator import BoundedOrchestrator


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def __init__(self, name: str, version: str = "1.0.0"):
        super().__init__(name, version)
        self.status = AgentStatus.HEALTHY

    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **_kwargs) -> dict:
        return {"status": "success", "result": "completed"}

    async def health_check(self) -> dict:
        return {"status": "healthy", "agent": self.agent_name}


@pytest.fixture
def orchestrator():
    """Create BoundedOrchestrator instance"""
    return BoundedOrchestrator(max_concurrent_tasks=50, local_only=True, auto_approve_low_risk=True)


@pytest.fixture
def mock_agent():
    """Create mock agent"""
    return MockAgent("test_agent", "1.0.0")


class TestBoundedOrchestratorInitialization:
    """Test orchestrator initialization"""

    def test_init_sets_defaults(self, orchestrator):
        """Test that initialization sets default values"""
        assert orchestrator.local_only is True
        assert orchestrator.auto_approve_low_risk is True
        assert orchestrator.system_paused is False
        assert orchestrator.emergency_stop_active is False
        assert len(orchestrator.wrapped_agents) == 0

    def test_init_creates_approval_system(self, orchestrator):
        """Test that initialization creates approval system"""
        assert orchestrator.approval_system is not None


class TestRegisterAgent:
    """Test agent registration"""

    @pytest.mark.asyncio
    async def test_register_agent_basic(self, orchestrator, mock_agent):
        """Test basic agent registration"""
        success = await orchestrator.register_agent(
            agent=mock_agent, capabilities=["test_capability"], priority=ExecutionPriority.MEDIUM
        )

        assert success is True
        assert mock_agent.agent_name in orchestrator.wrapped_agents

    @pytest.mark.asyncio
    async def test_register_agent_creates_wrapper(self, orchestrator, mock_agent):
        """Test that registration creates bounded wrapper"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_capability"])

        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapper is not None
        assert wrapper.wrapped_agent == mock_agent

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self, orchestrator):
        """Test registering multiple agents"""
        agents = [MockAgent(f"agent_{i}") for i in range(3)]

        for agent in agents:
            await orchestrator.register_agent(agent=agent, capabilities=[f"cap_{agent.agent_name}"])

        assert len(orchestrator.wrapped_agents) == 3


class TestExecuteTask:
    """Test task execution"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_task(self, orchestrator, mock_agent):
        """Test executing low-risk task"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["read_data"])

        result = await orchestrator.execute_task(
            task_type="read_data",
            parameters={"source": "test.csv"},
            required_capabilities=["read_data"],
            priority=ExecutionPriority.MEDIUM,
        )

        # Low-risk tasks may execute immediately depending on configuration
        assert "status" in result

    @pytest.mark.asyncio
    async def test_execute_high_risk_task_requires_approval(self, orchestrator, mock_agent):
        """Test that high-risk tasks require approval"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["write_data"])

        result = await orchestrator.execute_task(
            task_type="update_database",
            parameters={"data": "test"},
            required_capabilities=["write_data"],
            priority=ExecutionPriority.HIGH,
            require_approval=True,
        )

        assert result["status"] == "pending_approval"
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_execute_task_emergency_stop(self, orchestrator, mock_agent):
        """Test that emergency stop blocks task execution"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        await orchestrator.emergency_stop("Test emergency", "operator")

        result = await orchestrator.execute_task(
            task_type="test_task", parameters={}, required_capabilities=["test_cap"]
        )

        assert result["status"] == "blocked"
        assert "emergency" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_task_system_paused(self, orchestrator, mock_agent):
        """Test that paused system queues tasks"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        await orchestrator.pause_system("operator")

        result = await orchestrator.execute_task(
            task_type="test_task", parameters={}, required_capabilities=["test_cap"]
        )

        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_execute_task_no_capable_agents(self, orchestrator):
        """Test executing task with no capable agents"""
        result = await orchestrator.execute_task(
            task_type="test_task", parameters={}, required_capabilities=["nonexistent_capability"]
        )

        assert "error" in result


class TestExecuteApprovedTask:
    """Test executing approved tasks"""

    @pytest.mark.asyncio
    async def test_execute_approved_task(self, orchestrator, mock_agent):
        """Test executing an approved task"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        # Create task requiring approval
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={"test": "value"},
            required_capabilities=["test_cap"],
            require_approval=True,
        )

        task_id = result["task_id"]

        # Execute approved task
        exec_result = await orchestrator.execute_approved_task(task_id=task_id, approved_by="operator")

        assert "status" in exec_result

    @pytest.mark.asyncio
    async def test_execute_approved_nonexistent_task(self, orchestrator):
        """Test executing non-existent approved task"""
        result = await orchestrator.execute_approved_task(task_id="nonexistent", approved_by="operator")

        assert result["status"] == "error"


class TestRiskAssessment:
    """Test task risk assessment"""

    def test_assess_task_risk_critical(self, orchestrator):
        """Test assessment of critical tasks"""
        risk = orchestrator._assess_task_risk(task_type="deploy_production", parameters={}, agents=["agent1"])

        assert risk == ActionRiskLevel.CRITICAL

    def test_assess_task_risk_high(self, orchestrator):
        """Test assessment of high-risk tasks"""
        risk = orchestrator._assess_task_risk(task_type="update_records", parameters={}, agents=["agent1"])

        assert risk == ActionRiskLevel.HIGH

    def test_assess_task_risk_medium(self, orchestrator):
        """Test assessment of medium-risk tasks"""
        risk = orchestrator._assess_task_risk(task_type="analyze_data", parameters={}, agents=["agent1"])

        assert risk == ActionRiskLevel.MEDIUM

    def test_assess_task_risk_low(self, orchestrator):
        """Test assessment of low-risk tasks"""
        risk = orchestrator._assess_task_risk(task_type="read_logs", parameters={}, agents=["agent1"])

        assert risk == ActionRiskLevel.LOW

    def test_assess_task_risk_multiple_agents_increases_risk(self, orchestrator):
        """Test that multiple agents increase risk level"""
        risk = orchestrator._assess_task_risk(
            task_type="analyze_data", parameters={}, agents=["agent1", "agent2", "agent3", "agent4"]
        )

        assert risk == ActionRiskLevel.HIGH


class TestEmergencyStop:
    """Test emergency stop functionality"""

    @pytest.mark.asyncio
    async def test_emergency_stop_sets_flag(self, orchestrator):
        """Test that emergency stop sets the flag"""
        await orchestrator.emergency_stop("Test emergency", "operator")

        assert orchestrator.emergency_stop_active is True

    @pytest.mark.asyncio
    async def test_emergency_stop_stops_wrapped_agents(self, orchestrator, mock_agent):
        """Test that emergency stop propagates to wrapped agents"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        await orchestrator.emergency_stop("Test emergency", "operator")

        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapper.emergency_stop is True

    @pytest.mark.asyncio
    async def test_resume_operations_after_emergency(self, orchestrator, mock_agent):
        """Test resuming operations after emergency stop"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        await orchestrator.emergency_stop("Test emergency", "operator")
        result = await orchestrator.resume_operations("operator")

        assert result["status"] == "resumed"
        assert orchestrator.emergency_stop_active is False

    @pytest.mark.asyncio
    async def test_resume_without_emergency_stop(self, orchestrator):
        """Test resuming when no emergency stop is active"""
        result = await orchestrator.resume_operations("operator")

        assert "error" in result


class TestPauseResume:
    """Test pause and resume functionality"""

    @pytest.mark.asyncio
    async def test_pause_system(self, orchestrator):
        """Test pausing the system"""
        result = await orchestrator.pause_system("operator")

        assert result["status"] == "paused"
        assert orchestrator.system_paused is True

    @pytest.mark.asyncio
    async def test_resume_system(self, orchestrator):
        """Test resuming the system"""
        await orchestrator.pause_system("operator")
        result = await orchestrator.resume_system("operator")

        assert result["status"] == "resumed"
        assert orchestrator.system_paused is False

    @pytest.mark.asyncio
    async def test_pause_propagates_to_agents(self, orchestrator, mock_agent):
        """Test that pause propagates to wrapped agents"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        await orchestrator.pause_system("operator")

        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapper.paused is True


class TestGetBoundedStatus:
    """Test getting bounded status"""

    @pytest.mark.asyncio
    async def test_get_bounded_status_complete(self, orchestrator):
        """Test getting complete bounded status"""
        status = await orchestrator.get_bounded_status()

        assert "bounded_autonomy" in status
        assert "system_controls" in status["bounded_autonomy"]

    @pytest.mark.asyncio
    async def test_get_bounded_status_includes_controls(self, orchestrator):
        """Test that status includes control flags"""
        status = await orchestrator.get_bounded_status()

        controls = status["bounded_autonomy"]["system_controls"]
        assert "emergency_stop" in controls
        assert "paused" in controls
        assert "local_only" in controls
        assert "auto_approve_low_risk" in controls

    @pytest.mark.asyncio
    async def test_get_bounded_status_includes_wrapped_agents(self, orchestrator, mock_agent):
        """Test that status includes wrapped agent information"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        status = await orchestrator.get_bounded_status()

        assert "wrapped_agents" in status["bounded_autonomy"]
        assert mock_agent.agent_name in status["bounded_autonomy"]["wrapped_agents"]


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_register_agent_twice(self, orchestrator, mock_agent):
        """Test registering the same agent twice"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["cap1"])

        # Second registration should succeed (updates existing)
        success = await orchestrator.register_agent(agent=mock_agent, capabilities=["cap2"])

        assert success is True

    @pytest.mark.asyncio
    async def test_execute_task_with_empty_capabilities(self, orchestrator, mock_agent):
        """Test executing task with empty capability list"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test_cap"])

        result = await orchestrator.execute_task(task_type="test_task", parameters={}, required_capabilities=[])

        # Should fail with error about no capabilities
        assert "error" in result or "status" in result
