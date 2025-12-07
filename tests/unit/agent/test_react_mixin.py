"""
Unit Tests for ReAct (Reasoning and Acting) Mixin

Tests the ReActCapableMixin and IterativeRetrievalMixin classes
following AAA pattern (Arrange-Act-Assert).

Truth Protocol Compliance:
- Rule #8: Test Coverage ≥90%
- Rule #9: Document All
- Rule #10: No-Skip Rule
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.mixins.react_mixin import (
    DSPY_AVAILABLE,
    IterativeRetrievalMixin,
    ReActCapableMixin,
    ReasoningStep,
    ReasoningStepType,
    ReasoningTrace,
)


# =============================================================================
# ReasoningStepType Enum Tests
# =============================================================================


class TestReasoningStepType:
    """Tests for ReasoningStepType enum."""

    def test_thought_value(self):
        """Test THOUGHT enum value."""
        assert ReasoningStepType.THOUGHT.value == "thought"

    def test_action_value(self):
        """Test ACTION enum value."""
        assert ReasoningStepType.ACTION.value == "action"

    def test_observation_value(self):
        """Test OBSERVATION enum value."""
        assert ReasoningStepType.OBSERVATION.value == "observation"

    def test_final_answer_value(self):
        """Test FINAL_ANSWER enum value."""
        assert ReasoningStepType.FINAL_ANSWER.value == "final_answer"

    def test_enum_members_count(self):
        """Test that enum has exactly 4 members."""
        assert len(ReasoningStepType) == 4


# =============================================================================
# ReasoningStep Dataclass Tests
# =============================================================================


class TestReasoningStep:
    """Tests for ReasoningStep dataclass."""

    def test_create_thought_step(self):
        """Test creating a THOUGHT step."""
        step = ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="I need to search for products"
        )

        assert step.step_type == ReasoningStepType.THOUGHT
        assert step.content == "I need to search for products"
        assert step.tool_name is None
        assert step.tool_args is None
        assert step.tool_result is None
        assert step.confidence == 0.0
        assert isinstance(step.timestamp, datetime)

    def test_create_action_step_with_tool(self):
        """Test creating an ACTION step with tool details."""
        step = ReasoningStep(
            step_type=ReasoningStepType.ACTION,
            content="Calling search_products",
            tool_name="search_products",
            tool_args={"query": "shoes", "max_price": 100}
        )

        assert step.step_type == ReasoningStepType.ACTION
        assert step.tool_name == "search_products"
        assert step.tool_args == {"query": "shoes", "max_price": 100}

    def test_create_observation_step_with_result(self):
        """Test creating an OBSERVATION step with tool result."""
        step = ReasoningStep(
            step_type=ReasoningStepType.OBSERVATION,
            content="Found 5 products",
            tool_name="search_products",
            tool_result=[{"name": "Shoe A", "price": 50}]
        )

        assert step.step_type == ReasoningStepType.OBSERVATION
        assert step.tool_result == [{"name": "Shoe A", "price": 50}]

    def test_create_final_answer_step_with_confidence(self):
        """Test creating a FINAL_ANSWER step with confidence."""
        step = ReasoningStep(
            step_type=ReasoningStepType.FINAL_ANSWER,
            content="The best product is Shoe A at $50",
            confidence=0.95
        )

        assert step.step_type == ReasoningStepType.FINAL_ANSWER
        assert step.confidence == 0.95

    def test_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated."""
        before = datetime.now()
        step = ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="Test"
        )
        after = datetime.now()

        assert before <= step.timestamp <= after


# =============================================================================
# ReasoningTrace Dataclass Tests
# =============================================================================


