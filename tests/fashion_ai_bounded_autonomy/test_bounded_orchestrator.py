"""
Unit Tests for Bounded Orchestrator
Tests orchestration with bounded autonomy controls
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from fashion_ai_bounded_autonomy.bounded_orchestrator import BoundedOrchestrator
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel
from agent.modules.base_agent import BaseAgent, AgentStatus
from agent.orchestrator import ExecutionPriority, TaskStatus


class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True
    
    async def execute_core_function(self, **kwargs):
        return {"status": "success", "result": kwargs}
    
    async def health_check(self):
        return {"status": "healthy", "agent_name": self.agent_name}


@pytest.fixture
def orchestrator():
    """Create BoundedOrchestrator instance"""
    return BoundedOrchestrator(
        local_only=True,
        auto_approve_low_risk=True
    )


@pytest.fixture
def mock_agent():
    """Create mock agent"""
    return MockAgent("test_agent", version="1.0.0")


class TestOrchestratorInitialization:
    """Test orchestrator initialization"""

    def test_initialization(self):
        """Test basic initialization"""
        orch = BoundedOrchestrator(
            local_only=True,
            auto_approve_low_risk=True,
            max_concurrent_tasks=100
        )
        
        assert orch.local_only is True
        assert orch.auto_approve_low_risk is True
        assert orch.system_paused is False
        assert orch.emergency_stop_active is False

    def test_approval_system_initialized(self, orchestrator):
        """Test that approval system is initialized"""
        assert orchestrator.approval_system is not None


class TestAgentRegistration:
    """Test agent registration with bounded controls"""

    @pytest.mark.asyncio
    async def test_register_agent(self, orchestrator, mock_agent):
        """Test registering agent with bounded controls"""
        success = await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test_capability"],
            priority=ExecutionPriority.MEDIUM
        )
        
        assert success is True
        assert mock_agent.agent_name in orchestrator.wrapped_agents

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self, orchestrator):
        """Test registering multiple agents"""
        agent1 = MockAgent("agent1", "1.0.0")
        agent2 = MockAgent("agent2", "1.0.0")
        
        await orchestrator.register_agent(
            agent=agent1,
            capabilities=["cap1"]
        )
        
        await orchestrator.register_agent(
            agent=agent2,
            capabilities=["cap2"]
        )
        
        assert len(orchestrator.wrapped_agents) == 2

    @pytest.mark.asyncio
    async def test_wrapped_agent_has_bounded_controls(self, orchestrator, mock_agent):
        """Test that registered agents are wrapped with bounded controls"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        wrapped = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapped.local_only == orchestrator.local_only
        assert wrapped.auto_approve_low_risk == orchestrator.auto_approve_low_risk


class TestTaskExecution:
    """Test task execution with approval controls"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_task(self, orchestrator, mock_agent):
        """Test executing low-risk task (auto-approved)"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["query"]
        )
        
        result = await orchestrator.execute_task(
            task_type="query_data",
            parameters={"query": "test"},
            required_capabilities=["query"],
            priority=ExecutionPriority.MEDIUM
        )
        
        # Low-risk tasks should execute immediately
        assert result.get("status") in ["completed", "pending_approval"]

    @pytest.mark.asyncio
    async def test_execute_high_risk_requires_approval(self, orchestrator, mock_agent):
        """Test that high-risk tasks require approval"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["modify"]
        )
        
        result = await orchestrator.execute_task(
            task_type="create_resource",
            parameters={"data": "test"},
            required_capabilities=["modify"],
            require_approval=True
        )
        
        assert result["status"] == "pending_approval"
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_tasks(self, orchestrator):
        """Test that emergency stop blocks task execution"""
        orchestrator.emergency_stop_active = True
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=[]
        )
        
        assert "error" in result
        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_paused_system_queues_tasks(self, orchestrator):
        """Test that paused system queues tasks"""
        orchestrator.system_paused = True
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=[]
        )
        
        assert result["status"] == "queued"


class TestRiskAssessment:
    """Test task risk assessment"""

    def test_assess_low_risk_task(self, orchestrator):
        """Test assessment of low-risk tasks"""
        risk = orchestrator._assess_task_risk("query_data", {}, ["agent1"])
        assert risk == ActionRiskLevel.LOW

    def test_assess_high_risk_task(self, orchestrator):
        """Test assessment of high-risk tasks"""
        risk = orchestrator._assess_task_risk("create_user", {}, ["agent1"])
        assert risk == ActionRiskLevel.HIGH

    def test_assess_critical_risk_task(self, orchestrator):
        """Test assessment of critical-risk tasks"""
        risk = orchestrator._assess_task_risk("deploy_system", {}, ["agent1"])
        assert risk == ActionRiskLevel.CRITICAL

    def test_multiple_agents_increases_risk(self, orchestrator):
        """Test that tasks with multiple agents have higher risk"""
        risk_single = orchestrator._assess_task_risk(
            "analyze_data", {}, ["agent1"]
        )
        risk_multiple = orchestrator._assess_task_risk(
            "analyze_data", {}, ["agent1", "agent2", "agent3", "agent4"]
        )

        assert risk_multiple >= risk_single


class TestApprovedTaskExecution:
    """Test execution of approved tasks"""

    @pytest.mark.asyncio
    async def test_execute_approved_task(self, orchestrator, mock_agent):
        """Test executing an approved task"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["modify"]
        )
        
        # Create pending task
        result = await orchestrator.execute_task(
            task_type="create_record",
            parameters={"data": "test"},
            required_capabilities=["modify"],
            require_approval=True
        )
        
        task_id = result["task_id"]
        
        # Execute approved task
        exec_result = await orchestrator.execute_approved_task(
            task_id=task_id,
            approved_by="test_operator"
        )
        
        assert exec_result is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_task(self, orchestrator):
        """Test executing non-existent task"""
        result = await orchestrator.execute_approved_task(
            task_id="nonexistent",
            approved_by="operator"
        )
        
        assert "error" in result


