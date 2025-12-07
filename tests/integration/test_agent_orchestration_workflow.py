"""
Integration Tests for Agent Orchestration Workflows
Comprehensive testing of multi-agent collaboration, dependencies, and fault tolerance

Test Coverage:
- Multi-agent collaboration (3+ agents working together)
- Agent failure and fallback mechanisms
- Dependency resolution between agents
- Concurrent agent execution
- Agent caching and performance
- Error recovery and retry logic
- Circuit breaker patterns
- Load balancing
- Inter-agent communication

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #12: Performance SLOs (P95 < 200ms for agent selection)
- Rule #10: No-skip rule - all errors logged and handled
"""

import asyncio
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.orchestrator import (
    AgentCapability,
    AgentOrchestrator,
    AgentTask,
    ExecutionPriority,
    TaskStatus,
)
from agent.modules.base_agent import AgentStatus, BaseAgent


logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    """Create orchestrator instance for testing."""
    return AgentOrchestrator(max_concurrent_tasks=10)


@pytest.fixture
def mock_base_agent() -> BaseAgent:
    """Create a mock base agent for testing."""
    agent = MagicMock(spec=BaseAgent)
    agent.name = "test_agent"
    agent.status = AgentStatus.READY
    agent.execute = AsyncMock(return_value={"status": "success", "result": "test_output"})
    return agent


@pytest.fixture
def mock_claude_agent() -> BaseAgent:
    """Mock Claude agent for content generation."""
    agent = MagicMock(spec=BaseAgent)
    agent.name = "claude_agent"
    agent.status = AgentStatus.READY
    agent.execute = AsyncMock(
        return_value={
            "status": "success",
            "result": "Generated product description: Elegant handbag...",
        }
    )
    return agent


@pytest.fixture
def mock_gpt_agent() -> BaseAgent:
    """Mock GPT agent for analysis tasks."""
    agent = MagicMock(spec=BaseAgent)
    agent.name = "gpt_agent"
    agent.status = AgentStatus.READY
    agent.execute = AsyncMock(return_value={"status": "success", "result": "Analysis complete"})
    return agent


@pytest.fixture
def mock_codex_agent() -> BaseAgent:
    """Mock Codex agent for code generation."""
    agent = MagicMock(spec=BaseAgent)
    agent.name = "codex_agent"
    agent.status = AgentStatus.READY
    agent.execute = AsyncMock(return_value={"status": "success", "result": "Code generated"})
    return agent


@pytest.fixture
def full_agent_workflow_context() -> dict[str, Any]:
    """Complete workflow context for multi-agent scenarios."""
    return {
        "user_id": "test_user_123",
        "agents": ["claude_agent", "gpt_agent", "codex_agent"],
        "task": "Generate fashion product description with SEO analysis",
        "dependencies": {
            "images": ["handbag_front.jpg", "handbag_side.jpg"],
            "specs": {"material": "leather", "color": "black", "brand": "Skyy Rose"},
        },
        "workflow_id": "wf_test_001",
    }


# ============================================================================
# AGENT REGISTRATION & DEPENDENCY TESTS
# ============================================================================