class TestReasoningTrace:
    """Tests for ReasoningTrace dataclass."""

    def test_create_empty_trace(self):
        """Test creating an empty trace."""
        trace = ReasoningTrace(task="Find the best product")

        assert trace.task == "Find the best product"
        assert trace.steps == []
        assert trace.final_answer is None
        assert trace.success is False
        assert trace.iterations == 0
        assert trace.total_time_ms == 0.0
        assert trace.tools_used == []

    def test_trace_with_steps(self):
        """Test trace with multiple steps."""
        steps = [
            ReasoningStep(
                step_type=ReasoningStepType.THOUGHT,
                content="Thinking..."
            ),
            ReasoningStep(
                step_type=ReasoningStepType.ACTION,
                content="Acting...",
                tool_name="search"
            ),
            ReasoningStep(
                step_type=ReasoningStepType.OBSERVATION,
                content="Observing..."
            ),
        ]

        trace = ReasoningTrace(
            task="Test task",
            steps=steps,
            final_answer="Done",
            success=True,
            iterations=1,
            total_time_ms=150.5,
            tools_used=["search"]
        )

        assert len(trace.steps) == 3
        assert trace.final_answer == "Done"
        assert trace.success is True
        assert trace.iterations == 1
        assert trace.total_time_ms == 150.5
        assert trace.tools_used == ["search"]


# =============================================================================
# ReActCapableMixin Tests
# =============================================================================


class MockAgent(ReActCapableMixin):
    """Mock agent class for testing ReActCapableMixin."""

    def __init__(self):
        """Initialize mock agent with ReAct capabilities."""
        self.__init_react__()
        self.client = None  # No Claude client for testing


class MockAgentWithClient(ReActCapableMixin):
    """Mock agent with Claude client for testing."""

    def __init__(self, mock_client):
        """Initialize with mock Claude client."""
        self.__init_react__()
        self.client = mock_client
        self.model = "claude-sonnet-4-5-20250929"


class TestReActCapableMixinInit:
    """Tests for ReActCapableMixin initialization."""

    def test_init_react_creates_traces_list(self):
        """Test that __init_react__ creates traces list."""
        agent = MockAgent()
        assert hasattr(agent, "_react_traces")
        assert isinstance(agent._react_traces, list)
        assert len(agent._react_traces) == 0

    def test_init_react_creates_tools_dict(self):
        """Test that __init_react__ creates tools dict."""
        agent = MockAgent()
        assert hasattr(agent, "_react_tools")
        assert isinstance(agent._react_tools, dict)
        assert len(agent._react_tools) == 0

    def test_init_react_sets_max_iterations(self):
        """Test that __init_react__ sets max iterations."""
        agent = MockAgent()
        assert hasattr(agent, "_max_iterations")
        assert agent._max_iterations == 10

    def test_init_react_sets_dspy_configured(self):
        """Test that __init_react__ sets dspy configured flag."""
        agent = MockAgent()
        assert hasattr(agent, "_dspy_configured")
        assert agent._dspy_configured is False


class TestReActCapableMixinRegisterTool:
    """Tests for register_react_tool method."""

    def test_register_tool_with_function_name(self):
        """Test registering tool with default name."""
        agent = MockAgent()

        def my_tool(x: int) -> int:
            """Add one to x."""
            return x + 1

        agent.register_react_tool(my_tool)

        assert "my_tool" in agent._react_tools
        assert agent._react_tools["my_tool"] == my_tool

    def test_register_tool_with_custom_name(self):
        """Test registering tool with custom name."""
        agent = MockAgent()

        def some_function(x: int) -> int:
            """Add one."""
            return x + 1

        agent.register_react_tool(some_function, name="custom_tool")

        assert "custom_tool" in agent._react_tools
        assert "some_function" not in agent._react_tools

    def test_register_multiple_tools(self):
        """Test registering multiple tools."""
        agent = MockAgent()

        def tool_a():
            """Tool A."""
            pass

        def tool_b():
            """Tool B."""
            pass

        agent.register_react_tool(tool_a)
        agent.register_react_tool(tool_b)

        assert len(agent._react_tools) == 2
        assert "tool_a" in agent._react_tools
        assert "tool_b" in agent._react_tools

    def test_register_tool_overwrites_existing(self):
        """Test that registering tool with same name overwrites."""
        agent = MockAgent()

        def tool_v1():
            """Version 1."""
            return 1

        def tool_v2():
            """Version 2."""
            return 2

        agent.register_react_tool(tool_v1, name="my_tool")
        agent.register_react_tool(tool_v2, name="my_tool")

        assert agent._react_tools["my_tool"] == tool_v2


