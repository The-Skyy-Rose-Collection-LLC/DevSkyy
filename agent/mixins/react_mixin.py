"""
ReAct (Reasoning and Acting) Mixin for DevSkyy Agents

Implements iterative reasoning loops using DSPy ReAct pattern.
Per Yao et al., 2022 - "ReACT: Synergizing Reasoning and Acting in Language Models"

Verified implementation patterns from:
- DSPy ReAct: https://dspy.ai/api/modules/ReAct/
- DSPy Tools: https://dspy.ai/learn/programming/tools/

Usage:
    class MyAgent(BaseAgent, ReActCapableMixin):
        async def complex_task(self, task):
            return await self.reason_and_act(
                task=task,
                tools=[self.search, self.calculate],
                max_iterations=5
            )

Truth Protocol Compliance:
- Rule #1: Never guess - Uses iterative verification
- Rule #9: Document All - Full docstrings and type hints
- Rule #10: No-Skip Rule - Logs all reasoning steps
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReasoningStepType(Enum):
    """Types of reasoning steps in ReAct loop."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"


@dataclass
class ReasoningStep:
    """Single step in the reasoning chain."""
    step_type: ReasoningStepType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: Any | None = None
    confidence: float = 0.0


@dataclass
class ReasoningTrace:
    """Complete trace of reasoning process."""
    task: str
    steps: list[ReasoningStep] = field(default_factory=list)
    final_answer: str | None = None
    success: bool = False
    iterations: int = 0
    total_time_ms: float = 0.0
    tools_used: list[str] = field(default_factory=list)