class TestAgentRegistration:
    """Test agent registration and capability management."""

    def test_register_single_agent(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test registering a single agent with capabilities."""
        capability = AgentCapability(
            agent_name="test_agent",
            capabilities=["content_generation", "text_analysis"],
            priority=ExecutionPriority.MEDIUM,
        )

        orchestrator.register_agent(mock_base_agent, capability)

        assert "test_agent" in orchestrator.agents
        assert "test_agent" in orchestrator.agent_capabilities
        assert orchestrator.agent_capabilities["test_agent"].agent_name == "test_agent"

    def test_register_multiple_agents(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test registering multiple agents with different capabilities."""
        claude_capability = AgentCapability(
            agent_name="claude_agent",
            capabilities=["content_generation", "creative_writing"],
            priority=ExecutionPriority.HIGH,
        )
        gpt_capability = AgentCapability(
            agent_name="gpt_agent",
            capabilities=["text_analysis", "summarization"],
            priority=ExecutionPriority.MEDIUM,
        )

        orchestrator.register_agent(mock_claude_agent, claude_capability)
        orchestrator.register_agent(mock_gpt_agent, gpt_capability)

        assert len(orchestrator.agents) == 2
        assert "claude_agent" in orchestrator.agents
        assert "gpt_agent" in orchestrator.agents

    def test_register_agents_with_dependencies(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test registering agents with dependency relationships."""
        claude_capability = AgentCapability(
            agent_name="claude_agent",
            capabilities=["content_generation"],
            priority=ExecutionPriority.HIGH,
        )
        gpt_capability = AgentCapability(
            agent_name="gpt_agent",
            capabilities=["seo_analysis"],
            required_agents=["claude_agent"],  # Depends on Claude
            priority=ExecutionPriority.MEDIUM,
        )

        orchestrator.register_agent(mock_claude_agent, claude_capability)
        orchestrator.register_agent(mock_gpt_agent, gpt_capability)

        assert "claude_agent" in orchestrator.dependency_graph["gpt_agent"]
        assert "gpt_agent" in orchestrator.reverse_dependencies["claude_agent"]

    def test_duplicate_agent_registration(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test handling duplicate agent registration."""
        capability = AgentCapability(
            agent_name="test_agent",
            capabilities=["content_generation"],
        )

        orchestrator.register_agent(mock_base_agent, capability)

        with pytest.raises(ValueError, match="already registered"):
            orchestrator.register_agent(mock_base_agent, capability)


# ============================================================================
# MULTI-AGENT COLLABORATION TESTS
# ============================================================================


class TestMultiAgentCollaboration:
    """Test multi-agent collaboration and coordination."""

    @pytest.mark.asyncio
    async def test_three_agent_collaboration(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
        mock_codex_agent: BaseAgent,
        full_agent_workflow_context: dict[str, Any],
    ):
        """Test 3 agents working together on a complex task."""
        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(
                agent_name="gpt_agent",
                capabilities=["seo_analysis"],
                required_agents=["claude_agent"],
            ),
        )
        orchestrator.register_agent(
            mock_codex_agent,
            AgentCapability(
                agent_name="codex_agent",
                capabilities=["code_generation"],
                required_agents=["gpt_agent"],
            ),
        )

        task = AgentTask(
            task_id="task_multi_001",
            task_type="complete_workflow",
            parameters=full_agent_workflow_context,
            required_agents=["claude_agent", "gpt_agent", "codex_agent"],
            priority=ExecutionPriority.HIGH,
        )

        result = await orchestrator.execute_task(task)

        assert result is not None
        assert task.status == TaskStatus.COMPLETED
        assert mock_claude_agent.execute.called
        assert mock_gpt_agent.execute.called
        assert mock_codex_agent.execute.called

    @pytest.mark.asyncio
    async def test_parallel_agent_execution(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test parallel execution of independent agents."""
        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(agent_name="gpt_agent", capabilities=["text_analysis"]),
        )

        task1 = AgentTask(
            task_id="task_parallel_001",
            task_type="content_generation",
            parameters={"prompt": "Generate description"},
            required_agents=["claude_agent"],
            priority=ExecutionPriority.MEDIUM,
        )
        task2 = AgentTask(
            task_id="task_parallel_002",
            task_type="analysis",
            parameters={"text": "Analyze this content"},
            required_agents=["gpt_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        start_time = time.time()
        results = await asyncio.gather(
            orchestrator.execute_task(task1),
            orchestrator.execute_task(task2),
        )
        execution_time = (time.time() - start_time) * 1000

        assert len(results) == 2
        assert execution_time < 500
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_sequential_dependency_execution(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test sequential execution respecting dependencies."""
        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(
                agent_name="gpt_agent",
                capabilities=["seo_analysis"],
                required_agents=["claude_agent"],
            ),
        )

        task = AgentTask(
            task_id="task_seq_001",
            task_type="content_with_seo",
            parameters={"product": "handbag"},
            required_agents=["claude_agent", "gpt_agent"],
            priority=ExecutionPriority.HIGH,
        )

        result = await orchestrator.execute_task(task)

        assert result is not None
        assert mock_claude_agent.execute.call_count >= 1
        assert mock_gpt_agent.execute.call_count >= 1


# ============================================================================
# FAILURE & FALLBACK TESTS
# ============================================================================


class TestFailureAndFallback:
    """Test agent failure handling and fallback mechanisms."""

    @pytest.mark.asyncio
    async def test_agent_failure_with_fallback(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test fallback to alternative agent on failure."""
        mock_claude_agent.execute = AsyncMock(side_effect=Exception("Claude agent failed"))
        mock_gpt_agent.execute = AsyncMock(
            return_value={"status": "success", "result": "Fallback content"}
        )

        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(agent_name="gpt_agent", capabilities=["content_generation"]),
        )

        task = AgentTask(
            task_id="task_fallback_001",
            task_type="content_generation",
            parameters={"prompt": "Generate content"},
            required_agents=["claude_agent"],
            priority=ExecutionPriority.HIGH,
        )

        result = await orchestrator.execute_task_with_fallback(task, fallback_agents=["gpt_agent"])

        assert result is not None
        assert result["status"] == "success"
        assert mock_gpt_agent.execute.called

    @pytest.mark.asyncio
    async def test_all_agents_fail(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test behavior when all agents fail."""
        mock_claude_agent.execute = AsyncMock(side_effect=Exception("Claude failed"))
        mock_gpt_agent.execute = AsyncMock(side_effect=Exception("GPT failed"))

        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(agent_name="gpt_agent", capabilities=["content_generation"]),
        )

        task = AgentTask(
            task_id="task_fail_all_001",
            task_type="content_generation",
            parameters={"prompt": "Generate content"},
            required_agents=["claude_agent"],
            priority=ExecutionPriority.HIGH,
        )

        with pytest.raises(Exception):
            await orchestrator.execute_task_with_fallback(task, fallback_agents=["gpt_agent"])

    @pytest.mark.asyncio
    async def test_retry_logic_on_transient_failure(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test retry logic for transient failures."""
        call_count = 0

        async def failing_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient failure")
            return {"status": "success", "result": "Success after retry"}

        mock_base_agent.execute = AsyncMock(side_effect=failing_execute)

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["test_capability"]),
        )

        task = AgentTask(
            task_id="task_retry_001",
            task_type="test_task",
            parameters={"test": "data"},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        result = await orchestrator.execute_task_with_retry(task, max_retries=3, backoff_seconds=0.1)

        assert result is not None
        assert result["status"] == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(
        self,
        orchestrator: AgentOrchestrator,
        mock_base_agent: BaseAgent,
    ):
        """Test circuit breaker opens after consecutive failures."""
        mock_base_agent.execute = AsyncMock(side_effect=Exception("Agent failure"))

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["test_capability"]),
        )

        orchestrator.enable_circuit_breaker("test_agent", failure_threshold=3)

        for i in range(3):
            task = AgentTask(
                task_id=f"task_cb_{i}",
                task_type="test_task",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.MEDIUM,
            )
            try:
                await orchestrator.execute_task(task)
            except Exception:
                pass

        assert orchestrator.get_circuit_breaker_state("test_agent") == "OPEN"


# ============================================================================
# PERFORMANCE & LOAD BALANCING TESTS
# ============================================================================


class TestPerformanceAndLoadBalancing:
    """Test performance optimization and load balancing."""

    @pytest.mark.asyncio
    async def test_agent_selection_performance(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test agent selection completes within P95 < 200ms."""
        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(agent_name="gpt_agent", capabilities=["content_generation"]),
        )

        latencies = []
        for i in range(100):
            start = time.time()
            agent = orchestrator.select_agent_for_capability("content_generation")
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        p95_latency = sorted(latencies)[94]
        assert p95_latency < 200, f"P95 latency {p95_latency}ms exceeds 200ms threshold"

    @pytest.mark.asyncio
    async def test_load_balancing_across_agents(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test load balancing distributes tasks across agents."""
        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(
                agent_name="claude_agent",
                capabilities=["content_generation"],
                max_concurrent=5,
            ),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(
                agent_name="gpt_agent",
                capabilities=["content_generation"],
                max_concurrent=5,
            ),
        )

        tasks = [
            AgentTask(
                task_id=f"task_lb_{i}",
                task_type="content_generation",
                parameters={"index": i},
                required_agents=[],
                priority=ExecutionPriority.MEDIUM,
            )
            for i in range(20)
        ]

        results = await asyncio.gather(*[orchestrator.execute_task(task) for task in tasks])

        claude_calls = mock_claude_agent.execute.call_count
        gpt_calls = mock_gpt_agent.execute.call_count

        assert claude_calls > 0 and gpt_calls > 0, "Load should be distributed"
        assert abs(claude_calls - gpt_calls) <= 5, "Load should be relatively balanced"

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test max concurrent task enforcement."""
        async def slow_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            await asyncio.sleep(0.5)
            return {"status": "success"}

        mock_base_agent.execute = AsyncMock(side_effect=slow_execute)

        orchestrator = AgentOrchestrator(max_concurrent_tasks=5)
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["slow_task"]),
        )

        tasks = [
            AgentTask(
                task_id=f"task_concurrent_{i}",
                task_type="slow_task",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.MEDIUM,
            )
            for i in range(10)
        ]

        start_time = time.time()
        await asyncio.gather(*[orchestrator.execute_task(task) for task in tasks])
        total_time = time.time() - start_time

        assert total_time >= 1.0, "Tasks should be throttled due to concurrent limit"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test rate limiting per agent."""
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(
                agent_name="test_agent",
                capabilities=["rate_limited_task"],
                rate_limit=10,  # 10 requests per minute
            ),
        )

        tasks = [
            AgentTask(
                task_id=f"task_rate_{i}",
                task_type="rate_limited_task",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.MEDIUM,
            )
            for i in range(15)
        ]

        start_time = time.time()
        for task in tasks[:15]:
            try:
                await orchestrator.execute_task_with_rate_limit(task)
            except Exception as e:
                if "rate limit" in str(e).lower():
                    break
        execution_time = time.time() - start_time

        assert execution_time > 0.5, "Rate limiting should slow down execution"


# ============================================================================
# CACHING & OPTIMIZATION TESTS
# ============================================================================


class TestCachingAndOptimization:
    """Test caching mechanisms and performance optimizations."""

    @pytest.mark.asyncio
    async def test_result_caching(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test caching of agent results."""
        orchestrator.enable_result_caching(ttl_seconds=60)
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["cacheable_task"]),
        )

        task = AgentTask(
            task_id="task_cache_001",
            task_type="cacheable_task",
            parameters={"input": "test_data"},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        result1 = await orchestrator.execute_task(task)
        result2 = await orchestrator.execute_task(task)

        assert mock_base_agent.execute.call_count == 1, "Should use cached result"
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test cache invalidation after TTL expires."""
        orchestrator.enable_result_caching(ttl_seconds=1)
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["cacheable_task"]),
        )

        task = AgentTask(
            task_id="task_cache_invalidate_001",
            task_type="cacheable_task",
            parameters={"input": "test_data"},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        await orchestrator.execute_task(task)
        await asyncio.sleep(1.5)
        await orchestrator.execute_task(task)

        assert mock_base_agent.execute.call_count == 2, "Cache should expire"

    @pytest.mark.asyncio
    async def test_task_deduplication(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test deduplication of identical concurrent tasks."""
        async def slow_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            await asyncio.sleep(0.5)
            return {"status": "success", "result": "completed"}

        mock_base_agent.execute = AsyncMock(side_effect=slow_execute)

        orchestrator.enable_task_deduplication()
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["dedup_task"]),
        )

        task1 = AgentTask(
            task_id="task_dedup_001",
            task_type="dedup_task",
            parameters={"input": "same_data"},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )
        task2 = AgentTask(
            task_id="task_dedup_002",
            task_type="dedup_task",
            parameters={"input": "same_data"},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        results = await asyncio.gather(
            orchestrator.execute_task(task1),
            orchestrator.execute_task(task2),
        )

        assert mock_base_agent.execute.call_count == 1, "Should deduplicate identical tasks"
        assert results[0] == results[1]


# ============================================================================
# INTER-AGENT COMMUNICATION TESTS
# ============================================================================


class TestInterAgentCommunication:
    """Test communication and data sharing between agents."""

    @pytest.mark.asyncio
    async def test_data_passing_between_agents(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test data is correctly passed between dependent agents."""
        claude_output = {"content": "Generated product description"}

        async def claude_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return {"status": "success", "result": claude_output}

        async def gpt_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            context = kwargs.get("context", {})
            assert "previous_results" in context
            assert context["previous_results"]["claude_agent"] == claude_output
            return {"status": "success", "result": "SEO analysis complete"}

        mock_claude_agent.execute = AsyncMock(side_effect=claude_execute)
        mock_gpt_agent.execute = AsyncMock(side_effect=gpt_execute)

        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(
                agent_name="gpt_agent",
                capabilities=["seo_analysis"],
                required_agents=["claude_agent"],
            ),
        )

        task = AgentTask(
            task_id="task_data_pass_001",
            task_type="content_with_seo",
            parameters={"product": "handbag"},
            required_agents=["claude_agent", "gpt_agent"],
            priority=ExecutionPriority.HIGH,
        )

        result = await orchestrator.execute_task_with_context(task)

        assert result is not None
        assert mock_gpt_agent.execute.called

    @pytest.mark.asyncio
    async def test_shared_context_updates(
        self,
        orchestrator: AgentOrchestrator,
        mock_claude_agent: BaseAgent,
        mock_gpt_agent: BaseAgent,
    ):
        """Test agents can update shared context."""
        shared_context = {"keywords": []}

        async def claude_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            shared_context["keywords"].extend(["luxury", "elegant"])
            return {"status": "success"}

        async def gpt_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            assert "luxury" in shared_context["keywords"]
            shared_context["keywords"].append("premium")
            return {"status": "success"}

        mock_claude_agent.execute = AsyncMock(side_effect=claude_execute)
        mock_gpt_agent.execute = AsyncMock(side_effect=gpt_execute)

        orchestrator.register_agent(
            mock_claude_agent,
            AgentCapability(agent_name="claude_agent", capabilities=["content_generation"]),
        )
        orchestrator.register_agent(
            mock_gpt_agent,
            AgentCapability(agent_name="gpt_agent", capabilities=["seo_analysis"]),
        )

        task = AgentTask(
            task_id="task_shared_context_001",
            task_type="collaborative_task",
            parameters={"shared_context": shared_context},
            required_agents=["claude_agent", "gpt_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        await orchestrator.execute_task(task)

        assert len(shared_context["keywords"]) == 3
        assert "premium" in shared_context["keywords"]


# ============================================================================
# ERROR RECOVERY & MONITORING TESTS
# ============================================================================


class TestErrorRecoveryAndMonitoring:
    """Test error recovery mechanisms and health monitoring."""

    @pytest.mark.asyncio
    async def test_automatic_recovery_after_agent_restart(
        self,
        orchestrator: AgentOrchestrator,
        mock_base_agent: BaseAgent,
    ):
        """Test automatic recovery after agent becomes healthy again."""
        call_count = 0

        async def recovering_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Agent unhealthy")
            return {"status": "success", "result": "Recovered"}

        mock_base_agent.execute = AsyncMock(side_effect=recovering_execute)
        mock_base_agent.status = AgentStatus.READY

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["recovery_test"]),
        )

        orchestrator.enable_health_monitoring(check_interval_seconds=0.5)

        task = AgentTask(
            task_id="task_recovery_001",
            task_type="recovery_test",
            parameters={},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        for i in range(3):
            try:
                result = await orchestrator.execute_task_with_retry(task, max_retries=3, backoff_seconds=0.2)
                if result and result.get("status") == "success":
                    break
            except Exception:
                await asyncio.sleep(0.5)

        assert call_count == 3
        assert mock_base_agent.status == AgentStatus.READY

    @pytest.mark.asyncio
    async def test_health_check_monitoring(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test periodic health checks for agents."""
        health_checks = []

        async def health_check() -> bool:
            health_checks.append(datetime.now())
            return True

        mock_base_agent.health_check = AsyncMock(side_effect=health_check)

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["health_test"]),
        )

        orchestrator.enable_health_monitoring(check_interval_seconds=0.5)
        await asyncio.sleep(2)
        orchestrator.disable_health_monitoring()

        assert len(health_checks) >= 3, "Should perform multiple health checks"

    @pytest.mark.asyncio
    async def test_error_ledger_recording(self, orchestrator: AgentOrchestrator, mock_base_agent: BaseAgent):
        """Test all errors are recorded in error ledger."""
        mock_base_agent.execute = AsyncMock(side_effect=Exception("Test error for ledger"))

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["error_test"]),
        )

        orchestrator.enable_error_ledger()

        task = AgentTask(
            task_id="task_error_ledger_001",
            task_type="error_test",
            parameters={},
            required_agents=["test_agent"],
            priority=ExecutionPriority.MEDIUM,
        )

        try:
            await orchestrator.execute_task(task)
        except Exception:
            pass

        error_ledger = orchestrator.get_error_ledger()
        assert len(error_ledger) > 0
        assert any("Test error for ledger" in str(err) for err in error_ledger)


