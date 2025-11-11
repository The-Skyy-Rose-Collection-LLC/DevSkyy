"""
Unit tests for BoundedOrchestrator
Tests bounded orchestration with approval workflows
"""

import unittest
import pytest

from fashion_ai_bounded_autonomy.bounded_orchestrator import BoundedOrchestrator
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel
from agent.orchestrator import ExecutionPriority
from agent.modules.base_agent import BaseAgent, AgentStatus


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
    return BoundedOrchestrator(
        max_concurrent_tasks=50,
        local_only=True,
        auto_approve_low_risk=True
    )


@pytest.fixture
def mock_agent():
    """Create mock agent"""
    return MockAgent("test_agent", "1.0.0")


class TestBoundedOrchestratorInitialization(unittest.TestCase):
    """Test orchestrator initialization"""

    def test_init_sets_defaults(self, orchestrator):
        """Test that initialization sets default values"""
        self.assertIs(orchestrator.local_only, True)
        self.assertIs(orchestrator.auto_approve_low_risk, True)
        self.assertIs(orchestrator.system_paused, False)
        self.assertIs(orchestrator.emergency_stop_active, False)
        self.assertEqual(len(orchestrator.wrapped_agents), 0)

    def test_init_creates_approval_system(self, orchestrator):
        """Test that initialization creates approval system"""
        self.assertIsNotNone(orchestrator.approval_system)


class TestRegisterAgent(unittest.TestCase):
    """Test agent registration"""

    @pytest.mark.asyncio
    async def test_register_agent_basic(self, orchestrator, mock_agent):
        """Test basic agent registration"""
        success = await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_capability"],
            priority=ExecutionPriority.MEDIUM
        )
        
        self.assertIs(success, True)
        self.assertIn(mock_agent.agent_name, orchestrator.wrapped_agents)

    @pytest.mark.asyncio
    async def test_register_agent_creates_wrapper(self, orchestrator, mock_agent):
        """Test that registration creates bounded wrapper"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_capability"]
        )
        
        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        self.assertIsNotNone(wrapper)
        self.assertEqual(wrapper.wrapped_agent, mock_agent)

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self, orchestrator):
        """Test registering multiple agents"""
        agents = [MockAgent(f"agent_{i}") for i in range(3)]
        
        for agent in agents:
            await orchestrator.register_agent(
                agent=agent,
                capabilities=[f"cap_{agent.agent_name}"]
            )
        
        self.assertEqual(len(orchestrator.wrapped_agents), 3)


class TestExecuteTask(unittest.TestCase):
    """Test task execution"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_task(self, orchestrator, mock_agent):
        """Test executing low-risk task"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["read_data"]
        )
        
        result = await orchestrator.execute_task(
            task_type="read_data",
            parameters={"source": "test.csv"},
            required_capabilities=["read_data"],
            priority=ExecutionPriority.MEDIUM
        )
        
        # Low-risk tasks may execute immediately depending on configuration
        self.assertIn("status", result)

    @pytest.mark.asyncio
    async def test_execute_high_risk_task_requires_approval(self, orchestrator, mock_agent):
        """Test that high-risk tasks require approval"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["write_data"]
        )
        
        result = await orchestrator.execute_task(
            task_type="update_database",
            parameters={"data": "test"},
            required_capabilities=["write_data"],
            priority=ExecutionPriority.HIGH,
            require_approval=True
        )
        
        self.assertEqual(result["status"], "pending_approval")
        self.assertIn("task_id", result)

    @pytest.mark.asyncio
    async def test_execute_task_emergency_stop(self, orchestrator, mock_agent):
        """Test that emergency stop blocks task execution"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        await orchestrator.emergency_stop("Test emergency", "operator")
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=["test_cap"]
        )
        
        self.assertEqual(result["status"], "blocked")
        self.assertIn("emergency", result["error"].lower())

    @pytest.mark.asyncio
    async def test_execute_task_system_paused(self, orchestrator, mock_agent):
        """Test that paused system queues tasks"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        await orchestrator.pause_system("operator")
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=["test_cap"]
        )
        
        self.assertEqual(result["status"], "queued")

    @pytest.mark.asyncio
    async def test_execute_task_no_capable_agents(self, orchestrator):
        """Test executing task with no capable agents"""
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=["nonexistent_capability"]
        )
        
        self.assertIn("error", result)