class ReActCapableMixin:
    """
    Mixin that adds ReAct (Reasoning + Acting) capabilities to any agent.

    Implements iterative reasoning loop:
    1. THOUGHT: Reason about current state and what to do next
    2. ACTION: Choose and execute a tool
    3. OBSERVATION: Analyze tool result
    4. Repeat until task is complete or max iterations reached

    Compatible with existing DevSkyy agent architecture.
    Does NOT replace existing functionality - augments it.
    """

    def __init_react__(self):
        """Initialize ReAct components. Call in agent __init__."""
        self._react_traces: list[ReasoningTrace] = []
        self._react_tools: dict[str, Callable] = {}
        self._max_iterations = 10
        self._dspy_configured = False

        if DSPY_AVAILABLE:
            logger.info("ReAct mixin initialized with DSPy support")
        else:
            logger.warning("DSPy not available - using fallback reasoning loop")

    def register_react_tool(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None
    ) -> None:
        """
        Register a tool for use in ReAct reasoning.

        Args:
            func: Callable function with type hints
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)

        Per DSPy docs: Tools require type hints and docstrings.
        """
        tool_name = name or func.__name__
        self._react_tools[tool_name] = func
        logger.debug(f"Registered ReAct tool: {tool_name}")

    async def reason_and_act(
        self,
        task: str,
        tools: list[Callable] | None = None,
        max_iterations: int = 5,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute ReAct reasoning loop for complex task.

        Implements: Thought ' Action ' Observation ' ... ' Final Answer

        Args:
            task: Task description to solve
            tools: List of callable tools (functions with type hints)
            max_iterations: Maximum reasoning iterations
            context: Additional context for reasoning

        Returns:
            Dict with final_answer, reasoning_trace, and metadata

        Example:
            result = await agent.reason_and_act(
                task="Find products under $100 and recommend the best one",
                tools=[search_products, calculate_value],
                max_iterations=5
            )
        """
        start_time = datetime.now()
        trace = ReasoningTrace(task=task)

        # Register provided tools
        if tools:
            for tool in tools:
                self.register_react_tool(tool)

        try:
            if DSPY_AVAILABLE and self._dspy_configured:
                result = await self._dspy_react_loop(task, max_iterations, context, trace)
            else:
                result = await self._fallback_react_loop(task, max_iterations, context, trace)

            trace.success = True
            trace.final_answer = result.get("final_answer")

        except Exception as e:
            logger.error(f"ReAct loop failed: {e}")
            trace.success = False
            result = {
                "final_answer": None,
                "error": str(e),
                "status": "failed"
            }

        # Calculate timing
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        trace.total_time_ms = elapsed
        trace.iterations = len([s for s in trace.steps if s.step_type == ReasoningStepType.THOUGHT])
        trace.tools_used = list(set(s.tool_name for s in trace.steps if s.tool_name))

        # Store trace
        self._react_traces.append(trace)

        return {
            **result,
            "reasoning_trace": trace,
            "iterations": trace.iterations,
            "tools_used": trace.tools_used,
            "time_ms": elapsed,
        }

    async def _dspy_react_loop(
        self,
        task: str,
        max_iterations: int,
        context: dict[str, Any] | None,
        trace: ReasoningTrace,
    ) -> dict[str, Any]:
        """
        Execute ReAct loop using DSPy framework.

        Uses dspy.ReAct module for structured reasoning.
        Per DSPy docs: https://dspy.ai/api/modules/ReAct/
        """
        if not DSPY_AVAILABLE:
            return await self._fallback_react_loop(task, max_iterations, context, trace)

        # Convert tools to DSPy format
        dspy_tools = list(self._react_tools.values())

        # Create ReAct module with signature
        react_module = dspy.ReAct(
            signature="task -> final_answer",
            tools=dspy_tools,
            max_iters=max_iterations
        )

        # Execute
        result = react_module(task=task)

        # Log the reasoning trace
        trace.steps.append(ReasoningStep(
            step_type=ReasoningStepType.FINAL_ANSWER,
            content=str(result.final_answer),
            confidence=0.9
        ))

        return {
            "final_answer": result.final_answer,
            "status": "success",
            "method": "dspy_react"
        }

    async def _fallback_react_loop(
        self,
        task: str,
        max_iterations: int,
        context: dict[str, Any] | None,
        trace: ReasoningTrace,
    ) -> dict[str, Any]:
        """
        Fallback ReAct implementation without DSPy.

        Implements manual Thought ' Action ' Observation loop.
        Uses Claude API directly for reasoning.
        """
        logger.info(f"Starting fallback ReAct loop for: {task[:50]}...")

        observations = []
        context_str = ""

        if context:
            context_str = f"\nContext: {context}"

        for iteration in range(max_iterations):
            # THOUGHT: Reason about current state
            thought = await self._generate_thought(
                task=task,
                observations=observations,
                context_str=context_str,
                iteration=iteration
            )

            trace.steps.append(ReasoningStep(
                step_type=ReasoningStepType.THOUGHT,
                content=thought["reasoning"],
                confidence=thought.get("confidence", 0.8)
            ))

            # Check if we have enough information
            if thought.get("ready_to_answer", False):
                final_answer = thought.get("answer", "")
                trace.steps.append(ReasoningStep(
                    step_type=ReasoningStepType.FINAL_ANSWER,
                    content=final_answer,
                    confidence=thought.get("confidence", 0.9)
                ))

                return {
                    "final_answer": final_answer,
                    "status": "success",
                    "method": "fallback_react",
                    "iterations": iteration + 1
                }

            # ACTION: Select and execute a tool
            action = thought.get("next_action")
            if action and action.get("tool_name"):
                tool_name = action["tool_name"]
                tool_args = action.get("args", {})

                trace.steps.append(ReasoningStep(
                    step_type=ReasoningStepType.ACTION,
                    content=f"Calling {tool_name}",
                    tool_name=tool_name,
                    tool_args=tool_args
                ))

                # Execute tool
                observation = await self._execute_tool(tool_name, tool_args)

                trace.steps.append(ReasoningStep(
                    step_type=ReasoningStepType.OBSERVATION,
                    content=str(observation),
                    tool_name=tool_name,
                    tool_result=observation
                ))

                observations.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": observation
                })

        # Max iterations reached - provide best answer
        return {
            "final_answer": f"After {max_iterations} iterations, best answer: {observations[-1] if observations else 'No conclusion reached'}",
            "status": "max_iterations",
            "method": "fallback_react",
            "iterations": max_iterations
        }

    async def _generate_thought(
        self,
        task: str,
        observations: list[dict],
        context_str: str,
        iteration: int
    ) -> dict[str, Any]:
        """
        Generate a thought about the current state.

        Uses Claude or configured LLM to reason about:
        - What do we know so far?
        - What do we still need to find out?
        - Which tool should we use next?
        - Or are we ready to answer?
        """
        # Build observation summary
        obs_summary = ""
        if observations:
            obs_summary = "\n\nPrevious observations:\n"
            for obs in observations:
                obs_summary += f"- {obs['tool']}: {str(obs['result'])[:200]}\n"

        # Build tool list
        tool_list = "\n".join([
            f"- {name}: {func.__doc__ or 'No description'}"
            for name, func in self._react_tools.items()
        ])

        prompt = f"""You are reasoning about a task step by step.

Task: {task}
{context_str}
{obs_summary}

Available tools:
{tool_list}

Iteration: {iteration + 1}

Think about:
1. What do we know so far from observations?
2. What do we still need to find out?
3. Should we use a tool, or are we ready to provide a final answer?

Respond in this JSON format:
{{
    "reasoning": "Your thought process...",
    "ready_to_answer": true/false,
    "answer": "Final answer if ready",
    "next_action": {{
        "tool_name": "tool to call if not ready",
        "args": {{"arg1": "value1"}}
    }},
    "confidence": 0.0-1.0
}}"""

        # If we have a Claude client (from ClaudeSonnetIntelligenceService), use it
        if hasattr(self, 'client') and self.client:
            try:
                response = await self.client.messages.create(
                    model=getattr(self, 'model', 'claude-sonnet-4-5-20250929'),
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )

                import json
                content = response.content[0].text

                # Try to parse JSON from response
                try:
                    # Find JSON in response
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start >= 0 and end > start:
                        return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

                # Fallback: return as reasoning
                return {
                    "reasoning": content,
                    "ready_to_answer": iteration >= 2,  # After 2 iterations, try to answer
                    "answer": content if iteration >= 2 else None,
                    "confidence": 0.7
                }

            except Exception as e:
                logger.error(f"Error generating thought: {e}")

        # Fallback without LLM
        return {
            "reasoning": f"Iteration {iteration + 1}: Processing task",
            "ready_to_answer": iteration >= max(2, len(self._react_tools)),
            "answer": f"Based on observations: {observations}" if observations else None,
            "confidence": 0.5
        }

    async def _execute_tool(
        self,
        tool_name: str,
        args: dict[str, Any]
    ) -> Any:
        """Execute a registered tool with given arguments."""
        if tool_name not in self._react_tools:
            return {"error": f"Tool '{tool_name}' not found"}

        tool = self._react_tools[tool_name]

        try:
            # Check if async
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**args)
            else:
                result = tool(**args)

            return result

        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"error": str(e)}

    def get_reasoning_traces(self, limit: int = 10) -> list[ReasoningTrace]:
        """Get recent reasoning traces for debugging/analysis."""
        return self._react_traces[-limit:]

    def configure_dspy(
        self,
        lm: Any = None,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-5-20250929"
    ) -> bool:
        """
        Configure DSPy with language model.

        Args:
            lm: Pre-configured DSPy language model
            api_key: API key for auto-configuration
            model: Model name

        Returns:
            True if configuration successful
        """
        if not DSPY_AVAILABLE:
            logger.warning("DSPy not installed - cannot configure")
            return False

        try:
            if lm:
                dspy.configure(lm=lm)
            elif api_key:
                lm = dspy.LM(model=f"anthropic/{model}", api_key=api_key)
                dspy.configure(lm=lm)

            self._dspy_configured = True
            logger.info(f"DSPy configured with model: {model}")
            return True

        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            return False


class IterativeRetrievalMixin:
    """
    Mixin for iterative RAG retrieval loops.

    Implements multi-hop retrieval:
    1. Initial retrieval based on query
    2. Evaluate if results are sufficient
    3. If not, reformulate query and retrieve again
    4. Repeat until sufficient or max iterations

    Perfect for:
    - Complex multi-hop questions
    - Questions requiring synthesis from multiple sources
    - Exploratory information gathering
    """

    async def iterative_retrieve(
        self,
        query: str,
        retriever: Callable,
        max_iterations: int = 3,
        min_results: int = 3,
        sufficiency_threshold: float = 0.8
    ) -> dict[str, Any]:
        """
        Perform iterative retrieval until sufficient context gathered.

        Args:
            query: Initial search query
            retriever: Async function that takes query and returns results
            max_iterations: Maximum retrieval iterations
            min_results: Minimum results needed
            sufficiency_threshold: Confidence threshold for stopping

        Returns:
            Dict with combined results and retrieval trace
        """
        all_results = []
        queries_used = [query]
        current_query = query

        for iteration in range(max_iterations):
            # Retrieve
            results = await retriever(current_query)

            # Add new unique results
            for result in results:
                content = result.get("content", "")
                if not any(r.get("content") == content for r in all_results):
                    result["iteration"] = iteration
                    result["query"] = current_query
                    all_results.append(result)

            # Check sufficiency
            if len(all_results) >= min_results:
                avg_similarity = sum(r.get("similarity", 0) for r in all_results) / len(all_results)
                if avg_similarity >= sufficiency_threshold:
                    break

            # Reformulate query for next iteration
            if iteration < max_iterations - 1:
                current_query = await self._reformulate_query(
                    original_query=query,
                    current_results=all_results,
                    iteration=iteration
                )
                queries_used.append(current_query)

        return {
            "results": all_results,
            "total_results": len(all_results),
            "iterations": iteration + 1,
            "queries_used": queries_used,
            "avg_similarity": sum(r.get("similarity", 0) for r in all_results) / max(len(all_results), 1)
        }

    async def _reformulate_query(
        self,
        original_query: str,
        current_results: list[dict],
        iteration: int
    ) -> str:
        """
        Reformulate query based on current results.

        Strategies:
        - Add specificity based on gaps
        - Try synonyms or related terms
        - Break down into sub-questions
        """
        # Simple reformulation - in production use LLM
        reformulations = [
            f"{original_query} detailed",
            f"{original_query} explanation",
            f"how does {original_query} work",
            f"{original_query} examples",
        ]

        return reformulations[iteration % len(reformulations)]
