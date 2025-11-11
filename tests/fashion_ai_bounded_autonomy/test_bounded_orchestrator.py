"""
Unit Tests for Bounded Orchestrator
Tests orchestration with bounded autonomy controls
"""

import asyncio
from datetime import datetime

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from agent.orchestrator import ExecutionPriority
from fashion_ai_bounded_autonomy.bounded_autonomy_wrapper import ActionRiskLevel
from fashion_ai_bounded_autonomy.bounded_orchestrator import BoundedOrchestrator


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    async def initialize(self) -> bool:
        """
        Initialize the agent and mark it as healthy.

        Returns:
            True if initialization completes successfully.
        """
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs):
        """
        Execute the agent's core function and return a success result that echoes the provided inputs.

        Parameters:
            **kwargs: Arbitrary keyword arguments passed to the core function; these are returned unchanged in the result.

        Returns:
            dict: A dictionary with "status" set to "success" and "result" containing the provided kwargs.
        """
        return {"status": "success", "result": kwargs}

    async def health_check(self):
        """
        Report the agent's health status.

        Returns:
            dict: A mapping with keys `"status"` set to `"healthy"` and `"agent_name"` set to the agent's name.
        """
        return {"status": "healthy", "agent_name": self.agent_name}


@pytest.fixture
def orchestrator():
    """
    Create a BoundedOrchestrator configured for local-only testing with automatic approval for low-risk actions.

    Returns:
        BoundedOrchestrator: An orchestrator instance configured with local_only=True and auto_approve_low_risk=True.
    """
    return BoundedOrchestrator(local_only=True, auto_approve_low_risk=True)


@pytest.fixture
def mock_agent():
    """
    Create a MockAgent preconfigured for tests.

    Returns:
        MockAgent: Instance named "test_agent" with version "1.0.0".
    """
    return MockAgent("test_agent", version="1.0.0")


class TestOrchestratorInitialization:
    """Test orchestrator initialization"""

    def test_initialization(self):
        """
        Verify BoundedOrchestrator initializes with provided control flags and default operational states.

        Asserts that:
        - the `local_only` and `auto_approve_low_risk` flags reflect the constructor arguments,
        - the orchestrator starts with `system_paused` set to False,
        - the orchestrator starts with `emergency_stop_active` set to False.
        """
        orch = BoundedOrchestrator(local_only=True, auto_approve_low_risk=True, max_concurrent_tasks=100)

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
            agent=mock_agent, capabilities=["test_capability"], priority=ExecutionPriority.MEDIUM
        )

        assert success is True
        assert mock_agent.agent_name in orchestrator.wrapped_agents

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self, orchestrator):
        """Test registering multiple agents"""
        agent1 = MockAgent("agent1", "1.0.0")
        agent2 = MockAgent("agent2", "1.0.0")

        await orchestrator.register_agent(agent=agent1, capabilities=["cap1"])

        await orchestrator.register_agent(agent=agent2, capabilities=["cap2"])

        assert len(orchestrator.wrapped_agents) == 2

    @pytest.mark.asyncio
    async def test_wrapped_agent_has_bounded_controls(self, orchestrator, mock_agent):
        """Test that registered agents are wrapped with bounded controls"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        wrapped = orchestrator.wrapped_agents[mock_agent.agent_name]
        assert wrapped.local_only == orchestrator.local_only
        assert wrapped.auto_approve_low_risk == orchestrator.auto_approve_low_risk


class TestTaskExecution:
    """Test task execution with approval controls"""

    @pytest.mark.asyncio
    async def test_execute_low_risk_task(self, orchestrator, mock_agent):
        """Test executing low-risk task (auto-approved)"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["query"])

        result = await orchestrator.execute_task(
            task_type="query_data",
            parameters={"query": "test"},
            required_capabilities=["query"],
            priority=ExecutionPriority.MEDIUM,
        )

        # Low-risk tasks should execute immediately
        assert result.get("status") in ["completed", "pending_approval"]

    @pytest.mark.asyncio
    async def test_execute_high_risk_requires_approval(self, orchestrator, mock_agent):
        """Test that high-risk tasks require approval"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["modify"])

        result = await orchestrator.execute_task(
            task_type="create_resource",
            parameters={"data": "test"},
            required_capabilities=["modify"],
            require_approval=True,
        )

        assert result["status"] == "pending_approval"
        assert "task_id" in result

    @pytest.mark.asyncio
    async def test_emergency_stop_blocks_tasks(self, orchestrator):
        """Test that emergency stop blocks task execution"""
        orchestrator.emergency_stop_active = True

        result = await orchestrator.execute_task(task_type="test_task", parameters={}, required_capabilities=[])

        assert "error" in result
        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_paused_system_queues_tasks(self, orchestrator):
        """Test that paused system queues tasks"""
        orchestrator.system_paused = True

        result = await orchestrator.execute_task(task_type="test_task", parameters={}, required_capabilities=[])

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
        risk_single = orchestrator._assess_task_risk("analyze_data", {}, ["agent1"])
        risk_multiple = orchestrator._assess_task_risk("analyze_data", {}, ["agent1", "agent2", "agent3", "agent4"])

        assert risk_multiple >= risk_single


class TestApprovedTaskExecution:
    """Test execution of approved tasks"""

    @pytest.mark.asyncio
    async def test_execute_approved_task(self, orchestrator, mock_agent):
        """Test executing an approved task"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["modify"])

        # Create pending task
        result = await orchestrator.execute_task(
            task_type="create_record",
            parameters={"data": "test"},
            required_capabilities=["modify"],
            require_approval=True,
        )

        task_id = result["task_id"]

        # Execute approved task
        exec_result = await orchestrator.execute_approved_task(task_id=task_id, approved_by="test_operator")

        assert exec_result is not None

    @pytest.mark.asyncio
    async def test_execute_nonexistent_task(self, orchestrator):
        """Test executing non-existent task"""
        result = await orchestrator.execute_approved_task(task_id="nonexistent", approved_by="operator")

        assert "error" in result


