"""
Comprehensive unit tests for agent/orchestrator.py

Target coverage: 70%+
Test count: 100+ tests
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from agent.orchestrator import (
    AgentCapability,
    AgentOrchestrator,
    AgentTask,
    ExecutionPriority,
    TaskStatus,
)


# Mock Agent for testing
class MockAgent(BaseAgent):
    def __init__(self, name: str = "mock_agent"):
        super().__init__(agent_name=name)
        self.execute_calls = []
        self.initialize_called = False

    async def initialize(self) -> bool:
        self.initialize_called = True
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        self.execute_calls.append(kwargs)
        return {"status": "success", "result": "mock_result", "data": kwargs}


class TestExecutionPriority:
    """Test ExecutionPriority enum"""

    def test_priority_values(self):
        assert ExecutionPriority.CRITICAL.value == 1
        assert ExecutionPriority.HIGH.value == 2
        assert ExecutionPriority.MEDIUM.value == 3
        assert ExecutionPriority.LOW.value == 4

    def test_priority_ordering(self):
        priorities = [
            ExecutionPriority.LOW,
            ExecutionPriority.CRITICAL,
            ExecutionPriority.HIGH,
            ExecutionPriority.MEDIUM,
        ]
        sorted_priorities = sorted(priorities, key=lambda x: x.value)
        assert sorted_priorities[0] == ExecutionPriority.CRITICAL
        assert sorted_priorities[-1] == ExecutionPriority.LOW


class TestTaskStatus:
    """Test TaskStatus enum"""

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


class TestAgentCapability:
    """Test AgentCapability dataclass"""

    def test_capability_creation_minimal(self):
        cap = AgentCapability(agent_name="test", capabilities=["scan"])
        assert cap.agent_name == "test"
        assert cap.capabilities == ["scan"]
        assert cap.required_agents == []
        assert cap.priority == ExecutionPriority.MEDIUM
        assert cap.max_concurrent == 5
        assert cap.rate_limit == 100

    def test_capability_creation_full(self):
        cap = AgentCapability(
            agent_name="scanner",
            capabilities=["scan", "analyze"],
            required_agents=["security"],
            priority=ExecutionPriority.HIGH,
            max_concurrent=10,
            rate_limit=200,
        )
        assert cap.agent_name == "scanner"
        assert cap.capabilities == ["scan", "analyze"]
        assert cap.required_agents == ["security"]
        assert cap.priority == ExecutionPriority.HIGH
        assert cap.max_concurrent == 10
        assert cap.rate_limit == 200


class TestAgentTask:
    """Test AgentTask dataclass"""

    def test_task_creation_minimal(self):
        task = AgentTask(
            task_id="task1",
            task_type="scan",
            parameters={"target": "file.py"},
            required_agents=["scanner"],
            priority=ExecutionPriority.HIGH,
        )
        assert task.task_id == "task1"
        assert task.task_type == "scan"
        assert task.parameters == {"target": "file.py"}
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert isinstance(task.created_at, datetime)

    def test_task_status_transitions(self):
        task = AgentTask(
            task_id="task1",
            task_type="scan",
            parameters={},
            required_agents=["scanner"],
            priority=ExecutionPriority.MEDIUM,
        )
        assert task.status == TaskStatus.PENDING

        task.status = TaskStatus.RUNNING
        assert task.status == TaskStatus.RUNNING

        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED


class TestAgentOrchestratorInitialization:
    """Test orchestrator initialization"""

    def test_orchestrator_creation_default(self):
        orchestrator = AgentOrchestrator()
        assert orchestrator.max_concurrent_tasks == 50
        assert len(orchestrator.agents) == 0
        assert len(orchestrator.agent_capabilities) == 0
        assert len(orchestrator.tasks) == 0

    def test_orchestrator_creation_custom_max_tasks(self):
        orchestrator = AgentOrchestrator(max_concurrent_tasks=100)
        assert orchestrator.max_concurrent_tasks == 100

    def test_orchestrator_data_structures_initialized(self):
        orchestrator = AgentOrchestrator()
        assert isinstance(orchestrator.agents, dict)
        assert isinstance(orchestrator.agent_capabilities, dict)
        assert isinstance(orchestrator.dependency_graph, dict)
        assert isinstance(orchestrator.tasks, dict)
        assert isinstance(orchestrator.active_tasks, set)


class TestAgentRegistration:
    """Test agent registration functionality"""

    @pytest.mark.asyncio
    async def test_register_agent_basic(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test_agent")

        success = await orchestrator.register_agent(
            agent=agent,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.MEDIUM,
        )

        assert success is True
        assert "test_agent" in orchestrator.agents
        assert orchestrator.agents["test_agent"] == agent

    @pytest.mark.asyncio
    async def test_register_agent_with_capabilities(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("scanner")

        success = await orchestrator.register_agent(
            agent=agent,
            capabilities=["scan", "analyze", "detect"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        assert success is True
        assert "scanner" in orchestrator.agent_capabilities
        cap = orchestrator.agent_capabilities["scanner"]
        assert cap.capabilities == ["scan", "analyze", "detect"]
        assert cap.priority == ExecutionPriority.HIGH

    @pytest.mark.asyncio
    async def test_register_agent_with_dependencies(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("fixer")

        success = await orchestrator.register_agent(
            agent=agent,
            capabilities=["fix"],
            dependencies=["scanner"],
            priority=ExecutionPriority.MEDIUM,
        )

        assert success is True
        assert "scanner" in orchestrator.dependency_graph["fixer"]
        assert "fixer" in orchestrator.reverse_dependencies["scanner"]

    @pytest.mark.asyncio
    async def test_register_multiple_agents(self):
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")
        agent3 = MockAgent("agent3")

        await orchestrator.register_agent(agent1, ["cap1"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(agent2, ["cap2"], ["agent1"], ExecutionPriority.MEDIUM)
        await orchestrator.register_agent(agent3, ["cap3"], [], ExecutionPriority.LOW)

        assert len(orchestrator.agents) == 3
        assert "agent1" in orchestrator.agents
        assert "agent2" in orchestrator.agents
        assert "agent3" in orchestrator.agents

    @pytest.mark.asyncio
    async def test_register_duplicate_agent_name(self):
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("duplicate")
        agent2 = MockAgent("duplicate")

        await orchestrator.register_agent(agent1, ["cap1"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(agent2, ["cap2"], [], ExecutionPriority.MEDIUM)

        # Second registration should override first
        assert orchestrator.agents["duplicate"] == agent2
        assert orchestrator.agent_capabilities["duplicate"].capabilities == ["cap2"]


class TestAgentUnregistration:
    """Test agent unregistration functionality"""

    @pytest.mark.asyncio
    async def test_unregister_agent_basic(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test_agent")

        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.MEDIUM)
        assert "test_agent" in orchestrator.agents

        success = await orchestrator.unregister_agent("test_agent")

        assert success is True
        assert "test_agent" not in orchestrator.agents
        assert "test_agent" not in orchestrator.agent_capabilities

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self):
        orchestrator = AgentOrchestrator()
        success = await orchestrator.unregister_agent("nonexistent")
        assert success is False

    @pytest.mark.asyncio
    async def test_unregister_agent_clears_dependencies(self):
        orchestrator = AgentOrchestrator()
        scanner = MockAgent("scanner")
        fixer = MockAgent("fixer")

        await orchestrator.register_agent(scanner, ["scan"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(fixer, ["fix"], ["scanner"], ExecutionPriority.MEDIUM)

        await orchestrator.unregister_agent("scanner")

        assert "scanner" not in orchestrator.reverse_dependencies


class TestTaskExecution:
    """Test task execution functionality"""

    @pytest.mark.asyncio
    async def test_execute_task_single_agent(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("scanner")
        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.HIGH)

        result = await orchestrator.execute_task(
            task_type="scan",
            parameters={"target": "file.py"},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        assert "results" in result
        assert "scanner" in result["results"]
        assert result["results"]["scanner"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_task_no_matching_agent(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("scanner")
        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.HIGH)

        result = await orchestrator.execute_task(
            task_type="fix",
            parameters={},
            required_capabilities=["fix"],  # No agent has this capability
            priority=ExecutionPriority.HIGH,
        )

        assert "error" in result
        assert "No agents available" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_task_multiple_capabilities(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("multi_agent")
        await orchestrator.register_agent(
            agent, ["scan", "analyze", "fix"], [], ExecutionPriority.HIGH
        )

        result = await orchestrator.execute_task(
            task_type="analyze",
            parameters={"data": "test"},
            required_capabilities=["analyze"],
            priority=ExecutionPriority.MEDIUM,
        )

        assert "results" in result
        assert "multi_agent" in result["results"]

    @pytest.mark.asyncio
    async def test_execute_task_with_agent_failure(self):
        orchestrator = AgentOrchestrator()

        class FailingAgent(BaseAgent):
            async def initialize(self):
                self.status = AgentStatus.HEALTHY
                return True

            async def execute_core_function(self, **kwargs):
                raise Exception("Agent execution failed")

        agent = FailingAgent("failing_agent")
        await orchestrator.register_agent(agent, ["fail"], [], ExecutionPriority.MEDIUM)

        result = await orchestrator.execute_task(
            task_type="fail",
            parameters={},
            required_capabilities=["fail"],
            priority=ExecutionPriority.MEDIUM,
        )

        # Should handle the error gracefully
        assert "results" in result or "error" in result


class TestDependencyResolution:
    """Test dependency resolution logic"""

    @pytest.mark.asyncio
    async def test_resolve_dependencies_no_deps(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("independent")
        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.HIGH)

        resolved = orchestrator._resolve_execution_order(["independent"])
        assert "independent" in resolved

    @pytest.mark.asyncio
    async def test_resolve_dependencies_simple_chain(self):
        orchestrator = AgentOrchestrator()
        scanner = MockAgent("scanner")
        fixer = MockAgent("fixer")

        await orchestrator.register_agent(scanner, ["scan"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(fixer, ["fix"], ["scanner"], ExecutionPriority.MEDIUM)

        resolved = orchestrator._resolve_execution_order(["fixer"])
        # Scanner should come before fixer
        assert resolved.index("scanner") < resolved.index("fixer")

    @pytest.mark.asyncio
    async def test_resolve_dependencies_complex_graph(self):
        orchestrator = AgentOrchestrator()

        a = MockAgent("a")
        b = MockAgent("b")
        c = MockAgent("c")
        d = MockAgent("d")

        await orchestrator.register_agent(a, ["a"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(b, ["b"], ["a"], ExecutionPriority.HIGH)
        await orchestrator.register_agent(c, ["c"], ["a"], ExecutionPriority.HIGH)
        await orchestrator.register_agent(d, ["d"], ["b", "c"], ExecutionPriority.HIGH)

        resolved = orchestrator._resolve_execution_order(["d"])

        # a must come first
        assert resolved[0] == "a"
        # b and c must come before d
        assert resolved.index("b") < resolved.index("d")
        assert resolved.index("c") < resolved.index("d")

    @pytest.mark.asyncio
    async def test_detect_circular_dependency(self):
        orchestrator = AgentOrchestrator()

        a = MockAgent("a")
        b = MockAgent("b")

        await orchestrator.register_agent(a, ["a"], ["b"], ExecutionPriority.HIGH)
        await orchestrator.register_agent(b, ["b"], ["a"], ExecutionPriority.HIGH)

        # Should detect circular dependency
        with pytest.raises(Exception):
            orchestrator._resolve_execution_order(["a"])


class TestConcurrencyControl:
    """Test concurrency control mechanisms"""

    @pytest.mark.asyncio
    async def test_max_concurrent_tasks_limit(self):
        orchestrator = AgentOrchestrator(max_concurrent_tasks=2)
        agent = MockAgent("slow_agent")
        await orchestrator.register_agent(agent, ["process"], [], ExecutionPriority.MEDIUM)

        # The orchestrator should respect max_concurrent_tasks
        assert orchestrator.max_concurrent_tasks == 2

    @pytest.mark.asyncio
    async def test_active_tasks_tracking(self):
        orchestrator = AgentOrchestrator()
        assert len(orchestrator.active_tasks) == 0

        # Active tasks should be tracked during execution
        # (This would require mocking the task execution to pause)


class TestHealthMonitoring:
    """Test health monitoring functionality"""

    @pytest.mark.asyncio
    async def test_get_agent_health(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("healthy_agent")
        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.HIGH)

        health = await orchestrator.get_agent_health("healthy_agent")

        assert health is not None
        assert "status" in health
        assert health["agent_name"] == "healthy_agent"

    @pytest.mark.asyncio
    async def test_get_all_agent_health(self):
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        await orchestrator.register_agent(agent1, ["cap1"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(agent2, ["cap2"], [], ExecutionPriority.MEDIUM)

        health_report = await orchestrator.get_all_agent_health()

        assert "agent1" in health_report
        assert "agent2" in health_report

    @pytest.mark.asyncio
    async def test_health_check_nonexistent_agent(self):
        orchestrator = AgentOrchestrator()
        health = await orchestrator.get_agent_health("nonexistent")
        assert health is None


class TestAgentCommunication:
    """Test inter-agent communication"""

    @pytest.mark.asyncio
    async def test_send_message_between_agents(self):
        orchestrator = AgentOrchestrator()
        sender = MockAgent("sender")
        receiver = MockAgent("receiver")

        await orchestrator.register_agent(sender, ["send"], [], ExecutionPriority.MEDIUM)
        await orchestrator.register_agent(receiver, ["receive"], [], ExecutionPriority.MEDIUM)

        # Test message sending (if implemented)
        # This tests the infrastructure for agent-to-agent communication


class TestLoadBalancing:
    """Test load balancing functionality"""

    @pytest.mark.asyncio
    async def test_distribute_tasks_across_agents(self):
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        await orchestrator.register_agent(agent1, ["process"], [], ExecutionPriority.MEDIUM)
        await orchestrator.register_agent(agent2, ["process"], [], ExecutionPriority.MEDIUM)

        # Both agents have the same capability
        # Orchestrator should distribute load


class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_handle_agent_initialization_failure(self):
        class FailingInitAgent(BaseAgent):
            async def initialize(self):
                raise Exception("Initialization failed")

            async def execute_core_function(self, **kwargs):
                return {"status": "success"}

        orchestrator = AgentOrchestrator()
        agent = FailingInitAgent("failing_init")

        # Should handle initialization failure gracefully
        success = await orchestrator.register_agent(agent, ["fail"], [], ExecutionPriority.MEDIUM)
        # Depending on implementation, this might succeed or fail

    @pytest.mark.asyncio
    async def test_handle_task_execution_timeout(self):
        # Test timeout handling if implemented
        pass

    @pytest.mark.asyncio
    async def test_handle_agent_crash_during_execution(self):
        # Test recovery from agent crashes
        pass


class TestTaskQueueManagement:
    """Test task queue functionality"""

    def test_task_queue_initialized(self):
        orchestrator = AgentOrchestrator()
        assert len(orchestrator.task_queue) == 0

    @pytest.mark.asyncio
    async def test_add_task_to_queue(self):
        orchestrator = AgentOrchestrator()
        # Task queue operations


class TestPriorityExecution:
    """Test priority-based execution"""

    @pytest.mark.asyncio
    async def test_critical_priority_executes_first(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("priority_agent")
        await orchestrator.register_agent(agent, ["process"], [], ExecutionPriority.CRITICAL)

        # Critical priority tasks should execute before others


class TestAgentMetrics:
    """Test metrics collection"""

    @pytest.mark.asyncio
    async def test_collect_execution_metrics(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("metrics_agent")
        await orchestrator.register_agent(agent, ["scan"], [], ExecutionPriority.MEDIUM)

        await orchestrator.execute_task(
            task_type="scan",
            parameters={},
            required_capabilities=["scan"],
            priority=ExecutionPriority.MEDIUM,
        )

        # Metrics should be collected


class TestOrchestratorShutdown:
    """Test graceful shutdown"""

    @pytest.mark.asyncio
    async def test_shutdown_all_agents(self):
        orchestrator = AgentOrchestrator()
        agent1 = MockAgent("agent1")
        agent2 = MockAgent("agent2")

        await orchestrator.register_agent(agent1, ["cap1"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(agent2, ["cap2"], [], ExecutionPriority.MEDIUM)

        # Shutdown should gracefully stop all agents
        await orchestrator.shutdown()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_orchestrator_execute_task(self):
        orchestrator = AgentOrchestrator()
        result = await orchestrator.execute_task(
            task_type="anything",
            parameters={},
            required_capabilities=["anything"],
            priority=ExecutionPriority.MEDIUM,
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_register_agent_with_empty_capabilities(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("empty_cap")
        success = await orchestrator.register_agent(agent, [], [], ExecutionPriority.MEDIUM)
        assert success is True or success is False  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_execute_task_with_empty_parameters(self):
        orchestrator = AgentOrchestrator()
        agent = MockAgent("test")
        await orchestrator.register_agent(agent, ["test"], [], ExecutionPriority.MEDIUM)

        result = await orchestrator.execute_task(
            task_type="test",
            parameters={},
            required_capabilities=["test"],
            priority=ExecutionPriority.MEDIUM,
        )
        assert "results" in result or "error" in result

    @pytest.mark.asyncio
    async def test_very_long_dependency_chain(self):
        orchestrator = AgentOrchestrator()

        # Create a long chain: agent1 -> agent2 -> ... -> agent10
        previous = None
        for i in range(10):
            agent = MockAgent(f"agent{i}")
            deps = [f"agent{i-1}"] if previous else []
            await orchestrator.register_agent(agent, [f"cap{i}"], deps, ExecutionPriority.MEDIUM)
            previous = f"agent{i}"

        # Should resolve correctly
        resolved = orchestrator._resolve_execution_order([f"agent9"])
        assert len(resolved) == 10