class TestReActCapableMixinExecuteTool:
    """Tests for _execute_tool method."""

    @pytest.mark.asyncio
    async def test_execute_sync_tool(self):
        """Test executing a synchronous tool."""
        agent = MockAgent()

        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        agent.register_react_tool(add)

        result = await agent._execute_tool("add", {"a": 2, "b": 3})
        assert result == 5

    @pytest.mark.asyncio
    async def test_execute_async_tool(self):
        """Test executing an async tool."""
        agent = MockAgent()

        async def async_multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        agent.register_react_tool(async_multiply)

        result = await agent._execute_tool("async_multiply", {"a": 4, "b": 5})
        assert result == 20

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test executing a tool that doesn't exist."""
        agent = MockAgent()

        result = await agent._execute_tool("nonexistent", {})
        assert "error" in result
        assert "nonexistent" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_tool_with_exception(self):
        """Test executing a tool that raises an exception."""
        agent = MockAgent()

        def failing_tool():
            """Tool that fails."""
            raise ValueError("Tool failure")

        agent.register_react_tool(failing_tool)

        result = await agent._execute_tool("failing_tool", {})
        assert "error" in result
        assert "Tool failure" in result["error"]


class TestReActCapableMixinReasonAndAct:
    """Tests for reason_and_act method."""

    @pytest.mark.asyncio
    async def test_reason_and_act_returns_result(self):
        """Test that reason_and_act returns a result dict."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="Simple task",
            max_iterations=1
        )

        assert isinstance(result, dict)
        assert "reasoning_trace" in result
        assert "iterations" in result
        assert "tools_used" in result
        assert "time_ms" in result

    @pytest.mark.asyncio
    async def test_reason_and_act_with_tools(self):
        """Test reason_and_act with provided tools."""
        agent = MockAgent()

        def my_tool(x: int) -> int:
            """Process x."""
            return x * 2

        result = await agent.reason_and_act(
            task="Process data",
            tools=[my_tool],
            max_iterations=1
        )

        # Tool should be registered
        assert "my_tool" in agent._react_tools

    @pytest.mark.asyncio
    async def test_reason_and_act_stores_trace(self):
        """Test that reason_and_act stores the trace."""
        agent = MockAgent()
        initial_traces = len(agent._react_traces)

        await agent.reason_and_act(
            task="Test task",
            max_iterations=1
        )

        assert len(agent._react_traces) == initial_traces + 1

    @pytest.mark.asyncio
    async def test_reason_and_act_with_context(self):
        """Test reason_and_act with context dict."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="Use context",
            context={"key": "value"},
            max_iterations=1
        )

        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_reason_and_act_calculates_time(self):
        """Test that reason_and_act calculates elapsed time."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="Timed task",
            max_iterations=1
        )

        assert result["time_ms"] >= 0


class TestReActCapableMixinFallbackLoop:
    """Tests for _fallback_react_loop method."""

    @pytest.mark.asyncio
    async def test_fallback_loop_no_client(self):
        """Test fallback loop without Claude client."""
        agent = MockAgent()
        trace = ReasoningTrace(task="Test")

        result = await agent._fallback_react_loop(
            task="Simple task",
            max_iterations=2,
            context=None,
            trace=trace
        )

        assert "status" in result
        assert "method" in result
        assert result["method"] == "fallback_react"

    @pytest.mark.asyncio
    async def test_fallback_loop_with_context(self):
        """Test fallback loop with context."""
        agent = MockAgent()
        trace = ReasoningTrace(task="Test")

        result = await agent._fallback_react_loop(
            task="Task with context",
            max_iterations=1,
            context={"info": "extra data"},
            trace=trace
        )

        assert "status" in result

    @pytest.mark.asyncio
    async def test_fallback_loop_adds_steps_to_trace(self):
        """Test that fallback loop adds steps to trace."""
        agent = MockAgent()
        trace = ReasoningTrace(task="Test")

        await agent._fallback_react_loop(
            task="Multi-step task",
            max_iterations=2,
            context=None,
            trace=trace
        )

        # Should have at least one THOUGHT step
        thought_steps = [
            s for s in trace.steps
            if s.step_type == ReasoningStepType.THOUGHT
        ]
        assert len(thought_steps) >= 1


class TestReActCapableMixinGenerateThought:
    """Tests for _generate_thought method."""

    @pytest.mark.asyncio
    async def test_generate_thought_no_client(self):
        """Test thought generation without Claude client."""
        agent = MockAgent()

        result = await agent._generate_thought(
            task="Test task",
            observations=[],
            context_str="",
            iteration=0
        )

        assert "reasoning" in result
        assert "ready_to_answer" in result
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_generate_thought_with_observations(self):
        """Test thought generation with prior observations."""
        agent = MockAgent()
        observations = [
            {"tool": "search", "args": {}, "result": "Found 3 items"}
        ]

        result = await agent._generate_thought(
            task="Process results",
            observations=observations,
            context_str="",
            iteration=1
        )

        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_generate_thought_with_context(self):
        """Test thought generation with context string."""
        agent = MockAgent()

        result = await agent._generate_thought(
            task="Contextualized task",
            observations=[],
            context_str="\nContext: User prefers blue items",
            iteration=0
        )

        assert "reasoning" in result

    @pytest.mark.asyncio
    async def test_generate_thought_ready_after_iterations(self):
        """Test that thought is ready after sufficient iterations."""
        agent = MockAgent()

        result = await agent._generate_thought(
            task="Eventually ready",
            observations=[],
            context_str="",
            iteration=3  # After 2 iterations, should be ready
        )

        # Fallback logic: ready_to_answer should be True after iteration >= 2
        assert result["ready_to_answer"] is True

    @pytest.mark.asyncio
    async def test_generate_thought_with_client(self):
        """Test thought generation with mock Claude client."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = """{
            "reasoning": "I should search for products",
            "ready_to_answer": false,
            "next_action": {"tool_name": "search", "args": {"q": "test"}},
            "confidence": 0.8
        }"""

        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        agent = MockAgentWithClient(mock_client)

        result = await agent._generate_thought(
            task="Search for products",
            observations=[],
            context_str="",
            iteration=0
        )

        assert result["reasoning"] == "I should search for products"
        assert result["ready_to_answer"] is False
        assert result["confidence"] == 0.8


class TestReActCapableMixinGetTraces:
    """Tests for get_reasoning_traces method."""

    def test_get_traces_empty(self):
        """Test getting traces when none exist."""
        agent = MockAgent()
        traces = agent.get_reasoning_traces()
        assert traces == []

    @pytest.mark.asyncio
    async def test_get_traces_after_reasoning(self):
        """Test getting traces after reasoning."""
        agent = MockAgent()

        await agent.reason_and_act(task="Task 1", max_iterations=1)
        await agent.reason_and_act(task="Task 2", max_iterations=1)

        traces = agent.get_reasoning_traces()
        assert len(traces) == 2

    @pytest.mark.asyncio
    async def test_get_traces_with_limit(self):
        """Test getting traces with limit."""
        agent = MockAgent()

        for i in range(5):
            await agent.reason_and_act(task=f"Task {i}", max_iterations=1)

        traces = agent.get_reasoning_traces(limit=3)
        assert len(traces) == 3


class TestReActCapableMixinConfigureDSPy:
    """Tests for configure_dspy method."""

    def test_configure_dspy_not_available(self):
        """Test configure_dspy when DSPy not available."""
        agent = MockAgent()

        with patch("agent.mixins.react_mixin.DSPY_AVAILABLE", False):
            result = agent.configure_dspy(api_key="test_key")

        # Should return False or handle gracefully
        # The actual implementation checks DSPY_AVAILABLE
        assert isinstance(result, bool)

    @pytest.mark.skipif(not DSPY_AVAILABLE, reason="DSPy not installed")
    def test_configure_dspy_with_lm(self):
        """Test configure_dspy with pre-configured LM."""
        agent = MockAgent()
        mock_lm = MagicMock()

        with patch("agent.mixins.react_mixin.dspy") as mock_dspy:
            result = agent.configure_dspy(lm=mock_lm)

        assert result is True
        assert agent._dspy_configured is True


# =============================================================================
# IterativeRetrievalMixin Tests
# =============================================================================


class MockRetrieverAgent(IterativeRetrievalMixin):
    """Mock agent for testing IterativeRetrievalMixin."""

    pass


class TestIterativeRetrievalMixin:
    """Tests for IterativeRetrievalMixin."""

    @pytest.mark.asyncio
    async def test_iterative_retrieve_single_iteration(self):
        """Test iterative retrieve with single iteration."""
        agent = MockRetrieverAgent()

        async def mock_retriever(query: str):
            return [
                {"content": "Result 1", "similarity": 0.9},
                {"content": "Result 2", "similarity": 0.85},
                {"content": "Result 3", "similarity": 0.8},
            ]

        result = await agent.iterative_retrieve(
            query="test query",
            retriever=mock_retriever,
            max_iterations=1,
            min_results=3,
            sufficiency_threshold=0.8
        )

        assert "results" in result
        assert "total_results" in result
        assert "iterations" in result
        assert "queries_used" in result
        assert result["total_results"] >= 3

    @pytest.mark.asyncio
    async def test_iterative_retrieve_multiple_iterations(self):
        """Test iterative retrieve requiring multiple iterations."""
        agent = MockRetrieverAgent()
        call_count = 0

        async def mock_retriever(query: str):
            nonlocal call_count
            call_count += 1
            # Return low similarity results first, then high
            if call_count == 1:
                return [{"content": f"Result {call_count}", "similarity": 0.5}]
            return [{"content": f"Result {call_count}", "similarity": 0.9}]

        result = await agent.iterative_retrieve(
            query="test query",
            retriever=mock_retriever,
            max_iterations=3,
            min_results=2,
            sufficiency_threshold=0.7
        )

        assert len(result["queries_used"]) >= 1

    @pytest.mark.asyncio
    async def test_iterative_retrieve_deduplicates_results(self):
        """Test that iterative retrieve deduplicates results."""
        agent = MockRetrieverAgent()

        async def mock_retriever(query: str):
            # Always return the same result
            return [{"content": "Duplicate", "similarity": 0.6}]

        result = await agent.iterative_retrieve(
            query="test",
            retriever=mock_retriever,
            max_iterations=3,
            min_results=1,
            sufficiency_threshold=0.5
        )

        # Should only have one unique result despite multiple iterations
        unique_contents = set(r["content"] for r in result["results"])
        assert len(unique_contents) == 1

    @pytest.mark.asyncio
    async def test_iterative_retrieve_adds_metadata(self):
        """Test that results include iteration and query metadata."""
        agent = MockRetrieverAgent()

        async def mock_retriever(query: str):
            return [{"content": "Result", "similarity": 0.9}]

        result = await agent.iterative_retrieve(
            query="original query",
            retriever=mock_retriever,
            max_iterations=1,
            min_results=1,
            sufficiency_threshold=0.8
        )

        first_result = result["results"][0]
        assert "iteration" in first_result
        assert "query" in first_result
        assert first_result["iteration"] == 0
        assert first_result["query"] == "original query"

    @pytest.mark.asyncio
    async def test_iterative_retrieve_calculates_avg_similarity(self):
        """Test that average similarity is calculated."""
        agent = MockRetrieverAgent()

        async def mock_retriever(query: str):
            return [
                {"content": "Result 1", "similarity": 0.8},
                {"content": "Result 2", "similarity": 0.6},
            ]

        result = await agent.iterative_retrieve(
            query="test",
            retriever=mock_retriever,
            max_iterations=1,
            min_results=2,
            sufficiency_threshold=0.6
        )

        assert "avg_similarity" in result
        assert result["avg_similarity"] == 0.7  # (0.8 + 0.6) / 2


class TestIterativeRetrievalMixinReformulateQuery:
    """Tests for _reformulate_query method."""

    @pytest.mark.asyncio
    async def test_reformulate_query_iteration_0(self):
        """Test query reformulation at iteration 0."""
        agent = MockRetrieverAgent()

        new_query = await agent._reformulate_query(
            original_query="test query",
            current_results=[],
            iteration=0
        )

        assert "test query" in new_query
        assert new_query != "test query"  # Should be reformulated

    @pytest.mark.asyncio
    async def test_reformulate_query_cycles(self):
        """Test that reformulation cycles through strategies."""
        agent = MockRetrieverAgent()
        queries = []

        for i in range(4):
            q = await agent._reformulate_query(
                original_query="base",
                current_results=[],
                iteration=i
            )
            queries.append(q)

        # Should have different reformulations
        assert len(set(queries)) >= 2


# =============================================================================
# Integration Tests
# =============================================================================


class IntegratedAgent(ReActCapableMixin, IterativeRetrievalMixin):
    """Agent with both mixins for integration testing."""

    def __init__(self):
        """Initialize with ReAct capabilities."""
        self.__init_react__()
        self.client = None


class TestMixinIntegration:
    """Integration tests for combined mixins."""

    def test_agent_has_both_capabilities(self):
        """Test that agent has both ReAct and retrieval methods."""
        agent = IntegratedAgent()

        assert hasattr(agent, "reason_and_act")
        assert hasattr(agent, "iterative_retrieve")
        assert hasattr(agent, "register_react_tool")
        assert hasattr(agent, "_reformulate_query")

    @pytest.mark.asyncio
    async def test_react_with_retrieval_tool(self):
        """Test using retrieval as a ReAct tool."""
        agent = IntegratedAgent()

        async def search_tool(query: str) -> list:
            """Search for items."""
            return [{"item": "result", "score": 0.9}]

        agent.register_react_tool(search_tool)

        result = await agent.reason_and_act(
            task="Find relevant items",
            max_iterations=1
        )

        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_multiple_react_sessions(self):
        """Test running multiple ReAct sessions."""
        agent = IntegratedAgent()

        # Run multiple sessions
        for i in range(3):
            await agent.reason_and_act(
                task=f"Task {i}",
                max_iterations=1
            )

        # All traces should be stored
        traces = agent.get_reasoning_traces()
        assert len(traces) == 3


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_task(self):
        """Test handling of empty task string."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="",
            max_iterations=1
        )

        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_zero_iterations(self):
        """Test with zero max iterations."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="Quick task",
            max_iterations=0
        )

        # Should complete without error
        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_tool_with_no_args(self):
        """Test executing tool with no arguments."""
        agent = MockAgent()

        def no_args_tool() -> str:
            """Tool with no arguments."""
            return "success"

        agent.register_react_tool(no_args_tool)

        result = await agent._execute_tool("no_args_tool", {})
        assert result == "success"

    @pytest.mark.asyncio
    async def test_very_long_task(self):
        """Test handling of very long task description."""
        agent = MockAgent()
        long_task = "Find products " * 100

        result = await agent.reason_and_act(
            task=long_task,
            max_iterations=1
        )

        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_special_characters_in_task(self):
        """Test handling of special characters in task."""
        agent = MockAgent()

        result = await agent.reason_and_act(
            task="Find items with $price < 100 && rating >= 4.5",
            max_iterations=1
        )

        assert "reasoning_trace" in result

    @pytest.mark.asyncio
    async def test_retriever_returns_empty(self):
        """Test handling when retriever returns empty results."""
        agent = MockRetrieverAgent()

        async def empty_retriever(query: str):
            return []

        result = await agent.iterative_retrieve(
            query="no results query",
            retriever=empty_retriever,
            max_iterations=2,
            min_results=1,
            sufficiency_threshold=0.5
        )

        assert result["total_results"] == 0

    @pytest.mark.asyncio
    async def test_retriever_raises_exception(self):
        """Test handling when retriever raises exception."""
        agent = MockRetrieverAgent()

        async def failing_retriever(query: str):
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            await agent.iterative_retrieve(
                query="test",
                retriever=failing_retriever,
                max_iterations=1,
                min_results=1,
                sufficiency_threshold=0.5
            )


# =============================================================================
# Concurrency Tests
# =============================================================================


class TestConcurrency:
    """Tests for concurrent usage."""

    @pytest.mark.asyncio
    async def test_concurrent_react_sessions(self):
        """Test running multiple ReAct sessions concurrently."""
        agent = MockAgent()

        async def run_session(task_id: int):
            return await agent.reason_and_act(
                task=f"Concurrent task {task_id}",
                max_iterations=1
            )

        # Run 5 sessions concurrently
        results = await asyncio.gather(
            *[run_session(i) for i in range(5)]
        )

        assert len(results) == 5
        assert all("reasoning_trace" in r for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """Test executing multiple tools concurrently."""
        agent = MockAgent()
        call_count = 0

        async def counting_tool(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Small delay
            return x * 2

        agent.register_react_tool(counting_tool)

        # Execute tool multiple times concurrently
        results = await asyncio.gather(
            *[agent._execute_tool("counting_tool", {"x": i}) for i in range(10)]
        )

        assert len(results) == 10
        assert call_count == 10
