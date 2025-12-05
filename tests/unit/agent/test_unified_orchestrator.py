"""
Unit Tests for Agent Orchestrator

Tests the AgentOrchestrator class including agent registration,
task execution, dependency resolution, circuit breakers, and metrics.

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All
- Rule #10: No-Skip Rule
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.orchestrator import (
    AgentCapability,
    AgentOrchestrator,
    AgentTask,
    ExecutionPriority,
    MockAgent,
    TaskStatus,
)
from agent.modules.base_agent import AgentStatus


# =============================================================================
# ExecutionPriority Enum Tests
# =============================================================================


class TestExecutionPriority:
    """Tests for ExecutionPriority enum."""

    def test_priority_values(self):
        """Test priority enum values are ordered correctly."""
        assert ExecutionPriority.CRITICAL.value == 1
        assert ExecutionPriority.HIGH.value == 2
        assert ExecutionPriority.MEDIUM.value == 3
        assert ExecutionPriority.LOW.value == 4

    def test_priority_count(self):
        """Test that enum has 4 priority levels."""
        assert len(ExecutionPriority) == 4


# =============================================================================
# TaskStatus Enum Tests
# =============================================================================


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test task status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"


# =============================================================================
# AgentCapability Dataclass Tests
# =============================================================================


class TestAgentCapability:
    """Tests for AgentCapability dataclass."""

    def test_create_capability(self):
        """Test creating an agent capability."""
        cap = AgentCapability(
            agent_name="test_agent",
            capabilities=["search", "analyze"]
        )

        assert cap.agent_name == "test_agent"
        assert cap.capabilities == ["search", "analyze"]
        assert cap.required_agents == []
        assert cap.priority == ExecutionPriority.MEDIUM
        assert cap.max_concurrent == 5
        assert cap.rate_limit == 100

    def test_capability_with_dependencies(self):
        """Test capability with dependencies."""
        cap = AgentCapability(
            agent_name="data_agent",
            capabilities=["process_data"],
            required_agents=["auth_agent", "db_agent"],
            priority=ExecutionPriority.HIGH
        )

        assert cap.required_agents == ["auth_agent", "db_agent"]
        assert cap.priority == ExecutionPriority.HIGH


# =============================================================================
# AgentTask Dataclass Tests
# =============================================================================


class TestAgentTask:
    """Tests for AgentTask dataclass."""

    def test_create_task(self):
        """Test creating an agent task."""
        task = AgentTask(
            task_id="task_123",
            task_type="process_order",
            parameters={"order_id": "ORD-001"},
            required_agents=["order_agent", "inventory_agent"],
            priority=ExecutionPriority.HIGH
        )

        assert task.task_id == "task_123"
        assert task.task_type == "process_order"
        assert task.parameters == {"order_id": "ORD-001"}
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
        assert isinstance(task.created_at, datetime)

    def test_task_default_values(self):
        """Test task default values."""
        task = AgentTask(
            task_id="t1",
            task_type="test",
            parameters={},
            required_agents=[],
            priority=ExecutionPriority.LOW
        )

        assert task.started_at is None
        assert task.completed_at is None


# =============================================================================
# AgentOrchestrator Initialization Tests
# =============================================================================


class TestAgentOrchestratorInit:
    """Tests for AgentOrchestrator initialization."""

    def test_init_default(self):
        """Test default initialization."""
        orch = AgentOrchestrator()

        assert orch.agents == {}
        assert orch.agent_capabilities == {}
        assert orch.max_concurrent_tasks == 50
        assert orch.active_tasks == set()
        assert orch.tasks == {}
        assert orch.shared_context == {}

    def test_init_custom_concurrent(self):
        """Test initialization with custom max concurrent tasks."""
        orch = AgentOrchestrator(max_concurrent_tasks=10)
        assert orch.max_concurrent_tasks == 10

    def test_init_creates_tracking_structures(self):
        """Test that initialization creates all tracking structures."""
        orch = AgentOrchestrator()

        assert hasattr(orch, "execution_history")
        assert hasattr(orch, "agent_metrics")
        assert hasattr(orch, "circuit_breakers")
        assert hasattr(orch, "access_control")
        assert hasattr(orch, "api_keys")


# =============================================================================
# Agent Registration Tests
# =============================================================================


class TestAgentRegistration:
    """Tests for agent registration."""

    @pytest.mark.asyncio
    async def test_register_agent_success(self):
        """Test successful agent registration."""
        orch = AgentOrchestrator()
        agent = MockAgent("test_agent")

        success = await orch.register_agent(
            agent,
            capabilities=["search", "analyze"],
            priority=ExecutionPriority.HIGH
        )

        assert success is True
        assert "test_agent" in orch.agents
        assert "test_agent" in orch.agent_capabilities

    @pytest.mark.asyncio
    async def test_register_agent_with_dependencies(self):
        """Test agent registration with dependencies."""
        orch = AgentOrchestrator()
        agent = MockAgent("data_agent")

        await orch.register_agent(
            agent,
            capabilities=["process"],
            dependencies=["auth_agent"]
        )

        assert orch.dependency_graph["data_agent"] == {"auth_agent"}
        assert "data_agent" in orch.reverse_dependencies["auth_agent"]

    @pytest.mark.asyncio
    async def test_register_agent_enhances_capabilities(self):
        """Test that agent capabilities are enhanced based on agent type."""
        orch = AgentOrchestrator()
        agent = MockAgent("fashion_agent")
        # Add video generation method
        agent.generate_fashion_runway_video = AsyncMock()

        await orch.register_agent(
            agent,
            capabilities=["fashion"]
        )

        cap = orch.agent_capabilities["fashion_agent"]
        assert "video_generation" in cap.capabilities
        assert "runway_video_generation" in cap.capabilities

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Test agent unregistration."""
        orch = AgentOrchestrator()
        agent = MockAgent("temp_agent")

        await orch.register_agent(agent, capabilities=["temp"])
        assert "temp_agent" in orch.agents

        success = await orch.unregister_agent("temp_agent")
        assert success is True
        assert "temp_agent" not in orch.agents

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_agent(self):
        """Test unregistering nonexistent agent."""
        orch = AgentOrchestrator()
        success = await orch.unregister_agent("nonexistent")
        assert success is False