class TestExecuteApprovedTask(unittest.TestCase):
    """Test executing approved tasks"""

    @pytest.mark.asyncio
    async def test_execute_approved_task(self, orchestrator, mock_agent):
        """Test executing an approved task"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        # Create task requiring approval
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={"test": "value"},
            required_capabilities=["test_cap"],
            require_approval=True
        )
        
        task_id = result["task_id"]
        
        # Execute approved task
        exec_result = await orchestrator.execute_approved_task(
            task_id=task_id,
            approved_by="operator"
        )
        
        self.assertIn("status", exec_result)

    @pytest.mark.asyncio
    async def test_execute_approved_nonexistent_task(self, orchestrator):
        """Test executing non-existent approved task"""
        result = await orchestrator.execute_approved_task(
            task_id="nonexistent",
            approved_by="operator"
        )
        
        self.assertEqual(result["status"], "error")


class TestRiskAssessment(unittest.TestCase):
    """Test task risk assessment"""

    def test_assess_task_risk_critical(self, orchestrator):
        """Test assessment of critical tasks"""
        risk = orchestrator._assess_task_risk(
            task_type="deploy_production",
            parameters={},
            agents=["agent1"]
        )
        
        self.assertEqual(risk, ActionRiskLevel.CRITICAL)

    def test_assess_task_risk_high(self, orchestrator):
        """Test assessment of high-risk tasks"""
        risk = orchestrator._assess_task_risk(
            task_type="update_records",
            parameters={},
            agents=["agent1"]
        )
        
        self.assertEqual(risk, ActionRiskLevel.HIGH)

    def test_assess_task_risk_medium(self, orchestrator):
        """Test assessment of medium-risk tasks"""
        risk = orchestrator._assess_task_risk(
            task_type="analyze_data",
            parameters={},
            agents=["agent1"]
        )
        
        self.assertEqual(risk, ActionRiskLevel.MEDIUM)

    def test_assess_task_risk_low(self, orchestrator):
        """Test assessment of low-risk tasks"""
        risk = orchestrator._assess_task_risk(
            task_type="read_logs",
            parameters={},
            agents=["agent1"]
        )
        
        self.assertEqual(risk, ActionRiskLevel.LOW)

    def test_assess_task_risk_multiple_agents_increases_risk(self, orchestrator):
        """Test that multiple agents increase risk level"""
        risk = orchestrator._assess_task_risk(
            task_type="analyze_data",
            parameters={},
            agents=["agent1", "agent2", "agent3", "agent4"]
        )
        
        self.assertEqual(risk, ActionRiskLevel.HIGH)


class TestEmergencyStop(unittest.TestCase):
    """Test emergency stop functionality"""

    @pytest.mark.asyncio
    async def test_emergency_stop_sets_flag(self, orchestrator):
        """Test that emergency stop sets the flag"""
        await orchestrator.emergency_stop("Test emergency", "operator")
        
        self.assertIs(orchestrator.emergency_stop_active, True)

    @pytest.mark.asyncio
    async def test_emergency_stop_stops_wrapped_agents(self, orchestrator, mock_agent):
        """Test that emergency stop propagates to wrapped agents"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        await orchestrator.emergency_stop("Test emergency", "operator")
        
        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        self.assertIs(wrapper.emergency_stop, True)

    @pytest.mark.asyncio
    async def test_resume_operations_after_emergency(self, orchestrator, mock_agent):
        """Test resuming operations after emergency stop"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        await orchestrator.emergency_stop("Test emergency", "operator")
        result = await orchestrator.resume_operations("operator")
        
        self.assertEqual(result["status"], "resumed")
        self.assertIs(orchestrator.emergency_stop_active, False)

    @pytest.mark.asyncio
    async def test_resume_without_emergency_stop(self, orchestrator):
        """Test resuming when no emergency stop is active"""
        result = await orchestrator.resume_operations("operator")
        
        self.assertIn("error", result)


class TestPauseResume(unittest.TestCase):
    """Test pause and resume functionality"""

    @pytest.mark.asyncio
    async def test_pause_system(self, orchestrator):
        """Test pausing the system"""
        result = await orchestrator.pause_system("operator")
        
        self.assertEqual(result["status"], "paused")
        self.assertIs(orchestrator.system_paused, True)

    @pytest.mark.asyncio
    async def test_resume_system(self, orchestrator):
        """Test resuming the system"""
        await orchestrator.pause_system("operator")
        result = await orchestrator.resume_system("operator")
        
        self.assertEqual(result["status"], "resumed")
        self.assertIs(orchestrator.system_paused, False)

    @pytest.mark.asyncio
    async def test_pause_propagates_to_agents(self, orchestrator, mock_agent):
        """Test that pause propagates to wrapped agents"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        await orchestrator.pause_system("operator")
        
        wrapper = orchestrator.wrapped_agents[mock_agent.agent_name]
        self.assertIs(wrapper.paused, True)


class TestGetBoundedStatus(unittest.TestCase):
    """Test getting bounded status"""

    @pytest.mark.asyncio
    async def test_get_bounded_status_complete(self, orchestrator):
        """Test getting complete bounded status"""
        status = await orchestrator.get_bounded_status()
        
        self.assertIn("bounded_autonomy", status)
        self.assertIn("system_controls", status["bounded_autonomy"])

    @pytest.mark.asyncio
    async def test_get_bounded_status_includes_controls(self, orchestrator):
        """Test that status includes control flags"""
        status = await orchestrator.get_bounded_status()
        
        controls = status["bounded_autonomy"]["system_controls"]
        self.assertIn("emergency_stop", controls)
        self.assertIn("paused", controls)
        self.assertIn("local_only", controls)
        self.assertIn("auto_approve_low_risk", controls)

    @pytest.mark.asyncio
    async def test_get_bounded_status_includes_wrapped_agents(self, orchestrator, mock_agent):
        """Test that status includes wrapped agent information"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        status = await orchestrator.get_bounded_status()
        
        self.assertIn("wrapped_agents", status["bounded_autonomy"])
        self.assertIn(mock_agent.agent_name, status["bounded_autonomy"]["wrapped_agents"])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_register_agent_twice(self, orchestrator, mock_agent):
        """Test registering the same agent twice"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["cap1"]
        )
        
        # Second registration should succeed (updates existing)
        success = await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["cap2"]
        )
        
        self.assertIs(success, True)

    @pytest.mark.asyncio
    async def test_execute_task_with_empty_capabilities(self, orchestrator, mock_agent):
        """Test executing task with empty capability list"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_cap"]
        )
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=[]
        )
        
        # Should fail with error about no capabilities
        self.assertIn("error", result or "status" in result)