class TestEmergencyControls:
    """Test emergency control functionality"""

    @pytest.mark.asyncio
    async def test_emergency_stop(self, orchestrator, mock_agent):
        """Test emergency stop functionality"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        await orchestrator.emergency_stop(
            reason="Security incident",
            operator="security_team"
        )
        
        assert orchestrator.emergency_stop_active is True
        
        # Verify wrapped agents are also stopped
        wrapped = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapped.emergency_stop is True

    @pytest.mark.asyncio
    async def test_resume_operations(self, orchestrator):
        """Test resuming operations after emergency stop"""
        orchestrator.emergency_stop_active = True
        
        result = await orchestrator.resume_operations("operator")
        
        assert result["status"] == "resumed"
        assert orchestrator.emergency_stop_active is False

    @pytest.mark.asyncio
    async def test_pause_system(self, orchestrator, mock_agent):
        """Test pausing system operations"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        result = await orchestrator.pause_system("operator")
        
        assert result["status"] == "paused"
        assert orchestrator.system_paused is True

    @pytest.mark.asyncio
    async def test_resume_system(self, orchestrator, mock_agent):
        """Test resuming system operations"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        orchestrator.system_paused = True
        
        result = await orchestrator.resume_system("operator")
        
        assert result["status"] == "resumed"
        assert orchestrator.system_paused is False


class TestStatusReporting:
    """Test status reporting functionality"""

    @pytest.mark.asyncio
    async def test_get_bounded_status(self, orchestrator, mock_agent):
        """Test getting bounded orchestrator status"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        status = await orchestrator.get_bounded_status()
        
        assert "system_controls" in status["bounded_autonomy"]
        assert "wrapped_agents" in status["bounded_autonomy"]
        assert "pending_approvals" in status["bounded_autonomy"]

    @pytest.mark.asyncio
    async def test_status_includes_agent_details(self, orchestrator, mock_agent):
        """Test that status includes wrapped agent details"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        status = await orchestrator.get_bounded_status()
        agents = status["bounded_autonomy"]["wrapped_agents"]
        
        assert mock_agent.agent_name in agents
        assert "bounded_controls" in agents[mock_agent.agent_name]


class TestTaskManagement:
    """Test task management functionality"""

    @pytest.mark.asyncio
    async def test_task_creation(self, orchestrator, mock_agent):
        """Test that tasks are properly created"""
        await orchestrator.register_agent(
            agent=mock_agent,
            capabilities=["test"]
        )
        
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={"key": "value"},
            required_capabilities=["test"]
        )
        
        # Task should be tracked
        if "task_id" in result:
            assert result["task_id"] in orchestrator.tasks

    @pytest.mark.asyncio
    async def test_no_capable_agents(self, orchestrator):
        """Test task execution when no capable agents exist"""
        result = await orchestrator.execute_task(
            task_type="test_task",
            parameters={},
            required_capabilities=["nonexistent_capability"]
        )
        
        assert "error" in result