# =============================================================================
# Task Execution Tests
# =============================================================================


class TestTaskExecution:
    """Tests for task execution."""

    @pytest.fixture
    async def orchestrator_with_agents(self):
        """Create orchestrator with registered agents."""
        orch = AgentOrchestrator()

        auth_agent = MockAgent("auth_agent")
        data_agent = MockAgent("data_agent")

        await orch.register_agent(auth_agent, capabilities=["authentication"])
        await orch.register_agent(
            data_agent,
            capabilities=["data_processing"],
            dependencies=["auth_agent"]
        )

        return orch

    @pytest.mark.asyncio
    async def test_execute_task_success(self, orchestrator_with_agents):
        """Test successful task execution."""
        orch = orchestrator_with_agents

        result = await orch.execute_task(
            task_type="process_request",
            parameters={"user_id": "123"},
            required_capabilities=["authentication"]
        )

        assert "task_id" in result
        assert result["status"] == "completed"
        assert "results" in result

    @pytest.mark.asyncio
    async def test_execute_task_no_capable_agents(self):
        """Test task execution with no capable agents."""
        orch = AgentOrchestrator()

        result = await orch.execute_task(
            task_type="special_task",
            parameters={},
            required_capabilities=["nonexistent_capability"]
        )

        assert "error" in result
        assert "No agents found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_task_with_dependencies(self, orchestrator_with_agents):
        """Test task execution respects dependencies."""
        orch = orchestrator_with_agents

        # Both agents required
        result = await orch.execute_task(
            task_type="full_process",
            parameters={},
            required_capabilities=["authentication", "data_processing"]
        )

        # Should have executed both agents
        assert "auth_agent" in result.get("results", {})

    @pytest.mark.asyncio
    async def test_execute_task_records_metrics(self, orchestrator_with_agents):
        """Test that task execution records metrics."""
        orch = orchestrator_with_agents

        await orch.execute_task(
            task_type="metric_test",
            parameters={},
            required_capabilities=["authentication"]
        )

        metrics = orch.get_agent_metrics("auth_agent")
        assert metrics["calls"] >= 1


# =============================================================================
# Dependency Resolution Tests
# =============================================================================