# ============================================================================
# PRIORITY & SCHEDULING TESTS
# ============================================================================


class TestPriorityAndScheduling:
    """Test task priority and scheduling."""

    @pytest.mark.asyncio
    async def test_critical_priority_execution_order(
        self,
        orchestrator: AgentOrchestrator,
        mock_base_agent: BaseAgent,
    ):
        """Test critical priority tasks execute first."""
        execution_order = []

        async def tracking_execute(*args: Any, **kwargs: Any) -> dict[str, Any]:
            task_id = kwargs.get("task_id", "unknown")
            execution_order.append(task_id)
            await asyncio.sleep(0.1)
            return {"status": "success"}

        mock_base_agent.execute = AsyncMock(side_effect=tracking_execute)

        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["priority_test"]),
        )

        tasks = [
            AgentTask(
                task_id="task_low",
                task_type="priority_test",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.LOW,
            ),
            AgentTask(
                task_id="task_critical",
                task_type="priority_test",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.CRITICAL,
            ),
            AgentTask(
                task_id="task_medium",
                task_type="priority_test",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.MEDIUM,
            ),
        ]

        for task in tasks:
            orchestrator.enqueue_task(task)

        await orchestrator.process_task_queue()

        assert execution_order[0] == "task_critical", "Critical task should execute first"

    @pytest.mark.asyncio
    async def test_fair_scheduling_same_priority(
        self,
        orchestrator: AgentOrchestrator,
        mock_base_agent: BaseAgent,
    ):
        """Test fair scheduling for tasks with same priority."""
        orchestrator.register_agent(
            mock_base_agent,
            AgentCapability(agent_name="test_agent", capabilities=["fair_test"]),
        )

        tasks = [
            AgentTask(
                task_id=f"task_fair_{i}",
                task_type="fair_test",
                parameters={},
                required_agents=["test_agent"],
                priority=ExecutionPriority.MEDIUM,
            )
            for i in range(10)
        ]

        for task in tasks:
            orchestrator.enqueue_task(task)

        await orchestrator.process_task_queue()

        assert all(task.status == TaskStatus.COMPLETED for task in tasks)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