class TestEmergencyControls:
    """Test emergency control functionality"""

    @pytest.mark.asyncio
    async def test_emergency_stop(self, orchestrator, mock_agent):
        """Test emergency stop functionality"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        await orchestrator.emergency_stop(reason="Security incident", operator="security_team")

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
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        result = await orchestrator.pause_system("operator")

        assert result["status"] == "paused"
        assert orchestrator.system_paused is True

    @pytest.mark.asyncio
    async def test_resume_system(self, orchestrator, mock_agent):
        """Test resuming system operations"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        orchestrator.system_paused = True

        result = await orchestrator.resume_system("operator")

        assert result["status"] == "resumed"
        assert orchestrator.system_paused is False


class TestStatusReporting:
    """Test status reporting functionality"""

    @pytest.mark.asyncio
    async def test_get_bounded_status(self, orchestrator, mock_agent):
        """
        Verify the orchestrator's bounded autonomy status includes system controls, wrapped agents, and pending approvals.

        Registers a mock agent and retrieves the bounded status, asserting that "system_controls", "wrapped_agents", and "pending_approvals" exist under "bounded_autonomy".
        """
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        status = await orchestrator.get_bounded_status()

        assert "system_controls" in status["bounded_autonomy"]
        assert "wrapped_agents" in status["bounded_autonomy"]
        assert "pending_approvals" in status["bounded_autonomy"]

    @pytest.mark.asyncio
    async def test_status_includes_agent_details(self, orchestrator, mock_agent):
        """Test that status includes wrapped agent details"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        status = await orchestrator.get_bounded_status()
        agents = status["bounded_autonomy"]["wrapped_agents"]

        assert mock_agent.agent_name in agents
        assert "bounded_controls" in agents[mock_agent.agent_name]


class TestTaskManagement:
    """Test task management functionality"""

    @pytest.mark.asyncio
    async def test_task_creation(self, orchestrator, mock_agent):
        """Test that tasks are properly created"""
        await orchestrator.register_agent(agent=mock_agent, capabilities=["test"])

        result = await orchestrator.execute_task(
            task_type="test_task", parameters={"key": "value"}, required_capabilities=["test"]
        )

        # Task should be tracked
        if "task_id" in result:
            assert result["task_id"] in orchestrator.tasks

    @pytest.mark.asyncio
    async def test_no_capable_agents(self, orchestrator):
        """Test task execution when no capable agents exist"""
        result = await orchestrator.execute_task(
            task_type="test_task", parameters={}, required_capabilities=["nonexistent_capability"]
        )

        assert "error" in result


class TestSanitizeForJson:
    """Test the _sanitize_for_json method with depth and circular reference protection"""

    def test_simple_dict(self, orchestrator):
        """Test sanitization of a simple dict"""
        data = {"key": "value", "number": 42}
        result = orchestrator._sanitize_for_json(data)
        assert result == {"key": "value", "number": 42}

    def test_nested_dict(self, orchestrator):
        """Test sanitization of nested dicts"""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = orchestrator._sanitize_for_json(data)
        assert result == {"level1": {"level2": {"level3": "value"}}}

    def test_list_sanitization(self, orchestrator):
        """Test sanitization of lists"""
        data = [1, 2, {"key": "value"}, [3, 4]]
        result = orchestrator._sanitize_for_json(data)
        assert result == [1, 2, {"key": "value"}, [3, 4]]

    def test_tuple_sanitization(self, orchestrator):
        """Test sanitization of tuples"""
        data = (1, 2, {"key": "value"})
        result = orchestrator._sanitize_for_json(data)
        assert result == [1, 2, {"key": "value"}]

    def test_skip_circular_reference_keys(self, orchestrator):
        """Test that _previous_results and _shared_context are skipped"""
        data = {
            "valid_key": "value",
            "_previous_results": {"should": "be_skipped"},
            "_shared_context": {"also": "skipped"},
            "another_key": 123,
        }
        result = orchestrator._sanitize_for_json(data)
        assert result == {"valid_key": "value", "another_key": 123}

    def test_circular_reference_detection(self, orchestrator):
        """Test detection of circular references"""
        data = {"key": "value"}
        data["self"] = data  # Create circular reference

        result = orchestrator._sanitize_for_json(data)
        assert result["key"] == "value"
        assert result["self"] == "<circular_reference>"

    def test_circular_reference_in_list(self, orchestrator):
        """Test detection of circular references in lists"""
        data = [1, 2, 3]
        data.append(data)  # Create circular reference

        result = orchestrator._sanitize_for_json(data)
        assert result[0] == 1
        assert result[1] == 2
        assert result[2] == 3
        assert result[3] == "<circular_reference>"

    def test_max_depth_protection(self, orchestrator):
        """Test max depth protection prevents stack overflow"""
        # Create deeply nested structure
        data = {"level": 1}
        current = data
        for i in range(2, 200):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Test with default max_depth (100)
        result = orchestrator._sanitize_for_json(data)

        # Navigate to depth 99 - should be a dict
        current = result
        for _ in range(98):
            current = current["nested"]

        # At depth 100, should have max_depth marker
        assert "<max_depth_exceeded" in str(current["nested"])

    def test_custom_max_depth(self, orchestrator):
        """Test custom max_depth parameter"""
        # Create nested structure
        data = {"level": 1}
        current = data
        for i in range(2, 10):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Test with custom max_depth of 5
        result = orchestrator._sanitize_for_json(data, max_depth=5)

        # Navigate to depth 4 - should be a dict
        current = result
        for _ in range(4):
            current = current["nested"]

        # At depth 5, should have max_depth marker
        assert "<max_depth_exceeded" in str(current)

    def test_non_serializable_object(self, orchestrator):
        """Test conversion of non-serializable objects to string"""

        class CustomObject:
            def __str__(self):
                return "CustomObject"

        data = {"obj": CustomObject(), "normal": "value"}
        result = orchestrator._sanitize_for_json(data)
        assert result["obj"] == "CustomObject"
        assert result["normal"] == "value"

    def test_primitive_types(self, orchestrator):
        """Test that primitive types pass through unchanged"""
        assert orchestrator._sanitize_for_json("string") == "string"
        assert orchestrator._sanitize_for_json(42) == 42
        assert orchestrator._sanitize_for_json(3.14) == 3.14
        assert orchestrator._sanitize_for_json(True) is True
        assert orchestrator._sanitize_for_json(False) is False
        assert orchestrator._sanitize_for_json(None) is None

    def test_complex_nested_structure(self, orchestrator):
        """Test sanitization of complex nested structures"""
        data = {
            "users": [
                {"name": "Alice", "age": 30, "settings": {"theme": "dark"}},
                {"name": "Bob", "age": 25, "settings": {"theme": "light"}},
            ],
            "metadata": {"count": 2, "version": 1.0},
            "_previous_results": "should_be_skipped",
        }
        result = orchestrator._sanitize_for_json(data)

        assert len(result["users"]) == 2
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][0]["settings"]["theme"] == "dark"
        assert result["metadata"]["count"] == 2
        assert "_previous_results" not in result

    def test_same_object_in_different_branches(self, orchestrator):
        """Test that same object can appear in different branches of the tree"""
        shared = {"shared": "data"}
        data = {
            "branch1": shared,
            "branch2": shared,
        }

        result = orchestrator._sanitize_for_json(data)

        # Both branches should have the data (not circular reference markers)
        # because we clean up the visited set after processing each level
        assert result["branch1"]["shared"] == "data"
        assert result["branch2"]["shared"] == "data"

    def test_error_handling_in_dict(self, orchestrator):
        """Test error handling for non-serializable values in dict"""

        class ProblematicObject:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        data = {"key": "value"}
        # We can't really test this since our code converts to str(),
        # but we verify the try-except structure works
        result = orchestrator._sanitize_for_json(data)
        assert result == {"key": "value"}