class TestDependencyResolution:
    """Tests for dependency resolution."""

    def test_resolve_no_dependencies(self):
        """Test resolution with no dependencies."""
        orch = AgentOrchestrator()

        result = orch._resolve_dependencies(["agent_a", "agent_b", "agent_c"])

        assert len(result) == 3
        assert set(result) == {"agent_a", "agent_b", "agent_c"}

    def test_resolve_with_dependencies(self):
        """Test resolution with dependencies."""
        orch = AgentOrchestrator()
        orch.dependency_graph["agent_b"] = {"agent_a"}
        orch.dependency_graph["agent_c"] = {"agent_b"}

        result = orch._resolve_dependencies(["agent_a", "agent_b", "agent_c"])

        # agent_a should come before agent_b, agent_b before agent_c
        assert result.index("agent_a") < result.index("agent_b")
        assert result.index("agent_b") < result.index("agent_c")

    def test_find_agents_with_capabilities(self):
        """Test finding agents with required capabilities."""
        orch = AgentOrchestrator()
        orch.agent_capabilities["agent1"] = AgentCapability(
            agent_name="agent1",
            capabilities=["search", "analyze"]
        )
        orch.agent_capabilities["agent2"] = AgentCapability(
            agent_name="agent2",
            capabilities=["search"]
        )

        # Both have search
        result = orch._find_agents_with_capabilities(["search"])
        assert "agent1" in result
        assert "agent2" in result

        # Only agent1 has both
        result = orch._find_agents_with_capabilities(["search", "analyze"])
        assert "agent1" in result
        assert "agent2" not in result


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for circuit breaker pattern."""

    def test_circuit_initially_closed(self):
        """Test circuit starts closed."""
        orch = AgentOrchestrator()

        is_open = orch._is_circuit_open("test_agent")
        assert is_open is False

    def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        orch = AgentOrchestrator()

        for _ in range(5):
            orch._increment_circuit_breaker("test_agent")

        assert orch.circuit_breakers["test_agent"]["state"] == "open"
        assert orch._is_circuit_open("test_agent") is True

    def test_circuit_resets_on_success(self):
        """Test circuit resets after success."""
        orch = AgentOrchestrator()

        # Cause failures
        for _ in range(3):
            orch._increment_circuit_breaker("test_agent")

        # Reset
        orch._reset_circuit_breaker("test_agent")

        assert orch.circuit_breakers["test_agent"]["state"] == "closed"
        assert orch.circuit_breakers["test_agent"]["failures"] == 0


# =============================================================================
# Metrics and Monitoring Tests
# =============================================================================


class TestMetricsAndMonitoring:
    """Tests for metrics and monitoring."""

    def test_record_execution(self):
        """Test recording execution metrics."""
        orch = AgentOrchestrator()

        orch._record_execution("test_agent", True, 0.5)

        metrics = orch.agent_metrics["test_agent"]
        assert metrics["calls"] == 1
        assert metrics["errors"] == 0
        assert metrics["total_time"] == 0.5
        assert metrics["avg_time"] == 0.5

    def test_record_execution_failure(self):
        """Test recording failed execution."""
        orch = AgentOrchestrator()

        orch._record_execution("test_agent", False, 1.0)

        metrics = orch.agent_metrics["test_agent"]
        assert metrics["errors"] == 1

    def test_execution_history_limited(self):
        """Test execution history is limited to 1000 records."""
        orch = AgentOrchestrator()

        for i in range(1100):
            orch._record_execution("agent", True, 0.1)

        assert len(orch.execution_history) == 1000

    @pytest.mark.asyncio
    async def test_get_orchestrator_health(self):
        """Test getting orchestrator health."""
        orch = AgentOrchestrator()
        agent = MockAgent("test_agent")
        await orch.register_agent(agent, capabilities=["test"])

        health = await orch.get_orchestrator_health()

        assert "timestamp" in health
        assert health["registered_agents"] == 1
        assert "agent_health" in health
        assert "system_status" in health

    def test_get_agent_metrics_single(self):
        """Test getting metrics for single agent."""
        orch = AgentOrchestrator()
        orch._record_execution("agent1", True, 0.5)

        metrics = orch.get_agent_metrics("agent1")

        assert metrics["calls"] == 1

    def test_get_agent_metrics_all(self):
        """Test getting all agent metrics."""
        orch = AgentOrchestrator()
        orch._record_execution("agent1", True, 0.5)
        orch._record_execution("agent2", True, 0.3)

        metrics = orch.get_agent_metrics()

        assert "agent1" in metrics
        assert "agent2" in metrics

    def test_get_dependency_graph(self):
        """Test getting dependency graph."""
        orch = AgentOrchestrator()
        orch.dependency_graph["agent_b"] = {"agent_a"}

        graph = orch.get_dependency_graph()

        assert graph["agent_b"] == ["agent_a"]


# =============================================================================
# Inter-Agent Communication Tests
# =============================================================================


class TestInterAgentCommunication:
    """Tests for inter-agent communication."""

    def test_share_data(self):
        """Test sharing data between agents."""
        orch = AgentOrchestrator()

        orch.share_data("config", {"key": "value"})

        assert "config" in orch.shared_context
        assert orch.shared_context["config"]["value"] == {"key": "value"}

    def test_get_shared_data(self):
        """Test getting shared data."""
        orch = AgentOrchestrator()
        orch.share_data("test_key", "test_value")

        value = orch.get_shared_data("test_key")
        assert value == "test_value"

    def test_get_shared_data_nonexistent(self):
        """Test getting nonexistent shared data."""
        orch = AgentOrchestrator()

        value = orch.get_shared_data("nonexistent")
        assert value is None

    def test_shared_data_with_ttl(self):
        """Test shared data with TTL."""
        orch = AgentOrchestrator()

        orch.share_data("temp_data", "value", ttl=3600)

        assert orch.shared_context["temp_data"]["ttl"] == 3600

    @pytest.mark.asyncio
    async def test_broadcast_to_agents(self):
        """Test broadcasting message to agents."""
        orch = AgentOrchestrator()
        orch.agents = {"agent1": MagicMock(), "agent2": MagicMock()}

        await orch.broadcast_to_agents(
            {"type": "notification", "message": "test"},
            agent_names=["agent1"]
        )

        assert orch.get_shared_data("message_agent1") is not None


# =============================================================================
# Video Generation Task Tests
# =============================================================================


class TestVideoGenerationTasks:
    """Tests for video generation task handling."""

    @pytest.mark.asyncio
    async def test_create_video_generation_task(self):
        """Test creating a video generation task."""
        orch = AgentOrchestrator()

        task_id = await orch.create_video_generation_task(
            task_type="runway_video",
            parameters={"prompt": "luxury fashion"},
            priority=ExecutionPriority.HIGH
        )

        assert task_id is not None
        assert task_id in orch.tasks
        assert orch.tasks[task_id].task_type == "runway_video"

    @pytest.mark.asyncio
    async def test_execute_video_task_not_found(self):
        """Test executing nonexistent video task."""
        orch = AgentOrchestrator()

        result = await orch.execute_video_generation_task("nonexistent")

        assert result["status"] == "failed"
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_video_task_no_agent(self):
        """Test executing video task without required agent."""
        orch = AgentOrchestrator()
        task_id = await orch.create_video_generation_task(
            task_type="runway_video",
            parameters={}
        )

        result = await orch.execute_video_generation_task(task_id)

        assert result["status"] == "failed"
        assert "not available" in result["error"]


# =============================================================================
# MockAgent Tests
# =============================================================================


class TestMockAgent:
    """Tests for MockAgent class."""

    @pytest.mark.asyncio
    async def test_mock_agent_initialize(self):
        """Test mock agent initialization."""
        agent = MockAgent("test_mock")

        success = await agent.initialize()

        assert success is True
        assert agent.status == AgentStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_mock_agent_execute(self):
        """Test mock agent execution."""
        agent = MockAgent("test_mock")
        await agent.initialize()

        result = await agent.execute_core_function(param1="value1")

        assert result["status"] == "success"
        assert result["agent"] == "test_mock"
        assert "param1" in result["parameters_received"]

    @pytest.mark.asyncio
    async def test_mock_agent_failure_mode(self):
        """Test mock agent failure mode."""
        agent = MockAgent("failing_agent", should_fail=True)
        await agent.initialize()

        # First two succeed
        await agent.execute_core_function()
        await agent.execute_core_function()

        # Third fails
        with pytest.raises(Exception, match="Simulated failure"):
            await agent.execute_core_function()
